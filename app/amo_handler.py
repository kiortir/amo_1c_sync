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


STATUS_MAP = defaultdict(set)

ERROR_STATUS = {}

NAME_TO_STATUS = {
    'Устная бронь': ('create_booking', 'delete_stay', 'pre__delete_booking'),
    'Проживание': ('create_stay', 'pre__delete_stay'),
    'Закрыто и не реализовано': ('delete_booking',),
    'Не обработано': ('delete_stay', 'delete_booking'),
    'Принимает решение': ('delete_stay', 'delete_booking'),
    'Бронь Оплачена': ('delete_stay', 'pre__delete_booking'),
}


class StatusMatch:
    def __init__(self):
        self.status_set: set[int] = set()
        self.previous_status_set: set[int] = set()

    def match(self, status, previous_status):
        pass



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
                for status_category in status_categories:
                    STATUS_MAP[status_category].add(status.id)


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
print(STATUS_MAP)
