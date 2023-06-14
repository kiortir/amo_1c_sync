import asyncio
from typing import Any, Awaitable

import aioamqp
import ujson
from aioamqp.envelope import Envelope
from aioamqp.properties import Properties
from tenacity import RetryError

from amo import amo_client
from entity import Task
from logs import applogger, amologger, _1clogger
from rabbit import Channel, Manager, connect
from settings import ERROR_STATUS
from statuses import Status
from tasks import dispatch, set_error_status_by_id

TASKS = {"dispatch": dispatch, "set_error_status": set_error_status_by_id}


async def fetch_statuses() -> None:
    pipelines = await amo_client.pipelines.get_all()
    for pipeline in pipelines:
        statuses = pipeline.embedded.statuses
        for status in statuses:
            if status.name == "Ошибка брони":
                ERROR_STATUS[pipeline.id] = status.id
                continue
            Status(status.id, status.name, pipeline.id)


async def init_amo() -> None:
    await amo_client.initialize()
    await fetch_statuses()
    # await applogger.info("Коннектор запущен")


async def apply(
    coroutine: Awaitable[Any],
    channel: Channel,
    message: bytes,
    envelope: Envelope,
    properties: Properties,
) -> None:
    try:
        await coroutine  # fn(task.args)
    except RetryError:
        await channel.publish(
            Task(
                fn="set_error_status", args=ujson.loads(message)["args"]
            ).json(),
            "",
            envelope.routing_key,
        )
    except Exception as e:
        print(e)
    finally:
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)


async def work(
    channel: Channel,
    message: bytes,
    envelope: Envelope,
    properties: Properties,
) -> None:
    task = Task.parse_obj(ujson.loads(message))
    fn = TASKS.get(task.fn)
    if not fn:
        applogger.error(
            f"Получили сообщение о выполнении задачи {task.fn}, но она не зарегистрирована"  # noqa: E501
        )
    else:
        loop = asyncio.get_running_loop()
        loop.create_task(
            apply(fn(task.args), channel, message, envelope, properties)
        )


protocol = None
transport = None


async def start() -> None:
    await init_amo()
    global protocol
    while not protocol:
        try:
            protocol, _ = await connect()
        except aioamqp.AioamqpException:
            applogger.error("Соединение с RabbitMQ не удается установить")
            await asyncio.sleep(3)
    applogger.info("Исполнитель запущен")


async def main() -> None:
    await start()
    manager = Manager(protocol)
    print(manager)
    await manager.consume(work)


async def shutdown() -> None:
    applogger.info("Shutting down")
    global protocol
    global transport
    if protocol:
        await protocol.close()
    if transport:
        transport.close()
    amo_client.deinitialize()
    await amologger.shutdown()
    await applogger.shutdown()
    await _1clogger.shutdown()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    except Exception as e:
        print(e)
    finally:
        loop.run_until_complete(shutdown())
        loop.close()
