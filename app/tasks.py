from datetime import datetime
from logzero import setup_logger
from http.client import HTTPException
import os
import ujson

import dramatiq
import httpx
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage
from amocrm.v2 import Company, custom_field
try:
    from app.models import Lead, Contact
    from app import amo_handler
    from app.amo_handler import DEBUG, redis_client, STATUS_MAP, ERROR_STATUS

except ModuleNotFoundError:
    from models import Lead, Contact
    import amo_handler
    from amo_handler import DEBUG, redis_client, STATUS_MAP, ERROR_STATUS




try:
    from app.models import BoundHook, BoundHookMessage
except ImportError:
    from models import BoundHook, BoundHookMessage


HOST = os.environ.get('BROKER_HOST', 'localhost')

rabbitmq_broker = RabbitmqBroker(host=HOST, port=5672, confirm_delivery=True)
rabbitmq_broker.add_middleware(CurrentMessage())
dramatiq.set_broker(rabbitmq_broker)

amo_logger = setup_logger(
    name='amo', logfile='amo_logs.json', maxBytes=1e6, backupCount=3)
hook_logger = setup_logger(name='hook')


def get_status(status_id: int):
    for status_name, status_ids in STATUS_MAP.items():
        if status_id in status_ids:
            return status_name


@dramatiq.actor
def dispatch(lead_id: int):
    data: Lead = Lead.objects.get(lead_id)

    contact: Contact = next(data.contacts.__iter__())

    hook_logger.info(f'status:{data.status.id}, pipe: {data.pipeline.id}')
    status = get_status(data.status.id)
    if status is None:
        return
    py_data = BoundHook(
        id=data.id,
        status=status,
        room=data.sauna.value,
        start_booking_date=data.booking_start_datetime,
        end_booking_date=data.booking_end_datetime,
        summ_pay=data.advance_payment,
        bonus_card=data.bonus_card.value,
        name=contact.name,
        phone=contact.phone
    )
    new_data = BoundHookMessage(pipe=data.pipeline.id, data=py_data)
    hash_key = new_data.hash
    hash_lookup = str(data.id)
    cached_key = redis_client.get(hash_lookup)
    if cached_key is not None:
        cached_key = cached_key.decode('utf-8')

    if hash_key != cached_key or DEBUG:
        sendTo1c.send(new_data.json())
        redis_client.set(hash_lookup, hash_key, ex=900)


@dramatiq.actor(max_retries=3)
def sendTo1c(data):
    data = ujson.loads(data)
    hook_logger.info(data)
    message = CurrentMessage.get_current_message()
    retries = message.options.get('retries', 0)
    if retries == 3:
        setErrorStatus.send(data["data"]["id"], data["pipe"])
        raise HTTPException

    response = httpx.post('http://localhost:8888/endpoint', json=data)
    if response.status_code != 200:
        raise HTTPException


@dramatiq.actor(max_retries=2)
def setErrorStatus(lead_id: int, pipeline_id: int):
    new_status = ERROR_STATUS.get(pipeline_id)
    hook_logger.info(new_status)
    hook_logger.info(f'Ошибка брони, {lead_id=}')
    if new_status is not None:
        Lead.objects.update(
            lead_id,
            {
                "status_id": new_status
            })
