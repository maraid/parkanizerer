from datetime import datetime

DATE_FORMAT = r"%Y-%m-%d"


def date_to_str(date: datetime) -> str:
    return datetime.strftime(date, DATE_FORMAT)


def str_to_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FORMAT)