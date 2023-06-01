import os

import redis
from typing_extensions import Self
from pydantic import BaseSettings


DEBUG = os.environ.get("DEBUG", "TRUE") == "TRUE"

# if DEBUG:
#     from dotenv import load_dotenv
#     load_dotenv()

# ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
# INTEGRATION_ID = os.environ.get("INTEGRATION_ID")

# BASE_URL = os.environ.get("BASE_URL")
# SECRET_KEY = os.environ.get("SECRET_KEY")
# AUTH_CODE = os.environ.get("AUTH_CODE")
# REDIRECT_URI = os.environ.get("REDIRECT_URI")
# REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
# ENDPOINT = os.environ.get("ENDPOINT", "https://google.com")

ERROR_STATUS = {}


class Settings(BaseSettings):
    debug: bool = False
    is_root: bool = False


base_settings = Settings()


class AmoSettings(BaseSettings):
    encryption_key: str
    integration_id: str
    base_url: str
    secret_key: str
    redirect_uri: str

    auth_code: str


class RedisSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379


class UsadbaSettings(BaseSettings):
    endpoint: str


usadba_settings = UsadbaSettings()

_1c_repr_map = {
    "booking": {"Устная бронь", "Бронь оплачена"},
    "stay": {"Проживание"},
}


def _1c_repr(status_name: str):
    for _1c_status, statuses in _1c_repr_map.items():
        if status_name in statuses:
            return _1c_status


class StatusMatch:
    statuses: list["StatusMatch"] = []

    def __new__(cls: type[Self], *args, **kwargs) -> Self:
        instance = super().__new__(cls)
        cls.statuses.append(instance)
        return instance

    def __init__(
        self, status_code: str, status_endpoint: str, _1c_status=None
    ):
        self.status_code = status_code
        self.status_set: set[int] = set()
        self.previous_status_set: set[int] = set()
        self.endpoint = status_endpoint

    def match(self, previous_status, status):
        total_match = 0

        current_match = status in self.status_set
        if not current_match:
            return total_match
        total_match += 2
        if len(self.previous_status_set):
            previous_match = previous_status in self.previous_status_set
            if previous_match:
                total_match += 1
            else:
                return 0

        return total_match

    @classmethod
    def get_status(cls, previous_status_id: int, status_id: int):
        max_match_value = 0
        max_match_status = None
        for status in cls.statuses:
            match_value = status.match(previous_status_id, status_id)
            if match_value > max_match_value:
                max_match_value = match_value
                # max_match_status_code = status.status_code

                max_match_status = status

        return max_match_status if max_match_value else None

    def previous(self, status_id):
        self.previous_status_set.add(status_id)

    def current(self, status_id):
        self.status_set.add(status_id)


redis_settings = RedisSettings()
redis_client = redis.Redis(
    host=redis_settings.redis_host, port=redis_settings.redis_port
)


SUBDOMAIN = "usadbavip"

amo_settings = AmoSettings()
DATA = {
    "client_id": amo_settings.integration_id,
    "client_secret": amo_settings.secret_key,
    "subdomain": SUBDOMAIN,
    "redirect_url": amo_settings.redirect_uri,
}

STATUS_TO_DESCRIPTION_MAP = {
    "create_or_update_booking": {
        "create": "бланк брони создан в 1С",
        "error": "ошибка при создании бланка брони в 1С",
        "update": "бланк брони обновлен в 1С",
        "error_update": "ошибка обновления бланка брони в 1С",
    },
    "update_booking": {
        "ok": "бланк брони обновлен в 1С",
        "error": "ошибка при обновлении бланка брони в 1С",
    },
    "delete_booking": {
        "ok": "бланк брони удален в 1С",
        "error": "ошибка при удалении бланка брони в 1С",
    },
    "create_or_update_stay": {
        "ok": "бланк проживания создан в 1С",
        "error": "ошибка связи с 1С при создании бланка проживания",
        "update": "бланк брони обновлен в 1С",
        "error_stay": "ошибка обновления бланка брони в 1С",
    },
    "update_stay": {
        "ok": "бланк проживания обновлен в 1С",
        "error": "ошибка при обновлении бланка проживания в 1С",
    },
    "delete_stay": {
        "ok": "бланк проживания удален в 1С",
        "error": "ошибка при удалении бланка проживания в 1С",
    },
    "delete_all": {
        "ok": "бланк брони и бланк проживания удалены в 1С",
        "error": "ошибка при удалении бланка брони и проживания в 1С",
    },
}
