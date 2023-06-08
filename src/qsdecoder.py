from urllib.parse import unquote
from typing import Any, Callable, Coroutine

import qsparser
import ujson
from fastapi import Request, Response
from fastapi.routing import APIRoute

from starlette.datastructures import Headers


class QSRequest(Request):
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            body = await super().body()
            body = qsparser.parse(unquote(body.decode("utf-8")))
            self._body = ujson.dumps(
                body, encode_html_chars=False, ensure_ascii=False
            ).encode()
        return self._body

    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            headers = self.scope.get("headers", [])
            headers = dict(headers)
            headers[b"content-type"] = b"application/json"
            self.scope["headers"] = headers.items()
            self._headers = Headers(scope=self.scope)
        return self._headers


class QSEncodedRoute(APIRoute):
    def get_route_handler(
        self,
    ) -> Callable[..., Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = QSRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
