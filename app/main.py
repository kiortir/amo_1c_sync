
from app.models import Lead, WebHook
from app.tasks import dispatch, hook_logger

import os.path
import sys
from fastapi import FastAPI, Request
from querystring_parser import parser as qs_parser

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
    data = parsed_data.leads.fields
    dispatch.send(data.id, getattr(data, 'old_status_id'))
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
