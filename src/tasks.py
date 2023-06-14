import time
from typing import Any

import ujson
from amocrm_api_client.models import AddNote, Contact, Lead, UpdateLead
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from _1c import manager1C
from amo import amo_client
from entity import BoundHook
from redis_client import redis_client
from logs import _1clogger, amologger, applogger
from settings import ERROR_STATUS, STATUS_TO_DESCRIPTION_MAP, sauna_names
from statuses import match_status


def get_phone_number(contact: Contact) -> int | None:
    custom_values = contact.custom_fields_values
    if not custom_values:
        return None
    for value in custom_values:
        if value.field_id == 408175:
            phone_values = value.values
            if not phone_values:
                return None
            phone_string = phone_values[0].value
            phone_str = "".join((s for s in phone_string if s.isdigit()))
            phone = int(phone_str) if phone_str else None
            return phone
    return None


CUSTOM_FIELDS = {
    480671: "start_booking_date",
    480679: "end_booking_date",
    480957: "summ_pay",
    490537: "bonus_card",
}


def get_extra_field_value(field: dict[str, Any]) -> Any:
    values = field.get("values")
    if not values:
        return None
    value = values[0]["value"]
    return value


@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
async def dispatch(lead_id: int) -> Lead | None:
    lead = await amo_client.leads.get_by_id(lead_id, _with=("contacts",))
    amologger.info(f"Получены данные по лиду {lead_id}")
    _1c_status = await manager1C.get_reservation_status(lead_id)
    _1clogger.info(f"Получены данные по лиду {lead_id} из 1с")

    if not lead.status_id or not _1c_status:
        return None
    status = match_status(lead.status_id, _1c_status)
    if not status:
        return None

    contact_id = (
        contacts[0].id if (contacts := lead.embedded.contacts) else None
    )
    contact = (
        (await amo_client.contacts.get_by_id(contact_id))
        if contact_id
        else None
    )

    phone_number = get_phone_number(contact) if contact else None
    name = contact.name if contact else None

    additional_data = {}
    sauna_code = None
    if lead.custom_fields_values is not None:
        for field in lead.custom_fields_values:
            fid = field.get("field_id")
            if fid == 480665:
                sauna = get_extra_field_value(field)
                sauna_code = sauna_names.match(sauna)
            f = CUSTOM_FIELDS.get(fid, None)
            if f:
                value = get_extra_field_value(field)
                additional_data[f] = value

    data = BoundHook(
        id=lead_id,
        status=status or "test",
        room=sauna_code,
        name=name,
        phone=phone_number,
        **additional_data,
    )

    generated_hash = data.make_hash()
    stored_hash = await redis_client.get(str(lead_id))
    applogger.info(
        " --> ".join([str(e) for e in (stored_hash, generated_hash)])
    )
    if generated_hash and (generated_hash == int(stored_hash)):
        applogger.info(f"Информация по лиду {lead_id} уже актуальна")
        return None
    await redis_client.set(str(lead_id), generated_hash, ex=100)
    try:
        now = time.monotonic()
        response_status = await send_data_to_1c(data)

        await _1clogger.info(
            f"ID лида: {lead_id}, ответ 1с: {response_status}, время до ответа: {time.monotonic() - now} с."  # noqa: E501
        )
        if response_status in {"error", "booking_error"}:
            await set_error_status(lead)
        message = STATUS_TO_DESCRIPTION_MAP[data.status].get(
            response_status,
            f"получил непонятный ответ на запрос {data.status}",
        )
        await set_note(lead, message)

    except RetryError as e:
        # await set_error_status(lead)
        await _1clogger.error(
            f"Исчерпаны попытки на отправку информации по лиду {lead_id}"
        )
        raise e
    except Exception as e:
        print(e)

    return lead


# @retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
async def send_data_to_1c(data: BoundHook) -> str:
    amologger.info(f"Отправляем информацию по лиду {data.id}")
    response = await manager1C.sync(ujson.loads(data.json()))
    return response


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def set_error_status(lead: Lead) -> None:
    if lead.pipeline_id:
        new_status = ERROR_STATUS.get(lead.pipeline_id)
        if new_status:
            update_lead = UpdateLead(
                id=lead.id, status_id=new_status, _embedded=None
            )
            await amo_client.leads.update(update_lead)


async def set_error_status_by_id(lead_id: int) -> None:
    lead = await amo_client.leads.get_by_id(lead_id)
    if lead.pipeline_id:
        new_status = ERROR_STATUS.get(lead.pipeline_id)
        if new_status:
            update_lead = UpdateLead(
                id=lead.id, status_id=new_status, _embedded=None
            )
            await amo_client.leads.update(update_lead)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def set_note(lead: Lead, message: str) -> None:
    note = AddNote(
        entity_id=lead.id,
        note_type="common",
        params={"text": message},  # noqa: E501 # type: ignore
    )
    await amo_client.leads.add_notes([note])
