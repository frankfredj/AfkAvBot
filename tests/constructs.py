from pathlib import Path

from PIL import Image

from avbot.lib.screen import WoWcoordinates, Monitor, WoWclient
from avbot.lib.utils import Location, BBox


def build_wow_client_from_monitor_image(monitor_image_path: Path):
    wow_coordinates = WoWcoordinates(
        bbox=BBox(-2560, 0, 2560, 1440), location=Location(-2560, 0, 0, 1440), open=True
    )

    monitor = Monitor(
        name=r"\\\\.\\DISPLAY1",
        number=2,
        bbox=BBox(-2560, 0, 2560, 1440),
        location=Location(-2560, 0, 0, 1440),
        image=Image.open(monitor_image_path),
    )

    wow_client = WoWclient(
        wow_coordinates=wow_coordinates,
        monitor=monitor,
        monitor_relative_location=Location(0, 0, 2560, 1440),
        image=monitor.image,
    )
    wow_client.load_movements()
    wow_client.load_sub_images()

    return wow_client
