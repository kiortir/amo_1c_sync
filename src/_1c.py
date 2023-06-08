from enum import Enum
import httpx
from settings import _1c_settings
from typing import Any


class LeadStatus1C(str, Enum):
    BOOKING = "booking"
    STAY = "stay"


class InteractionManager:
    # def __init__(self) -> None:
    #     self.client = httpx.AsyncClient(follow_redirects=True)

    async def post(self, data: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _1c_settings.endpoint, json=data, timeout=120000
            )
            if response.status_code != 200:
                raise Exception("1с не вернул ответ 200")
            return response

    async def sync(self, data: dict[str, Any]) -> str:
        response = await self.post(data)
        return response.content.decode("utf-8-sig")

    async def get_reservation_status(
        self, lead_id: int
    ) -> LeadStatus1C | None:
        q = {"id": lead_id, "status": "blank_status"}
        response = await self.post(q)
        json = response.json()
        if json.get(LeadStatus1C.STAY) != "none":
            return LeadStatus1C.STAY
        if json.get(LeadStatus1C.BOOKING) != "none":
            return LeadStatus1C.BOOKING
        return None


manager1C = InteractionManager()
