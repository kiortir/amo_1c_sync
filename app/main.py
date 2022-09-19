from typing import Union

from fastapi import FastAPI


try:
    from app.tasks import example 
    from app.models import WebHook, BoundHook, LeadStatus

except ModuleNotFoundError:
    from tasks import example
    from models import WebHook, BoundHook, LeadStatus


app = FastAPI()

class Test:
    def __init__(self):
        self.q = "q"

@app.get("/")
def read_root():
    job = example.send("test")
    return {"job": job}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/hook")
def manage_webhook(hook_payload: WebHook):
    hook_event, hook = hook_payload.target.event
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
    # print(new_hook.json())
    return new_hook


if __name__ == '__main__':
    from test_main import test_read_main
    test_read_main()
