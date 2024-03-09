from datetime import datetime

from api.models import Desk, Zone, ZoneManager


def book_desk(
    zones: ZoneManager, zone_name: str, desk_name: str, wanted_weekdays: list[str]
):
    zone: Zone = zones.find(zone_name)
    desk: Desk = zone.desks.find(desk_name)
    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")  # fmt:skip
    wanted_weekdays = [weekdays.index(day) for day in wanted_weekdays]
    if wanted_weekdays:
        days_to_book = [
            day for day in zone.get_available_days() if day.weekday() in wanted_weekdays
        ]
    else:
        days_to_book = [
            day
            for day in zone.get_available_days()
            if ((day - datetime.today()).days % 7) == 6
        ]

    for day in days_to_book:
        desk.take(day)
