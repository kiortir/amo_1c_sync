import logzero
import ujson
import json
from logzero import setup_logger
from logging.config import fileConfig
from http.client import HTTPException
import os

import dramatiq
import httpx
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage

from app.models import BoundHook, WebHook


HOST = os.environ.get('BROKER_HOST', 'localhost')

print(HOST)

rabbitmq_broker = RabbitmqBroker(host=HOST, port=5672, confirm_delivery=True)
rabbitmq_broker.add_middleware(CurrentMessage())
dramatiq.set_broker(rabbitmq_broker)

amo_logger = setup_logger(name='amo', logfile='amo_logs.json', maxBytes=1e6, backupCount=3)
hook_logger = setup_logger(
    name='hook', logfile='amo_hooks_data.json', maxBytes=1e6, backupCount=3, json=True, json_ensure_ascii=False)


# logzero.logfile("amo_logs.json", maxBytes=1e6, backupCount=3)
# logzero.json()


@dramatiq.actor
def example(arg):
    print(arg)


@dramatiq.actor(max_retries=1)
def dispatch(data: BoundHook):
    # data.json()
    # j_data = ujson.dumps(data, ensure_ascii=False)
    hook_logger.info(data)

    # message = CurrentMessage.get_current_message()
    # retries = message.options.get('retries', 0)
    # if retries == 0:
    #     setLeadError.send(data)
    #     raise Exception
    # raise Exception
    # response = httpx.post('https://test', data=data)
    # if (response := response.json().get('status')) != 200:
    #     raise HTTPException


@dramatiq.actor
def setLeadError(lead_id: int):
    amo_logger.warning(f'Error in hook, {lead_id=}')


def send_to_1c(message):
    pass
