from pathlib import Path

from pydantic import BaseModel, BaseSettings


class AmoSettings(BaseSettings):
    encryption_key: str = ""
    integration_id: str = ""

    base_url: str = ""
    secret_key: str = ""
    auth_code: str = ""
    redirect_uri: str = ""

    class Config:
        env_file = ".amo.env"
        env_file_encoding = "utf-8"


class RedisSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379


class SettingsPath(BaseSettings):
    settings_path: Path = Path(".")
    sauna_path: Path = Path("sauna_list.yml")


class RabbitSettings(BaseSettings):
    rabbit_host: str = "localhost"


settings_files = SettingsPath()


class SaunaNames(BaseModel):
    __root__: dict[str, str] = {
        "Альпийская": "ЦБ000027",
        "Деревенская": "ЦБ000001",
        "Каменная": "ЦБ000016",
        "Русская": "ЦБ000005",
        "Скандинавская": "ЦБ000015",
        "Славянская": "ЦБ000017",
        "Турецкая": "ЦБ000003",
        "Финская": "ЦБ000006",
        "Японская": "ЦБ000007",
        "Римская": "ЦБ100018",
    }

    def match(self, sauna_name: str) -> str | None:
        for type_, code in self.__root__.items():
            if sauna_name.lower().startswith(type_.lower()):
                return code

        return None


class _1cSettings(BaseSettings):
    endpoint: str = (
        "https://webhook.site/8559a65b-3ffb-4da0-b594-e27e60e6d245"
    )
    # status_endpoint: AnyHttpUrl


amo_settings = AmoSettings()
redis_settings = RedisSettings()
_1c_settings = _1cSettings()


sauna_names = SaunaNames()
# sauna_names.init()

ERROR_STATUS: dict[int, int] = {}
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
