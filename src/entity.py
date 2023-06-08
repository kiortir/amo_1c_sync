from zoneinfo import ZoneInfo
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    fn: str
    args: str


class CustomField(BaseModel):
    id: int
    name: str
    values: Any


class Field0(BaseModel):
    id: int
    # name: str
    # status_id: int
    # old_status_id: Optional[int]
    # price: str
    # responsible_user_id: Optional[str]
    # last_modified: int
    # modified_user_id: Optional[int]
    # created_user_id: Optional[int]
    # date_create: int
    # created_at: Optional[int]
    # updated_at: Optional[int]

    # pipeline_id: Optional[int]
    # tags: Optional[dict]
    # account_id: Optional[int]
    # custom_fields: Optional[list[CustomField]]


class HookStatus(BaseModel):
    field_0: Field0 = Field(..., alias="0")


class Leads(BaseModel):
    update: list[Field0] | None = None
    add: list[Field0] | None = None

    delete: Optional[HookStatus] = None
    status: list[Field0] | None = None

    @property
    def fields(self) -> Field0 | None:
        names = {"update", "delete", "status", "add"}

        for name in names:
            hook_status: list[Field0] = getattr(self, name)
            if hook_status is not None:
                if name in {"update", "add", "status"}:
                    return hook_status[0]
        return None


class _Links(BaseModel):
    self: str


class Account(BaseModel):
    subdomain: str
    id: str
    _links: _Links


class WebHook(BaseModel):
    leads: Leads


def dateTimeEncoder(date: datetime) -> str:
    date = date.replace(tzinfo=ZoneInfo("Etc/UTC"))
    aware = date.astimezone(ZoneInfo("Europe/Ulyanovsk"))

    return aware.strftime("%d.%m.%Y %H:%M:%S")


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

    def hash(self) -> str:
        return "".join([str(value) for value in self.dict().values()])

    class Config:
        json_encoders = {
            datetime: dateTimeEncoder,
        }


class BoundHookMessage(BaseModel):
    pipe: int
    data: BoundHook

    @property
    def hash(self) -> str:
        return "".join([str(value) for value in self.data.dict().values()])

    class Config:
        json_encoders = {
            datetime: dateTimeEncoder,
        }
