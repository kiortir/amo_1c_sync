from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

try:
    from app.v2 import Contact as _Contact, exceptions
    from app.v2 import Lead as _Lead
    from app.v2 import custom_field
    from app.v2.interaction import GenericInteraction
except ModuleNotFoundError:
    from v2 import Contact as _Contact, exceptions
    from v2 import Lead as _Lead
    from v2 import custom_field
    from v2.interaction import GenericInteraction


class NoteInteraction(GenericInteraction):
    def create(self, data):
        response, status = self.request(
            "post", self._get_path(), data=[data])
        if status == 400:
            raise exceptions.ValidationError(response)
        return response


class Lead(_Lead):
    sauna = custom_field.SelectCustomField("Баня")
    advance_payment = custom_field.NumericCustomField("Сумма задатка")
    booking_start_datetime = custom_field.DateTimeCustomField(
        "Дата и время заезда")
    booking_end_datetime = custom_field.DateTimeCustomField(
        "Дата и время выезда")
    bonus_card = custom_field.SelectCustomField("Бонусная карта")


class Contact(_Contact):
    phone = custom_field.TextCustomField("Телефон")


class CustomField(BaseModel):
    id: int
    name: str
    values: Any


class Field0(BaseModel):
    id: int
    name: str
    status_id: int
    old_status_id: Optional[int]
    price: str
    responsible_user_id: Optional[str]
    last_modified: int
    modified_user_id: Optional[int]
    created_user_id: Optional[int]
    date_create: int
    created_at: Optional[int]
    updated_at: Optional[int]

    pipeline_id: Optional[int]
    tags: Optional[dict]
    account_id: Optional[int]
    custom_fields: Optional[list[CustomField]]


class HookStatus(BaseModel):
    field_0: Field0 = Field(..., alias='0')


class Leads(BaseModel):
    update: list[Field0] = None
    add: list[Field0] = None

    delete: Optional[HookStatus] = None
    status: list[Field0] = None

    @property
    def fields(self):
        names = ['update', 'delete', 'status', 'add']

        for name in names:
            hook_status = getattr(self, name)
            if hook_status is not None:
                if name in {'update', 'add', 'status'}:
                    return hook_status[0]
                if name == 'status':
                    return hook_status.field_0


class _Links(BaseModel):
    self: str


class Account(BaseModel):
    subdomain: str
    id: str
    _links: _Links


class WebHook(BaseModel):
    leads: Leads


def dateTimeEncoder(date: datetime):
    date = date.replace(tzinfo=ZoneInfo('Etc/UTC'))
    aware = date.astimezone(ZoneInfo('Europe/Ulyanovsk'))

    return aware.strftime('%d.%m.%Y %H:%M:%S')


class BoundHook(BaseModel):
    id: int
    status: str
    room: Optional[str]
    start_booking_date: Optional[datetime]
    end_booking_date: Optional[datetime]
    summ_pay: Optional[int]
    bonus_card: Optional[str]
    name: Optional[str]
    phone: Optional[int]


class BoundHookMessage(BaseModel):
    pipe: int
    data: BoundHook

    @property
    def hash(self):
        return u''.join([str(value) for value in self.data.dict().values()])

    class Config:
        json_encoders = {
            datetime: dateTimeEncoder,
        }
