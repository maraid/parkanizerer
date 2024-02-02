import logging
import os
import pathlib
from datetime import datetime

import math
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

from api.models import EmployeeManager, Zone, ZoneManager


def generate_map(employees: EmployeeManager,
                 zones: ZoneManager,
                 day: datetime,
                 result: pathlib.Path,
                 vip: list[str]):
    lne = max(len(e.name) for e in employees)  # longest employee name length
    lnz = max(len(z.name) for z in zones)  # longest zone name length

    logging.info(
        f"|{'%'.ljust(6)}|{'Employee name'.ljust(lne)}|{'Zone'.ljust(lnz)}|Desk|"
    )
    booked_for_the_day = {}
    for i, e in enumerate(employees):
        if (r := e.reservations[day]) is not None:
            booked_for_the_day[r.desk.id] = e.name
        logging.info(
            f"|{f"{i / len(employees) * 100:.1f}%".ljust(6)}"
            f"|{e.name.ljust(lne)}"
            f"|{(r.zone.name if r is not None else '').ljust(lnz)}"
            f"|{(r.desk.name if r is not None else '').ljust(4)}|"
        )

    logging.info("Creating Images for the fetched zones")
    result.mkdir(exist_ok=True)
    img_handler = ImageHandler(zones, booked_for_the_day, vip)
    img_handler.create_images(result)

    logging.info(f"Opening result location: {result}")
    if sys.platform.startswith("win"):
        os.startfile(result)


class ImageHandler:
    def __init__(self, zones: ZoneManager, booked_for_the_day: dict[str, str], vip: list[str]):
        self.zones: ZoneManager = zones
        self.booked_for_the_day: dict[str, str] = booked_for_the_day
        self.vip: list[str] = vip

    def create_images(self, target: pathlib.Path):
        # #1 Find zones that has the same image to draw 1 big instead of multiple small ones
        zone_maps = [Image.open(zone.get_map()) for zone in self.zones]
        combined_maps = []
        for zone, m in zip(self.zones, zone_maps):
            found = False
            for cm in combined_maps:
                if ImageChops.difference(cm["map"], m).getbbox() is None:
                    cm["zone_list"].append(zone)
                    found = True
            if not found:
                combined_maps.append({"map": m, "zone_list": [zone]})

        # Draw the map
        for m in combined_maps:
            image = m["map"].convert("RGBA")
            self._draw_zones(image, m["zone_list"])
            image_path = target / (m["zone_list"][0].name + ".png")
            image.save(image_path)
            # logging.info(f"Created map for {zone.name} - {image_path.absolute()} ")

    def _draw_zones(self, image: Image.Image, zones: list[Zone]):
        # image.convert()
        for zone in zones:
            self._draw_zone_name(image, zone)
            self._draw_names(image, zone)

    def _draw_zone_name(self, im: Image.Image, zone: Zone):
        """Draw name of the zone as an overlay"""
        zbbox = [
            min(d.x for d in zone.desks) * im.width,
            min(d.y for d in zone.desks) * im.height,
            max(d.x for d in zone.desks) * im.width,
            max(d.y for d in zone.desks) * im.height
        ]
        a = zbbox[3] - zbbox[1]
        b = zbbox[2] - zbbox[0]
        c = (a ** 2 + b ** 2) ** (1 / 2)
        angle = math.degrees(math.asin(a / c))
        txt = Image.new("RGBA", im.size, (255, 255, 255, 0))
        font_size = 1000
        font = ImageFont.truetype("impact.ttf")
        d = ImageDraw.Draw(txt)
        if angle > 20:  # don't tilt unless it's more than 20 deg
            text_length = None
            while text_length is None or text_length > c:
                font_size -= 3
                font = font.font_variant(size=font_size)
                text_length = d.textlength(zone.name, font)
            tbbox = d.textbbox((zbbox[0], zbbox[1]), zone.name, font)
            text_a = tbbox[3] - tbbox[1]
            text_b = tbbox[2] - tbbox[0]
            text_x0 = zbbox[0] + (b - text_b) / 2
            text_y0 = zbbox[1] + (a - text_a) / 2
            d.text((text_x0, text_y0), zone.name, font=font, fill=(128, 128, 128, 64))
            txt = txt.rotate(-angle, center=(text_x0 + text_b / 2, text_y0 + text_a / 2))
        else:
            tbbox = tuple()
            while not tbbox or tbbox[2] > zbbox[2] or tbbox[3] > zbbox[3]:
                font_size -= 3
                font = font.font_variant(size=font_size)
                tbbox = d.textbbox((zbbox[0], zbbox[1]), zone.name, font)
            d.text((zbbox[0] + ((zbbox[2] - zbbox[0]) - (tbbox[2] - tbbox[0])) / 2,
                    zbbox[1] + ((zbbox[3] - zbbox[1]) - (tbbox[3] - tbbox[1])) / 2),
                   zone.name, font=font, fill=(128, 128, 128, 64))

        im.alpha_composite(txt)

    def _draw_names(self, im: Image.Image, zone: Zone):
        """Visualize desks: Name (or 'Unknown') if booked. Blue circle otherwise"""
        draw = ImageDraw.Draw(im)
        for desk in zone.desks:
            x = int(im.width * desk.x)
            y = int(im.height * desk.y)
            if desk.state.value == 1:
                r = desk.radius * im.width
                x0 = x - r / 2
                x1 = x + r / 2
                y0 = y - r / 2
                y1 = y + r / 2
                draw.arc((x0, y0, x1, y1), 0, 360, "midnightblue", 3)
            else:
                name = self.booked_for_the_day.get(desk.id, "Unknown")
                font = ImageFont.truetype("arial.ttf", 18, encoding="unic")
                _, _, width, height = draw.textbbox((0, 0), name, font)

                # draw a text on a new canvas
                txt_canvas = Image.new("L", (width, height))
                text_draw = ImageDraw.Draw(txt_canvas)
                text_draw.text((0, 0), name, font=font, fill=255)

                # rotate to avoid overlapping letters of adjacent names
                w = txt_canvas.rotate(-13, expand=True, resample=3)

                # paste the text on the image
                color = "darkgreen" if name in self.vip else "darkred"
                im.paste(
                    ImageOps.colorize(w, "black", color),
                    (x - int(w.width / 2), y - int(w.height / 2)),
                    w,
                )
