import os
from http.client import HTTPException

import dramatiq
import httpx
import ujson
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage
from logzero import setup_logger
from amocrm.v2.exceptions import NotFound

from app.amo_handler import DEBUG, ERROR_STATUS, StatusMatch, redis_client, ENDPOINT, send_request
from app.models import BoundHook, BoundHookMessage, Contact, Lead

HOST = os.environ.get('BROKER_HOST', 'localhost')

rabbitmq_broker = RabbitmqBroker(host=HOST, port=5672, confirm_delivery=True)
rabbitmq_broker.add_middleware(CurrentMessage())
dramatiq.set_broker(rabbitmq_broker)

amo_logger = setup_logger(
    name='amo', logfile='amo_logs.json', maxBytes=1e6, backupCount=3)
hook_logger = setup_logger(name='hook')


# def get_status(previous_status_id: int, status_id: int):
#     match_list = [(status.match(previous_status_id, status_id),
#                    status.status_code) for status in StatusMatch.statuses]
#     max_match, match_status = max(match_list, default=(None, None), key=lambda x: x[0])
#     return match_status if max_match else None


@dramatiq.actor
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

    status = StatusMatch.get_status(previous_status, data.status.id)
    if status is None:
        return
    py_data = BoundHook(
        id=data.id,
        status=status,
        room=getattr(data.sauna, 'value', None),
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
        sendTo1c.send(new_data.json())
        redis_client.set(hash_lookup, hash_key, ex=86400)


# ENDPOINT = 'https://webhook.site/f1dedd2e-7667-44a4-9815-3a140d2f8cee'


@dramatiq.actor(max_retries=3)
def sendTo1c(data):
    hook_logger.info(data)
    data = ujson.loads(data)
    message = CurrentMessage.get_current_message()
    retries = message.options.get('retries', 0)
    if retries == 3:
        setErrorStatus.send(data["data"]["id"], data["pipe"])
        raise HTTPException
    hook_logger.info(f'Отправляем информацию по лиду {data["data"]["id"]}')
    response = send_request(data["data"])
    try:
        hook_logger.info(response.json())
    except Exception:
        pass
    if response.status_code != 200:
        raise HTTPException


@dramatiq.actor(max_retries=2)
def setErrorStatus(lead_id: int, pipeline_id: int):
    new_status = ERROR_STATUS.get(pipeline_id)
    hook_logger.info(f'Ошибка брони, {lead_id=}')
    if new_status is not None:
        Lead.objects.update(
            lead_id,
            {
                "status_id": new_status
            })
