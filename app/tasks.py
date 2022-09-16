import asyncio
import dramatiq
import requests

from dramatiq.brokers.rabbitmq import RabbitmqBroker


rabbitmq_broker = RabbitmqBroker(url="amqp://guest:guest@rabbitmq:5672/")
dramatiq.set_broker(rabbitmq_broker)

@dramatiq.actor
def example(arg):
    print(arg)


def send_to_1c(message):
    pass

