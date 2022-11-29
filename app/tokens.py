import threading
from typing import Optional, Tuple

import httpx
from amocrm.v2 import exceptions, tokens

try:
    import app.settings as SETTINGS
    from app.settings import DATA, redis_client
except ModuleNotFoundError:
    import settings as SETTINGS
    from settings import DATA, redis_client


class TokensStorage:
    def get_access_token(self) -> Optional[str]:
        pass

    def get_refresh_token(self) -> Optional[str]:
        pass

    def save_tokens(self, access_token: str, refresh_token: str):
        pass


class RedisTokensStorage(TokensStorage):
    _ACCESS_TOKEN_KEY = "amocrm:access:token"
    _REFRESH_TOKEN_KEY = "amocrm:refresh:token"

    def __init__(self, client, ttl=None):
        self._ttl = ttl
        self._client = client

    def get_access_token(self) -> Optional[str]:
        token = self._client.get(self._ACCESS_TOKEN_KEY)
        if token:
            return token.decode()
        return None

    def get_refresh_token(self) -> Optional[str]:
        token = self._client.get(self._REFRESH_TOKEN_KEY)
        if token:
            return token.decode()
        return None

    def save_tokens(self, access_token: str, refresh_token: str):
        self._client.set(self._ACCESS_TOKEN_KEY, access_token, ex=self._ttl)
        self._client.set(self._REFRESH_TOKEN_KEY, refresh_token, ex=self._ttl)


class TokenManager(tokens.TokenManager):

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not isinstance(cls._instance, cls):
                cls._instance = object.__new__(cls, *args, **kwargs)
            return cls._instance

    def _get_new_tokens(self) -> Tuple[str, str]:
        refresh_token = self._storage.get_refresh_token()
        if not refresh_token:
            raise ValueError()
        body = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "redirect_uri": self._redirect_url,
        }
        response = httpx.post(
            "https://{}.amocrm.ru/oauth2/access_token".format(self.subdomain), json=body)
        if response.status_code == 200:
            data = response.json()
            return data["access_token"], data["refresh_token"]
        raise EnvironmentError(
            "Can't refresh token {}".format(response.json()))

    def update_tokens(self):
        token, refresh_token = self._get_new_tokens()
        self._storage.save_tokens(token, refresh_token)

    def get_access_token(self):
        token = self._storage.get_access_token()
        if not token:
            raise exceptions.NoToken(
                "You need to init tokens with code by 'init' method")
        return token

    def _is_expire(token: str):
        ...


storage = RedisTokensStorage(redis_client)


def get_token():
    return storage.get_access_token()
