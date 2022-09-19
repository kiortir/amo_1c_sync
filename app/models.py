from __future__ import annotations
from enum import Enum
from typing import List, Dict

from typing import List

from pydantic import BaseModel, Field

# from amocrm_api_client.models.lead import Lead


class CustomField(BaseModel):
    id: str
    name: str
    values: List[str]


class DataField(BaseModel):
    id: int
    name: str
    old_status_id: int
    status_id: int
    price: str
    responsible_user_id: int
    last_modified: int
    modified_user_id: int
    created_user_id: int
    date_create: int
    account_id: int
    custom_fields: List[CustomField]


class HookEvent(BaseModel):
    field: DataField = Field(..., alias='0')


class HookTarget(BaseModel):
    __root__: Dict[str, HookEvent]

    @property
    def event(self):
        return (key := list(self.__root__.keys())[0]),  self.__root__[key].field


class WebHook(BaseModel):
    __root__: Dict[str, HookTarget]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        print(self.__root__)
        return list(self.__root__.values())[item]

    @property
    def target(self):
        return list(self.__root__.values())[0]


class LeadStatus(str, Enum):
    create_booking = 'create_booking'
    delete_booking = 'delete_booking'
    create_stay = 'create_stay'
    delete_stay = 'delete_stay'


class BoundHook(BaseModel):
    id: int
    status: LeadStatus
    room: str
    start_booking_date: int
    end_booking_date: int
    summ_pay: int
    has_bonuscard: bool
    name: str
    phone: str
