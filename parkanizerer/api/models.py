import io
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterator

from . import utils
from .session import parkanizer

# COMMON


class ApiItem:
    def from_dict(self, data_dict: dict):
        raise NotImplementedError


@dataclass
class ApiItemWithPK(ApiItem):
    """Api Item With Primary Key (i.e. ID)"""

    id: str
    name: str


class ApiItemManagerBase[T: ApiItem](Iterable):
    def __init__(self):
        self._data: list[T] = []

    def __getitem__(self, item) -> T:
        try:
            return self.get()[item]
        except TypeError:
            return self.find_by_pk(item)

    def __iter__(self):
        yield from self.get()

    def __len__(self) -> int:
        return len(self._data)

    def get(self, force: bool = False) -> list[T]:
        if not self._data or force:
            self._data = [self._create_obj(d) for d in self._fetch()]
        return self._data

    def filter(self, func: callable) -> Iterator[T]:
        yield from (d for d in self.get() if func(d))

    def find_by_pk(self, pk) -> T:
        """Find by primary key"""
        raise NotImplementedError

    def _create_obj(self, d: dict) -> T:
        raise NotImplementedError

    def _fetch(self) -> list[dict]:
        raise NotImplementedError


class ApiItemWithPKManagerBase[T: ApiItemWithPK](ApiItemManagerBase[T]):
    def find_by_pk(self, pk: str) -> T:
        return next(self.filter(lambda x: x.id == pk))

    def find(self, name: str) -> T | None:
        try:
            return next(self.filter(lambda x: x.name == name))
        except StopIteration:
            return None


# DESK


@dataclass
class Desk(ApiItemWithPK):
    class State(Enum):
        FREE = 1
        RESERVED = 2
        UNKNOWN = 3

        @classmethod
        def from_string(cls, data_str: str) -> "Desk.State":
            return {"Free": cls.FREE, "ReservedBy": cls.RESERVED}.get(
                data_str, cls.UNKNOWN
            )

    x: float
    y: float
    radius: float
    state: State
    _zone = None

    @classmethod
    def from_dict(cls, data_dict: dict) -> "Desk":
        return cls(
            data_dict["id"],
            data_dict["nameOrNull"],
            float(data_dict["x"]),
            float(data_dict["y"]),
            float(data_dict["radius"]),
            cls.State.from_string(data_dict["state"]),
        )

    def take(self, selected_date=datetime.today()):
        response = parkanizer.take_desk(self._zone.id, self.id, selected_date)
        if message := response.get("message"):
            if message == "An error has occurred.":
                logging.info("Failed to book desk. It might have been mine already.")
            else:
                logging.info(message)
        elif response.get("receivedDeskOrNull") is not None:
            logging.info(
                f"Booked desk [{self.name}] "
                f"in zone [{self._zone.name}] "
                f"for {utils.date_to_str(selected_date)}."
            )
        elif response.get("receivedDeskOrNull") is None:
            logging.info("Failed to book desk. It was already taken")
        else:
            logging.error(f"Failed to book desk. Response: {response.text}")


class DeskManager(ApiItemWithPKManagerBase[Desk]):
    def __init__(self, zone):
        super().__init__()
        self._zone: Zone = zone

    def _fetch(self) -> list[dict]:
        return parkanizer.get_desk_zone_map(self._zone.id)

    def _create_obj(self, d: dict) -> Desk:
        desk = Desk.from_dict(d)
        desk._zone = self._zone
        return desk


# ZONE


@dataclass
class Zone(ApiItemWithPK):
    is_map_available: bool
    desks: DeskManager | None = None
    _available_days: list[datetime] = field(default_factory=list)

    def __post_init__(self):
        self.desks: DeskManager = DeskManager(self)

    @classmethod
    def from_dict(cls, data_dict: dict) -> "Zone":
        return cls(data_dict["id"], data_dict["name"], data_dict["isMapAvailable"])

    def get_available_days(self, force: bool = False):
        if not self._available_days or force:
            self._available_days = parkanizer.get_available_days(self.id)
        return self._available_days

    def get_map(self) -> io.BytesIO:
        if self.is_map_available:
            return parkanizer.get_zone_image(self.id)


class ZoneManager(ApiItemWithPKManagerBase[Zone]):
    def _fetch(self) -> list[dict]:
        return parkanizer.get_zones()

    def _create_obj(self, d: dict) -> Zone:
        return Zone.from_dict(d)


# RESERVATION


@dataclass
class Reservation(ApiItem):
    day: datetime
    # In the first step zone and desk are filled with ID
    # In the second step they are replaced by zone and desk objects respectively
    zone: Zone | str
    desk: Desk | str

    @classmethod
    def from_dict(cls, data_dict: dict):
        return cls(
            utils.str_to_date(data_dict["date"]),
            data_dict["deskZoneId"],
            data_dict["deskId"],
        )


class ReservationManager(ApiItemManagerBase[Reservation]):
    def __init__(self, employee: "Employee", zones: ZoneManager):
        super().__init__()
        self._employee: "Employee" = employee
        self._zones: ZoneManager = zones

    def find_by_pk(self, pk: datetime) -> Reservation | None:
        try:
            return next(self.filter(lambda x: x.day.date() == pk.date()))
        except StopIteration:
            return None

    def _fetch(self) -> list[dict]:
        return parkanizer.get_employee_reservations(self._employee.id)

    def _create_obj(self, d: dict) -> Reservation:
        reservation = Reservation.from_dict(d)
        reservation.zone = self._zones[reservation.zone]
        reservation.desk = reservation.zone.desks[reservation.desk]
        return reservation


# EMPLOYEE


@dataclass
class Employee(ApiItemWithPK):
    reservations: ReservationManager | None = None

    @classmethod
    def from_dict(cls, data_dict: dict) -> "Employee":
        return cls(data_dict["employeeId"], data_dict["fullName"])


class EmployeeManager(ApiItemWithPKManagerBase[Employee]):
    def __init__(self, zones: ZoneManager):
        super().__init__()
        self._zones = zones

    def search(self, query: str):
        """Find employee by partial name by using the search endpoint instead of filtering all employees"""
        return [self._create_obj(d) for d in parkanizer.search_colleague(query)]

    def _fetch(self) -> list[dict]:
        return parkanizer.get_employees()

    def _create_obj(self, d: dict) -> Employee:
        employee = Employee.from_dict(d)
        employee.reservations = ReservationManager(employee, self._zones)
        return employee


# MYSELF


class Myself(Employee):
    @classmethod
    def from_dict(cls, data_dict: dict) -> "Employee":
        return cls(data_dict["id"], data_dict["fullName"])


class MyReservationManager(ReservationManager):
    def get(self, force: bool = False) -> list[Reservation]:
        if not self._data or force:
            for d in self._fetch():
                if d["status"] == "Reserved":
                    d.update(d["reservedDeskOrNull"])
                    self._data.append(Reservation.from_dict(d))
        return self._data

    def _fetch(self) -> list[dict]:
        return parkanizer.get_my_reservations()
