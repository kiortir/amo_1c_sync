from __future__ import annotations
from enum import Enum

from typing import Optional

from pydantic import BaseModel, Field


class CustomField(BaseModel):
    id:int
    name: str
    values: list[str]

class Field0(BaseModel):
    id: int
    name: str
    status_id: int
    old_status_id: int
    price: str
    responsible_user_id: str
    last_modified: int
    modified_user_id: int
    created_user_id: int
    date_create: int
    created_at: Optional[int]
    updated_at: Optional[int]

    pipeline_id: Optional[int]
    tags: Optional[dict]
    account_id: int
    custom_fields: list[CustomField]


class HookStatus(BaseModel):
    field_0: Field0 = Field(..., alias='0')


class Leads(BaseModel):
    update: Optional[HookStatus] = None
    delete: Optional[HookStatus] = None
    status: Optional[HookStatus] = None


class _Links(BaseModel):
    self: str


class Account(BaseModel):
    subdomain: str
    id: str
    _links: _Links


class WebHook(BaseModel):
    leads: Leads


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
