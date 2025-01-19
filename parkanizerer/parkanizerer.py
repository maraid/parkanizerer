#! /usr/bin/env python3

import argparse
import logging
import pathlib
import sys
import os
import tomllib

from api.parkanizer_api import ParkanizerApi
from book_desk import book_desk

FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(format=FORMAT, stream=sys.stdout, level=logging.INFO)

DIR = pathlib.Path(__file__).parents[1].resolve() if os.getenv("RUNNING_IN_DOCKER") is None else pathlib.Path("/config")
DEFAULT_CONFIG_PATH = DIR / "config.toml"


def load_config(config_path):
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    data["weekdays"] = [
        d.lower() for d in data.get("weekdays", [])
    ]
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Parkanizer Tool", 
                                     description=(
                                         "If no weekdays specified in the config file this will try to book "
                                         "a desk for the current weekday in advance for all the weeks that is "
                                         "available on parkanizer."
                                         "Otherwise it'll take those days and try to do the same thing with them."
                                     ))
    parser.add_argument(
        "-c",
        "--config",
        help="Specify path to config file. default: ./config.toml",
        default=DEFAULT_CONFIG_PATH,
        metavar="\b",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    papi = ParkanizerApi()
    papi.login(config["username"], config["password"])
    book_desk(
        papi.zones,
        config["zone"],
        config["desk"],
        config["weekdays"],
    )
