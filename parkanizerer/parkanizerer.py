#! /usr/bin/env python3

import argparse
import logging
import pathlib
import sys
import tomllib
from datetime import datetime

from api import utils
from api.parkanizer_api import ParkanizerApi
from book_desk import book_desk
from generate_map import generate_map

FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(format=FORMAT, stream=sys.stdout, level=logging.INFO)

ROOT_DIR = pathlib.Path(__file__).parents[1].resolve()
DEFAULT_CONFIG_PATH = ROOT_DIR / "config.toml"
DEFAULT_RESULTS_PATH = ROOT_DIR / "generated_maps"


def load_config(config_path):
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    data["book-desk"]["weekdays"] = [
        d.lower() for d in data["book-desk"].get("weekdays", [])
    ]
    data["generate-map"]["vip"] = data.get("vip", [])
    data["generate-map"]["result"] = data.get("result", "")
    return data


def login(config):
    papi = ParkanizerApi()
    papi.login(config["credentials"]["username"], config["credentials"]["password"])
    return papi


def run_generate_map(config: dict, args):
    papi = login(config)
    result = pathlib.Path(
        args.result or config["generate-map"].get("result") or DEFAULT_RESULTS_PATH
    )
    generate_map(
        papi.employees, papi.zones, args.date, result, config["generate-map"]["vip"]
    )


def run_book_desk(config, args):
    papi = login(config)
    book_desk(
        papi.zones,
        config["book-desk"]["zone"],
        config["book-desk"]["desk"],
        config["book-desk"]["weekdays"],
    )


def main():
    parser = argparse.ArgumentParser("Parkanizer Tool")
    parser.add_argument(
        "-c",
        "--config",
        help="Specify path to config file. default: ./config.toml",
        default=DEFAULT_CONFIG_PATH,
        metavar="\b",
    )

    subparsers = parser.add_subparsers(title="subcommands", required=True)
    book_desk_parser = subparsers.add_parser(
        "book-desk",
        help="Book a desk for each available day",
        description=(
            "If no weekdays specified in the config file this will try to book "
            "a desk for the current weekday in advance for all the weeks that is "
            "available on parkanizer."
            "Otherwise it'll take those days and try to do the same thing with them."
        ),
    )
    book_desk_parser.set_defaults(func=run_book_desk)

    generate_map_parser = subparsers.add_parser(
        "generate-map", help="Generate map of seatings on specified date."
    )
    generate_map_parser.set_defaults(func=run_generate_map)
    generate_map_parser.add_argument(
        "-d",
        "--date",
        help="Date to look for reservations on. format: YYYY-MM-DD. default: today",
        default=utils.date_to_str(datetime.today()),
        type=lambda s: utils.str_to_date(s),
        metavar="\b",
    )

    generate_map_parser.add_argument(
        "-r",
        "--result",
        help="Directory to put the generated images. default: ./generatedmaps",
        default="",
        metavar="\b",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    args.func(config, args)


if __name__ == "__main__":
    main()
