from typing import Union

from fastapi import FastAPI

from app.tasks import example

app = FastAPI()
# connection = Redis(host='172.20.128.2', port=6379, db=0)
# # connection = Redis(host='localhost', port=6379, db=0)
# queue = rq.Queue('fastapi_queue', connection=connection)

class Test:
    def __init__(self):
        self.q = "q"

@app.get("/")
def read_root():
    # job = queue.enqueue('app.main.example', {
    #     "test": "test"
    # })
    job = example.send("test")
    return {"job": job}


# @app.get("/jobs")
# def showJobs():
#     queue_info = queue.get_jobs()
#     return {"jobs": [job.id for job in queue_info]}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/hook")
def manage_webhook():
    # queue.add
    pass
