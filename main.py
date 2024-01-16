#!/usr/bin/env python3

import requests
from datetime import datetime
import tomllib as toml
from auth import get_token
import os
from unicodedata import normalize

API = "https://share.parkanizer.com/api/employee-desks/desk-marketplace"
DATE_FORMAT = r"%Y-%m-%d"


def date_to_str(date: datetime) -> str:
    return datetime.strftime(date, DATE_FORMAT)


def str_to_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FORMAT)


def load_config():
    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, "config.toml"), "rb") as f:
        data = toml.load(f)
    data["wanted"]["weekdays"] = [d.lower() for d in data["wanted"].get("weekdays", [])]
    return data


def fetch_zone_id(zone_name: str) -> str:
    response = session.post(API + "/get-marketplace-zones")
    zones = [
        {"id": zone["id"], "name": normalize("NFKD", zone["name"])}
        for zone in response.json()["zones"]
    ]
    try:
        return [zone["id"] for zone in zones if zone["name"] == zone_name][0]
    except IndexError:
        raise ValueError(
            f"No zone found with name [{zone_name}]"
            f", available zones: [{[zone['name'] for zone in zones]}]"
        )


def get_available_days(zone_id: str) -> list[datetime]:
    response = session.post(
        API + "/get-marketplace-desks",
        json={"zoneId": zone_id},
    )
    available_days = []
    for week in response.json()["weeks"]:
        for day in week["week"]:
            if day["reservedDeskOrNull"] is None:  # not taken by us yet
                available_days.append(str_to_date(day["day"]))
    return available_days


def fetch_desk_id(desk_name, zone_id, day_to_take):
    response = session.post(
        API + "/get-marketplace-desk-zone-map",
        json={"deskZoneId": zone_id, "date": day_to_take},
    )
    return next(
        desk
        for desk in response.json()["mapOrNull"]["desks"]
        if desk["nameOrNull"] == "{0:02d}".format(int(desk_name))
    )["id"]


def book_desk(zone_id: str, desk_id: str, day: str):
    response = session.post(
        API + "/take",
        json={"dayToTake": day, "zoneId": zone_id, "deskIdOrNull": desk_id},
    )
    if message := response.json().get("message"):
        print(message)
    elif response.json().get("receivedDeskOrNull") is not None:
        print(
            f"Booked desk [{config['wanted']['desk']}] "
            f"in zone [{config['wanted']['zone']}] "
            f"for {day}."
        )
    elif response.json().get("receivedDeskOrNull") is None:
        print("Failed to book desk. It was already taken")
    else:
        print(f"Failed to book desk. Response: {response.text}")


if __name__ == "__main__":
    config = load_config()

    bearer_token = get_token(*config["parkanizer"].values())
    session = requests.Session()
    session.headers.update({"Authorization": bearer_token})

    wanted_zone_id = fetch_zone_id(config["wanted"]["zone"])
    available_days_of_wanted_zone = get_available_days(wanted_zone_id)

    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")  # fmt:skip
    wanted_weekdays = [weekdays.index(day) for day in config["wanted"]["weekdays"]]
    if wanted_weekdays:
        days_to_book = [
            date_to_str(day)
            for day in available_days_of_wanted_zone
            if day.weekday() in wanted_weekdays
        ]
    else:
        days_to_book = [
            date_to_str(day)
            for day in available_days_of_wanted_zone
            if ((day.day + 1 - datetime.today().day) % 7) == 0
        ]

    print("days_to_book", days_to_book)
    for day in days_to_book:
        wanted_desk_id = fetch_desk_id(config["wanted"]["desk"], wanted_zone_id, day)
        book_desk(wanted_zone_id, wanted_desk_id, day)
