from typing import Optional, Callable
# from app.settings import _1c_repr
# from app.interactions import manager1C


class StatusMap:
    booking = {
        "Бронь оплачена",
        "Устная бронь"
    }
    stay = {
        "Проживание",
    }
    delete = {
        "Закрыто и не реализовано"
    }
    ignore = {
        'Выезд'
    }


class Status:

    statuses = {}

    def __init__(self, id: int, name: str, pipeline_id: int) -> None:
        self.id = id
        self.name = name
        self.pipeline_id = pipeline_id
        self.statuses[id] = self

    @classmethod
    def register(cls, id: int, name: str, pipeline_id: int):
        # _1c_status = _1c_repr(name)
        instance = cls(id, name, pipeline_id)
        cls.statuses[id] = instance
        return instance


class Condition:

    def match(self, lead_status: int, _1c_status: dict) -> bool:
        ...

    @property
    def status_name(self):
        return self.__class__.__name__

    def get_amo_status(self, lead_status: int):
        print('статусы', lead_status, Status.statuses)
        status = Status.statuses.get(lead_status)
        return status

    def __repr__(self) -> str:
        return f"Статус {self.status_name}"


class create_or_update_booking(Condition):

    def match(self, lead_status: int, _1c_status: dict) -> bool:
        status = self.get_amo_status(lead_status)
        if not status:
            return False
        if status.name in StatusMap.ignore:
            return

        return status.name in StatusMap.booking and _1c_status != 'stay'


class create_or_update_stay(Condition):

    def match(self, lead_status: int, _1c_status: dict) -> bool:
        status = self.get_amo_status(lead_status)
        if not status:
            return False
        if status.name in StatusMap.ignore:
            return
        return status.name in StatusMap.stay


class delete_booking(Condition):

    def match(self, lead_status: int, _1c_status: dict) -> bool:
        status = self.get_amo_status(lead_status)
        if not status:
            return False
        if status.name in StatusMap.ignore:
            return
        return _1c_status == 'booking' \
            and (status.name not in StatusMap.booking
                 and status.name not in StatusMap.stay) \
            or status.name in StatusMap.delete


class delete_stay(Condition):

    def match(self, lead_status: int, _1c_status: dict) -> bool:
        status = self.get_amo_status(lead_status)
        if not status:
            return False
        if status.name in StatusMap.ignore:
            return
        return status.name not in StatusMap.stay \
            and _1c_status == 'stay'


class delete_all(Condition):

    def match(self, lead_status: int, _1c_status: dict) -> bool:
        status = self.get_amo_status(lead_status)
        if not status:
            return False
        if status.name in StatusMap.ignore:
            return
        return _1c_status == 'stay' \
            and status.name in StatusMap.delete


statuses = [sub() for sub in Condition.__subclasses__()]


def match_status(lead_status: int, _1c_status):
    print(lead_status, _1c_status, statuses)
    for status_entry in statuses:
        print(status_entry)
        m = status_entry.match(lead_status, _1c_status)
        if m:
            return status_entry.status_name
