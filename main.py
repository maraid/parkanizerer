#!/usr/bin/env python3

import requests
from datetime import datetime, timedelta
import json
from auth import get_token
import os


PARKANIZER_URI = "https://share.parkanizer.com"


def load_config():
    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, "config.json"), "r") as f:
        return json.load(f)


def one_week_from_now():
    next_week = datetime.today() + timedelta(days=7)
    return next_week.strftime(r"%Y-%m-%d")

def get_next_week_days():
    result = []
    
    if not config.get("days_of_week", []):
        result.append(one_week_from_now())
    else:
        for dow in config["days_of_week"]:
            today = datetime.today()
            days_left = (dow - today.weekday()) % 7
            next_day = today + datetime.timedelta(days=days_left)
            result.append(next_day.strftime(r"%Y-%m-%d"))

    return result

def fetch_zone_id(zone_name):
    r = session.post(
        PARKANIZER_URI + "/api/employee-desks/desk-marketplace/get-marketplace-zones"
    )
    return next(zone["id"] for zone in r.json()["zones"] if zone["name"] == zone_name)


def fetch_desk_id(desk_name, zone_id, day_to_take):
    r = session.post(
        PARKANIZER_URI + "/api/employee-desks/desk-marketplace/get-marketplace-desk-zone-map",
        json={
            "deskZoneId": zone_id, 
            "date": day_to_take
        }
    )
    return next(desk for desk in r.json()["mapOrNull"]["desks"]
                if desk["nameOrNull"] == '{0:02d}'.format(int(desk_name)))["id"]


if __name__ == "__main__":
    config = load_config()

    bearer_token = get_token(config["parkanizer_user"], config["parkanizer_pass"])
    session = requests.Session()
    session.headers.update({"Authorization": bearer_token})

    days_to_take = get_next_week_days()
    
    for day in days_to_take:
        zone_id = fetch_zone_id(config["zone_name"])
        desk_id = fetch_desk_id(config["desk_name"], zone_id, day)

        response = session.post(
            PARKANIZER_URI + "/api/employee-desks/desk-marketplace/take",
            json={
                "dayToTake": day,
                "zoneId": zone_id,
                "deskIdOrNull": desk_id
            }
        )

        if message := response.json().get('message'):
            print(message)
        elif response.json().get('receivedDeskOrNull'):
            print(f"Booked desk [{config['desk_name']}] " 
                f"in zone [{config['zone_name']}] "
                f"for {day}.")
