import httpx
from app.settings import ENDPOINT
import ujson


class InteractionManager:

    def __init__(self) -> None:
        self.client = httpx.Client()

    def post(self, data: dict):
        response = self.client.post(ENDPOINT, json=data, timeout=120000)
        if response.status_code != 200:
            raise Exception('1с не вернул ответ 200')
        return response

    def sync(self, jdata: str):
        data = ujson.loads(jdata)
        response = self.post(data)
        return response.content.decode("utf-8-sig")

    def get_reservation_status(self, lead_id: int):
        q = {
            'id': lead_id,
            'status': 'blank_status'
        }
        response = self.post(q)
        json = response.json()
        parsed_json = {key: value != 'none' for key, value in json.items()}
        return parsed_json


manager1C = InteractionManager()
