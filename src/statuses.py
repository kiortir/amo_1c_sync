from _1c import LeadStatus1C


class StatusMap:
    booking = {"Бронь оплачена", "Устная бронь"}
    stay = {
        "Проживание",
    }
    delete = {"Закрыто и не реализовано"}
    ignore = {"Выезд"}


class Status:
    statuses: dict[int, "Status"] = {}

    def __init__(self, id: int, name: str, pipeline_id: int) -> None:
        self.id = id
        self.name = name
        self.pipeline_id = pipeline_id
        self.statuses[id] = self


class Condition:
    def match_condition(
        self, status: Status, _1c_status: LeadStatus1C
    ) -> bool:
        raise NotImplementedError

    @property
    def status_name(self) -> str:
        return self.__class__.__name__

    def get_amo_status(self, lead_status: int) -> Status | None:
        status = Status.statuses.get(lead_status)
        return status

    def __repr__(self) -> str:
        return f"Статус {self.status_name}"


class create_or_update_booking(Condition):
    def match_condition(
        self, status: Status, _1c_status: LeadStatus1C
    ) -> bool:
        return (
            status.name in StatusMap.booking
            and _1c_status is not LeadStatus1C.STAY
        )


class create_or_update_stay(Condition):
    def match_condition(
        self, status: Status, _1c_status: LeadStatus1C
    ) -> bool:
        return status.name in StatusMap.stay


class delete_booking(Condition):
    def match_condition(
        self, status: Status, _1c_status: LeadStatus1C
    ) -> bool:
        return _1c_status is LeadStatus1C.BOOKING and (
            status.name in StatusMap.delete
            or (
                status.name not in StatusMap.booking
                and status.name not in StatusMap.stay
            )
        )


class delete_stay(Condition):
    def match_condition(
        self, status: Status, _1c_status: LeadStatus1C
    ) -> bool:
        return (
            status.name not in StatusMap.stay
            and _1c_status is LeadStatus1C.STAY
            and status.name not in StatusMap.delete
        )


class delete_all(Condition):
    def match_condition(
        self, status: Status, _1c_status: LeadStatus1C
    ) -> bool:
        return (
            _1c_status is LeadStatus1C.STAY
            and status.name in StatusMap.delete
        )


statuses = [sub() for sub in Condition.__subclasses__()]
statuses.sort(key=lambda x: getattr(x, "sort_value", 0))


def match_status(lead_status: int, _1c_status: LeadStatus1C) -> str | None:
    status = Status.statuses.get(lead_status)
    if not status or status.name in StatusMap.ignore:
        return None

    for status_entry in statuses:
        match = status_entry.match_condition(status, _1c_status)
        if match:
            return status_entry.status_name

    return None
