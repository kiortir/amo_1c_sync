from typing import Awaitable, Callable
import aioamqp
from aioamqp.protocol import AmqpProtocol
from aioamqp.channel import Channel
from asyncio.transports import Transport
import socket
from settings import RabbitSettings
from entity import Task


async def error_callback(exception: Exception) -> None:
    print(exception)
    return None


async def connect() -> tuple[Transport, AmqpProtocol] | None:
    (
        transport,
        protocol,
    ) = await aioamqp.connect(
        host=RabbitSettings().rabbit_host,
        port=5672,
        login="rmuser",
        password="rmpassword",
        client_properties={
            "program_name": "test",
            "hostname": socket.gethostname(),
        },
    )
    return protocol, transport


class Manager:
    def __init__(self, protocol: AmqpProtocol, queue: str = "sync_tasks"):
        self.protocol = protocol
        self.channel: Channel | None = None
        self.queue = queue

    async def init_channel(self) -> Channel:
        self.channel = await self.protocol.channel()
        await self.channel.queue(self.queue, durable=True)
        # await self.channel.queue_declare()
        return self.channel

    async def get_channel(self) -> Channel:
        return self.channel or (await self.init_channel())

    async def push(self, message: Task) -> None:
        channel = await self.get_channel()
        await channel.publish(
            message.json(),
            "",
            self.queue,
            properties={
                "delivery_mode": 2,
            },
        )

    async def consume(self, callback: Callable[..., Awaitable[None]]) -> None:
        channel = await self.get_channel()
        await channel.basic_qos(connection_global=False, prefetch_count=5)
        await channel.basic_consume(callback, queue_name=self.queue)
