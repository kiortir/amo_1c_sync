from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from sched import scheduler
from app.v2.entity import lead
import os
from http.client import HTTPException
from typing import Tuple, Union

import dramatiq
import httpx
import ujson
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage
from logzero import setup_logger
from app.v2.exceptions import NotFound, UnAuthorizedException


import app.settings as SETTINGS
from app.settings import DEBUG, ERROR_STATUS, StatusMatch, redis_client, ENDPOINT, send_request, STATUS_TO_DESCRIPTION_MAP
from app.models import BoundHook, BoundHookMessage, Contact, Lead, NoteInteraction
from app.v2 import Company, Pipeline
from app.tokens import storage

HOST = os.environ.get('BROKER_HOST', 'localhost')

rabbitmq_broker = RabbitmqBroker(host=HOST, port=5672, confirm_delivery=True)
rabbitmq_broker.add_middleware(CurrentMessage())
dramatiq.set_broker(rabbitmq_broker)

amo_logger = setup_logger(
    name='amo', logfile='amo_logs.json', maxBytes=1e6, backupCount=3)
hook_logger = setup_logger(name='hook')

SAUNA_NAME_MAP = {
    "Альпийская": "ЦБ000027",
    "Деревенская": "ЦБ000001",
    "Каменная": "ЦБ000016",
    "Русская": "ЦБ000005",
    "Скандинавская": "ЦБ000015",
    "Славянская": "ЦБ000017",
    "Турецкая": "ЦБ000003",
    "Финская": "ЦБ000006",
    "Японская": "ЦБ000007",
}


def get_sauna_field(sauna_name: str):
    if sauna_name is None:
        return None
    for type_, code in SAUNA_NAME_MAP.items():
        if sauna_name.startswith(type_):
            return code


@dramatiq.actor(max_retries=3)
def dispatch(lead_id: int, previous_status=None):
    try:
        data: Lead = Lead.objects.get(lead_id)
    except NotFound:
        return

    try:
        contact: Contact = next(data.contacts.__iter__())
        phone_str = ''.join([s for s in contact.phone if s.isdigit()])
        phone = int(phone_str) if phone_str else None
        name = contact.name
    except StopIteration:
        phone = name = None

    hook_logger.info(f'status:{data.status.id}, pipe: {data.pipeline.id}')

    status: Union[StatusMatch, None] = StatusMatch.get_status(
        previous_status, data.status.id)
    if status is None:
        return
    py_data = BoundHook(
        id=data.id,
        status=status.status_code,
        room=get_sauna_field(getattr(data.sauna, 'value', None)),
        start_booking_date=data.booking_start_datetime,
        end_booking_date=data.booking_end_datetime,
        summ_pay=data.advance_payment,
        bonus_card=getattr(data.bonus_card, 'value', None),
        name=name,
        phone=phone
    )
    new_data = BoundHookMessage(pipe=data.pipeline.id, data=py_data)
    hash_key = new_data.hash
    hash_lookup = str(data.id)
    cached_key = redis_client.get(hash_lookup)
    if cached_key is not None:
        cached_key = cached_key.decode('utf-8')
    if hash_key != cached_key:
        sendTo1c.send(new_data.json(), status.endpoint)
        redis_client.set(hash_lookup, hash_key, ex=86400)


@dramatiq.actor(max_retries=3)
def sendTo1c(data, endpoint):
    hook_logger.info(data)
    data = ujson.loads(data)
    message = CurrentMessage.get_current_message()
    retries = message.options.get('retries', 0)
    lead_id = data["data"]["id"]
    if retries == 3:
        setErrorStatus.send(lead_id, data["pipe"])
        raise HTTPException
    hook_logger.info(f'Отправляем информацию по лиду {data["data"]["id"]}')
    response = send_request(data["data"], endpoint or ENDPOINT)
    hook_logger.info(
        f'Код ответа = {response.status_code}, ответ = {response.text}')
    # if response.status_code != 200:
    #     raise HTTPException
    status = data["data"]["status"]
    response_status = response.content.decode("utf-8-sig")
    if response_status in {'error', 'booking_error'}:
        setErrorStatus.send(lead_id, data["pipe"])

    note_text = STATUS_TO_DESCRIPTION_MAP[status].get(
        response_status, f'получил непонятный ответ на запрос {status}')
    hook_logger.info(
        f'{status=}, response = ->{response_status}<-, {note_text=}, map = {STATUS_TO_DESCRIPTION_MAP[status]}, raw={response.content.decode("utf-8-sig")}')
    note_data = {
        "note_type": "service_message",
        "params": {
            "service": "1С коннектор",
            "text": note_text
        }
    }
    setNote.send(note_data, lead_id)


@dramatiq.actor(max_retries=2)
def setNote(data, lead_id):
    interaction = NoteInteraction(path=f'leads/{lead_id}/notes')
    interaction.create(data)
    hook_logger.info('Примечание оставлено')


@dramatiq.actor(max_retries=2)
def setErrorStatus(lead_id: int, pipeline_id: int):
    new_status = ERROR_STATUS.get(pipeline_id)
    hook_logger.info(f'Ошибка брони, {lead_id=}')
    if new_status is not None:
        Lead.objects.update(
            lead_id,
            {
                "status_id": new_status
            }),


def init_tokens(skip_error=False):
    try:
        info = list(Company.objects.all())
        refresh_tokens.send()
    except (UnAuthorizedException, TypeError):
        data = {
            "grant_type": "authorization_code",
            "code": SETTINGS.AUTH_CODE,
            "redirect_uri": SETTINGS.REDIRECT_URI,
            "client_id": SETTINGS.INTEGRATION_ID,
            "client_secret": SETTINGS.SECRET_KEY,
        }
        try:
            response = httpx.post(
                "https://{}.amocrm.ru/oauth2/access_token".format(SETTINGS.SUBDOMAIN), json=data)
        except httpx.exceptions.RequestException:
            ...
        else:
            if response.status_code != 200 and not skip_error:
                raise Exception(response.json()["hint"])
            if response.status_code != 200 and skip_error:
                return
            response = response.json()
            storage.save_tokens(
                response["access_token"], response["refresh_token"])
            # refresh_tokens.send_with_options(delay=7200000)


def fetch_statuses():
    pipelines = Pipeline.objects.all()
    for pipeline in pipelines:
        statuses = pipeline.statuses
        for status in statuses:
            if status.name == 'Ошибка брони':
                ERROR_STATUS[pipeline.id] = status.id
                continue

            status_categories = SETTINGS.NAME_TO_STATUS.get(status.name)
            if status_categories is not None:
                for status_class_function in status_categories:
                    status_class_function(status.id)


def _get_new_tokens() -> Tuple[str, str]:
    refresh_token = storage.get_refresh_token()
    if not refresh_token:
        raise ValueError()
    body = {
        "client_id": SETTINGS.INTEGRATION_ID,
        "client_secret": SETTINGS.SECRET_KEY,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": SETTINGS.REDIRECT_URI,
    }
    response = httpx.post(
        "https://{}.amocrm.ru/oauth2/access_token".format(SETTINGS.SUBDOMAIN), json=body)
    if response.status_code == 200:
        data = response.json()
        return data["access_token"], data["refresh_token"]
    raise EnvironmentError(
        "Can't refresh token {}".format(response.json()))


@dramatiq.actor
def refresh_tokens():
    hook_logger.info('Обновляем токены')
    token, refresh_token = _get_new_tokens()
    storage.save_tokens(token, refresh_token)
    # refresh_tokens.send_with_options(delay=43200000)


if SETTINGS.IS_ROOT:
    init_tokens()

    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_tokens.send,
                      IntervalTrigger(hours=3))
    scheduler.start()
else:
    fetch_statuses()
