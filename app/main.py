from typing import Union

from fastapi import FastAPI, Request
from querystring_parser import parser as qs_parser

import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# try:
from app.tasks import dispatch, hook_logger
from app.models import WebHook, BoundHook, LeadStatus

# except ModuleNotFoundError:
#     from tasks import example
#     from models import WebHook, BoundHook, LeadStatus


app = FastAPI()

class Test:
    def __init__(self):
        self.q = "q"

@app.get("/")
def read_root(imitation_hook: WebHook):
    job = dispatch.send(imitation_hook)
    return {"job": job}

@app.post("/hook")
async def manage_webhook(hook_payload: Request):
    query = await hook_payload.body()
    hook_logger.info(query)
    data = qs_parser.parse(query, normalized=True)
    hook_logger.info(data)

    parsed_data = WebHook.parse_obj(data)
    hook_event, hook = parsed_data.leads.fields
    new_hook = BoundHook(
        id=hook.id,
        status=LeadStatus.create_booking,
        room='test',
        start_booking_date=3,
        end_booking_date=3,
        summ_pay=600,
        has_bonuscard=True,
        name='michael',
        phone='9953008454'
    )
    dispatch.send(new_hook.dict())
    return {'status': 'ok'}


if __name__ == '__main__':
    from test_main import test_read_main
    test_read_main()
