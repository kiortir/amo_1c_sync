import httpx
from app.settings import ENDPOINT
from app.tasks import hook_logger

class InteractionManager:

    def __init__(self) -> None:
        self.client = httpx.Client()

    def post(self, data: dict):
        response = self.client.post(ENDPOINT, json=data, timeout=120000)
        hook_logger.info(response.text)
        if response.status_code != 200:
            raise Exception('1с не вернул ответ 200')
        return response

    def sync(self, data: dict):
        response = self.post(data)
        return response.content.decode("utf-8-sig")

    def get_reservation_status(self, lead_id: int):
        q = {
            'id': lead_id,
            'status': 'blank_status'
        }
        response = self.post(q)
        json = response.json()
        print(json)
        # parsed_json = {key: value != 'none' for key, value in json.items()}
        if json.get('stay') != 'none':
            return 'stay'
        if json.get('booking') != 'none':
            return 'booking'
        return None

manager1C = InteractionManager()


if __name__ == '__main__':
    import time
    start = time.perf_counter()
    manager1C.get_reservation_status(10650669)
    end = time.perf_counter()
    print(end-start)