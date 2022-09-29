import asyncio
from datetime import datetime
from pickletools import int4
from logzero import setup_logger
from http.client import HTTPException
import os

import dramatiq
import httpx
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage
from amocrm.v2 import Company, custom_field
from app.models import Lead, Contact

from app import amo_handler

from app.amo_handler import redis_client


try:
    from app.models import BoundHook
except ImportError:
    from models import BoundHook


HOST = os.environ.get('BROKER_HOST', 'localhost')

rabbitmq_broker = RabbitmqBroker(host=HOST, port=5672, confirm_delivery=True)
rabbitmq_broker.add_middleware(CurrentMessage())
dramatiq.set_broker(rabbitmq_broker)

amo_logger = setup_logger(
    name='amo', logfile='amo_logs.json', maxBytes=1e6, backupCount=3)
hook_logger = setup_logger(name='hook')


@dramatiq.actor
def dispatch(lead_id: int):
    data: Lead = Lead.objects.get(lead_id)

    contact: Contact = next(data.contacts.__iter__())
    sauna: custom_field.SelectValue = data.sauna
    hook_logger.info(f'status:{data.status.id}, pipe: {data.pipeline.id}')
    new_data = {
        "pipe": data.pipeline.id,
        "data": {
            "id": data.id,
            "status": data.status.id,
            "room": sauna.value,
            "start_booking_date": data.booking_start_datetime.timestamp(),
            "end_booking_date": data.booking_end_datetime.timestamp(),
            "summ_pay": data.advance_payment,
            "bonus_card": data.bonus_card.value == 'да',
            "name": contact.name,
            "phone": contact.phone
        }}
    key = u''.join([str(value) for value in new_data["data"].values()])
    cached_key = (redis_client.get(str(data.id)) or b'').decode('utf-8')
    if key != cached_key:
        sendTo1c.send(new_data)
        redis_client.set(str(data.id), key, ex=900)
        hook_logger.info(f'Sent:{new_data}')
        return
    hook_logger.info(f'Same key fo :{data.id}')


@dramatiq.actor(max_retries=0)
def sendTo1c(data):
    # hook_logger.info(data)

    message = CurrentMessage.get_current_message()
    retries = message.options.get('retries', 0)
    if retries == 0:
        setErrorStatus.send(data["data"]["id"], data["pipe"])
        raise HTTPException

    response = httpx.post('http://localhost:8888/endpoint', data=data)
    if response.status_code != 200:
        raise HTTPException


@dramatiq.actor(max_retries=2)
def setErrorStatus(lead_id: int, pipeline_id: int):
    error_status = {
        5699695: 50366596,
        5711290: 50367064
    }
    new_status = error_status.get(pipeline_id)
    hook_logger.info(new_status)
    hook_logger.info(f'Ошибка брони, {lead_id=}')
    if new_status is not None:
        Lead.objects.update(
            lead_id,
            {
                "status_id": new_status
            })
