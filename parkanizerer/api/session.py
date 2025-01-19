import io
import logging
import pathlib
import pickle
from datetime import datetime, timedelta

from requests import Session

from . import auth, utils

PARKANIZER_API = "https://share.parkanizer.com/api"
ROOT_DIR = pathlib.Path(__file__).parents[1].resolve()


class ParkanizerSession:
    def __init__(self):
        self.session: Session = Session()

    def login(self, username: str, password: str):
        try:
            logging.info("Trying to authenticate with stored secrets")
            with open(ROOT_DIR / "session_secrets", "rb") as f:
                session_secrets = pickle.load(f)
            self._set_secrets(*(session_secrets.values()))
            self._try_refresh_token()
            logging.info("Successfully authenticated with stored secrets")

        except (FileNotFoundError, pickle.UnpicklingError, KeyError, EOFError, TypeError):
            logging.info(
                "Failed to authenticate with stored secrets. Trying with normal login."
            )
            session_secrets = auth.get_token(username, password)
            logging.info("Authenticated with username and password")
            self._set_secrets(*(session_secrets.values()))

        with open(ROOT_DIR / "session_secrets", "wb") as f:
            pickle.dump(session_secrets, f)

    def _try_refresh_token(self):
        url = PARKANIZER_API + "/auth0/try-refresh-token"
        response = self.session.post(url, json={})
        self._set_secrets(
            response.json()["newTokenOrNull"]["accessToken"],
            response.cookies["refresh_token"],
        )

    def get_zones(self) -> list[dict[str, str]]:
        url = PARKANIZER_API + "/employee-desks/desk-marketplace/get-marketplace-zones"
        return self._post(url)["zones"]

    def get_employees(self) -> list[dict[str, str]]:
        url = PARKANIZER_API + "/employee-reservations/get-employees"
        # For some reason management people are not listed in today's query
        days_to_share = utils.date_to_str(datetime.today() + timedelta(days=32))
        payload = {"daysToShare": [days_to_share]}
        return self._post(url, payload)["employeesOrNull"]

    def get_desk_zone_map(
        self, zone_id: str, date: datetime = datetime.today()
    ) -> list[dict[str, str]]:
        url = (
            PARKANIZER_API
            + "/employee-desks/desk-marketplace/get-marketplace-desk-zone-map"
        )
        payload = {"date": utils.date_to_str(date), "deskZoneId": zone_id}
        return self._post(url, payload)["mapOrNull"]["desks"]

    def get_available_days(self, zone_id: str) -> list[datetime]:
        url = PARKANIZER_API + "/employee-desks/desk-marketplace/get-marketplace-desks"
        payload = {"zoneId": zone_id}
        return [
            utils.str_to_date(day["day"])
            for week in self._post(url, payload)["weeks"]
            for day in week["week"]
        ]

    def get_employee_reservations(self, employee_id: str) -> list[dict[str, str]]:
        url = (
            PARKANIZER_API
            + "/employee-desks/colleague-finder/get-colleague-desk-reservations"
        )
        payload = {"colleagueId": employee_id}
        return self._post(url, payload)["deskReservations"]

    def take_desk(self, zone_id: str, desk_id: str, day: datetime):
        url = PARKANIZER_API + "/employee-desks/desk-marketplace/take"
        payload = {
            "dayToTake": utils.date_to_str(day),
            "zoneId": zone_id,
            "deskIdOrNull": desk_id,
        }
        return self._post(url, payload)

    def release_desk(self, day: datetime):
        url = PARKANIZER_API + "/employee-desks/share-desk/free"
        payload = {"daysToShare": utils.date_to_str(day)}
        return self._post(url, payload)

    def get_zone_image(self, zone_id: str) -> io.BytesIO:
        url = (
            PARKANIZER_API + "/components/desk-zone-map/desk-zone-map-image/" + zone_id
        )
        response = self.session.get(url)
        if response.status_code == 200:
            return io.BytesIO(response.content)

    def get_my_context(self):
        url = PARKANIZER_API + "/get-employee-context"
        payload = {}
        return self._post(url, payload)

    def get_my_reservations(self):
        url = PARKANIZER_API + "/employee-desks/my-desk/initialize-my-desk-view"
        return self._get(url)["reservations"]

    def search_colleague(self, query: str) -> list[dict]:
        url = PARKANIZER_API + "/employee-desks/colleague-finder/search"
        payload = {"fullNameQuery": query}
        return self._post(url, payload)["foundEmployees"]

    def _post(self, url, payload=None) -> dict:
        return self.session.post(url, json=payload).json()

    def _get(self, url) -> dict:
        return self.session.get(url).json()

    def _set_secrets(self, bearer_token, access_token):
        self.session.headers.update({"Authorization": "Bearer " + bearer_token})
        self.session.cookies.update({"refresh_token": access_token})


parkanizer = ParkanizerSession()
