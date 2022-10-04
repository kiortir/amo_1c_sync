import asyncio
from collections import defaultdict
import os
from typing import Union
from amocrm.v2 import tokens, Pipeline
import redis


DEBUG = os.environ.get('DEBUG', 'TRUE') == 'TRUE'

if DEBUG:
    from dotenv import load_dotenv
    load_dotenv()

ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
INTEGRATION_ID = os.environ.get('INTEGRATION_ID')

BASE_URL = os.environ.get('BASE_URL')
SECRET_KEY = os.environ.get('SECRET_KEY')
AUTH_CODE = os.environ.get('AUTH_CODE')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')

# amo status


def init_status(x): return set(int(status)
                               for status in (x or '0').split(';'))


ERROR_STATUS = {}


class StatusMatch:
    def __init__(self, status_code: str):
        self.status_code = status_code
        self.status_set: set[int] = set()
        self.previous_status_set: set[int] = set()

    def match(self, previous_status, status):
        return int(previous_status in self.previous_status_set) + int(status in self.status_set) * 2

    def previous(self, status_id):
        self.previous_status_set.add(status_id)

    def current(self, status_id):
        self.status_set.add(status_id)


CREATE_BOOKING = StatusMatch('create_booking')
DELETE_BOOKING = StatusMatch('delete_booking')
CREATE_STAY = StatusMatch('create_stay')
DELETE_STAY = StatusMatch('delete_stay')
DELETE_ALL = StatusMatch('delete_all')


STATUSES = [CREATE_BOOKING, DELETE_BOOKING,
            CREATE_STAY, DELETE_STAY, DELETE_ALL]

NAME_TO_STATUS = {
    'Устная бронь': (CREATE_BOOKING.current, DELETE_STAY.current, DELETE_BOOKING.previous),
    'Проживание': (CREATE_STAY.current, DELETE_STAY.previous),
    'Закрыто и не реализовано': (DELETE_ALL.current,),
    'Не обработано': (DELETE_STAY.current, DELETE_BOOKING.current),
    'Принимает решение': (DELETE_STAY.current, DELETE_BOOKING.current),
    'Бронь Оплачена': (DELETE_STAY.current, DELETE_BOOKING.previous),
}


def fetch_statuses():
    pipelines = Pipeline.objects.all()
    for pipeline in pipelines:
        statuses = pipeline.statuses
        for status in statuses:
            if status.name == 'Ошибка брони':
                ERROR_STATUS[pipeline.id] = status.id
                continue

            status_categories = NAME_TO_STATUS.get(status.name)
            if status_categories is not None:
                for status_class_function in status_categories:
                    status_class_function(status.id)


redis_client = redis.Redis(host=REDIS_HOST, port=6379)


settings = {
    "backup_file_path": "./tokens",
    "encryption_key": ENCRYPTION_KEY,
    "integration_id": INTEGRATION_ID,
    "secret_key": SECRET_KEY,
    "auth_code": AUTH_CODE,
    "base_url": BASE_URL,
    "redirect_uri": REDIRECT_URI,
}

tokens.default_token_manager(
    client_id=INTEGRATION_ID,
    client_secret=SECRET_KEY,
    subdomain='usadbavip',
    redirect_url=REDIRECT_URI,
    storage=tokens.RedisTokensStorage(
        redis_client),  # by default FileTokensStorage
)

tokens.default_token_manager.init(code=AUTH_CODE, skip_error=True)

fetch_statuses()
print(CREATE_BOOKING)
