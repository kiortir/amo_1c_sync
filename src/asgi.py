import asyncio

import aioamqp
from fastapi import (
    APIRouter,
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Response,
)

from entity import Task, WebHook
from logs import _1clogger, amologger, applogger
from qsdecoder import QSEncodedRoute
from rabbit import Manager, connect
from settings import amo_settings
from tasks import dispatch

app = FastAPI(root_path="/connector")
router = APIRouter(route_class=QSEncodedRoute)
manager = None
protocol = None
transport = None


@router.post("/hook")
async def manage_webhook(
    hook: WebHook, background_tasks: BackgroundTasks
) -> dict[str, str]:
    id: int | None = getattr(hook.leads.fields, "id", None)
    if id:
        await amologger.info(msg=f"Обрабатываем информацию по лиду {id}")
        background_tasks.add_task(dispatch, id)
    else:
        await amologger.error(msg="Не смогли извлечь id из вебхука")
    return {"status": "ok"}


@app.get("/lead")
async def get_lead(
    lead_id: int,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    await amologger.info(msg=f"Обрабатываем информацию по лиду {lead_id}")
    if lead_id:
        background_tasks.add_task(dispatch, id)
    return {"status": "ok"}


@app.post("/token")
async def set_auth_token(
    auth_code: str,
) -> dict[str, str]:
    await amologger.info(msg="Устанавливаем токен")
    amo_settings.auth_code = auth_code
    return {"status": "ok"}


@app.get("/test")
async def test_amqp() -> None:
    if manager:
        await manager.push(Task(fn="dispatch", args=17795931))
        return Response(status_code=201)
    else:
        raise HTTPException(500)


# @app.on_event("startup")
# async def init_amo() -> None:
#     await amo_client.initialize()
#     # try:
#     await fetch_statuses()
#     # except RefreshTokenExpiredException:
#     #     await amologger.critical("refresh токен устарел или не существует")

#     await applogger.info("Коннектор запущен")


@app.on_event("startup")
async def init_rabbit() -> None:
    global manager
    protocol = None
    while not protocol:
        try:
            protocol, _ = await connect()
        except aioamqp.AioamqpException:
            applogger.error("Соединение с RabbitMQ не удается установить")
            await asyncio.sleep(3)
    manager = Manager(protocol)


@app.on_event("shutdown")
async def deinit() -> None:
    # await amo_client.deinitialize()
    if protocol:
        await protocol.close()
    if transport:
        transport.close()
    await amologger.shutdown()
    await applogger.shutdown()
    await _1clogger.shutdown()
