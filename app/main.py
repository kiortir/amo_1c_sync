
import os.path
import sys

from fastapi import FastAPI, Request
from querystring_parser import parser as qs_parser

try:
    from app.models import Lead, WebHook
    from app.tasks import dispatch, hook_logger
except ModuleNotFoundError:
    from models import Lead, WebHook
    from tasks import dispatch, hook_logger

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


app = FastAPI()


@app.get("/")
def read_root(request: Request):
    return {"status": 'working'}


@app.post("/hook")
async def manage_webhook(hook_payload: Request):
    query = await hook_payload.body()
    data = qs_parser.parse(query, normalized=True)
    hook_logger.info(data)
    parsed_data = WebHook.parse_obj(data)
    data = parsed_data.leads.fields
    dispatch.send(data.id)
    return {'status': 'ok'}




@app.get("/test")
async def read_root(request: Request):
    test_id = 7932425
    note_data = {
        "note_type": "service_message",
        "params": {
            "service": "1С коннектор dev",
            "text": 'test1'
        }
    }
    # interaction = NoteInteraction(path='leads/7932425/notes')
    # data = interaction.create(note_data)
    # data = Lead.objects.get(7932425)
    return {"status": 'ok'}


@ app.get("/data")
async def read_root(request: Request):
    test_id = 7932425
    data: Lead = Lead.objects.get(test_id)
    return data
