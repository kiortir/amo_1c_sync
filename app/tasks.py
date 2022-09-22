import asyncio
from http.client import HTTPException

import dramatiq
import httpx
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage

from app.models import BoundHook, WebHook

rabbitmq_broker = RabbitmqBroker(url="amqp://guest:guest@localhost:5672/")
rabbitmq_broker.add_middleware(CurrentMessage())
dramatiq.set_broker(rabbitmq_broker)


@dramatiq.actor
def example(arg):
    print(arg)


@dramatiq.actor(max_retries=3)
def dispatch(data: BoundHook):
    message = CurrentMessage.get_current_message()
    retries = message.options.get('retries', 0)
    if retries == 3:
        setLeadError.send(data.id)
        raise Exception

    response = httpx.post('https://test', data=data)
    if (response := response.json().get('status')) != 200:
        raise HTTPException


@dramatiq.actor
def setLeadError(lead_id: int):
    pass


def send_to_1c(message):
    pass
