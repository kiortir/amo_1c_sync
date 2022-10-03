from amocrm_api_client.models.lead import UpdateLead
from datetime import datetime
from app.tasks import dispatch, hook_logger
from app.models import BoundHook, Leads, WebHook, Lead
from amocrm.v2 import Contact, Company, Pipeline, Status
import os.path
import sys
from typing import Union

from fastapi import FastAPI, Request
from querystring_parser import parser as qs_parser

from app import amo_handler

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


app = FastAPI()


@app.get("/")
def read_root(request: Request):
    return {"status": 'working'}


@app.post("/hook")
async def manage_webhook(hook_payload: Request):
    query = await hook_payload.body()
    data = qs_parser.parse(query, normalized=True)

    parsed_data = WebHook.parse_obj(data)
    hook_event, hook = parsed_data.leads.fields
    new_hook = BoundHook(
        id=hook.id,
        status='create_booking',
        room='test',
        start_booking_date=3,
        end_booking_date=3,
        summ_pay=600,
        has_bonuscard=True,
        name='michael',
        phone='9953008454'
    )
    dispatch.send(data.id)
    return {'status': 'ok'}


@app.get("/test")
async def read_root(request: Request):
    test_id = 6681281
    data = dispatch.send(test_id)
    return {"status": data}


@app.get("/data")
async def read_root(request: Request):
    test_id = 6681281
    data: Lead = Lead.objects.get(test_id)
    return data


@app.get("/status")
async def read_root(request: Request):
    test_id = 6681281
    data = Pipeline.objects.all()
    for pipeline in data:
        print(pipeline.statuses)
    return {"status": data}
