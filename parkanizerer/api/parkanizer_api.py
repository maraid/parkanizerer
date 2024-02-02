from . import models
from . import session


class ParkanizerApi:
    def __init__(self):
        self.zones = models.ZoneManager()
        self.employees = models.EmployeeManager(self.zones)
        self._myself: models.Myself | None = None

    @property
    def myself(self) -> models.Myself:
        if self._myself is None:
            data_dict = session.parkanizer.get_employee_reservations()
            self._myself = models.Myself.from_dict(data_dict)
            self._myself.reservations = models.MyReservationManager(
                self._myself, self.zones
            )
        return self._myself

    def login(self, username: str, password: str) -> None:
        session.parkanizer.login(username, password)
