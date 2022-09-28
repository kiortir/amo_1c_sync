from logzero import setup_logger
from http.client import HTTPException
import os

import dramatiq
import httpx
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage

try:
    from app.models import BoundHook, WebHook
except ImportError:
    from models import BoundHook, WebHook


HOST = os.environ.get('BROKER_HOST', 'localhost')

rabbitmq_broker = RabbitmqBroker(host=HOST, port=5672, confirm_delivery=True)
rabbitmq_broker.add_middleware(CurrentMessage())
dramatiq.set_broker(rabbitmq_broker)

amo_logger = setup_logger(
    name='amo', logfile='amo_logs.json', maxBytes=1e6, backupCount=3)
hook_logger = setup_logger(name='hook')


@dramatiq.actor(max_retries=3)
def dispatch(data: BoundHook.dict):
    hook_logger.info(data)

    message = CurrentMessage.get_current_message()
    retries = message.options.get('retries', 0)
    if retries == 3:
        setLeadError.send(data)
        raise HTTPException

    response = httpx.post('https://google.com', data=data)
    # if (response := response.json().get('status')) != 200:
    #     raise HTTPException


@dramatiq.actor
def setLeadError(lead_id: int):
    amo_logger.warning(f'Error in hook, {lead_id=}')


def send_to_1c(message):
    pass
