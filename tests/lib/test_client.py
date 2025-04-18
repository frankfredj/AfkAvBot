from pathlib import Path
from collections import namedtuple

from avbot.lib.screen import WoWcoordinates, WoWclient

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_TEST_OUTPUTS = PROJECT_ROOT / "tests" / "outputs"

BBox = namedtuple("BBox", ["left", "top", "width", "height"])


def test_wow_coordinates():
    """Tests the WoWlocation class
    Requires WoW open on a 24inches 2k monitor
    """
    wow_coordinates = WoWcoordinates()
    wow_coordinates.update_coordinates()

    assert isinstance(wow_coordinates.bbox, tuple)
    assert isinstance(wow_coordinates.location, tuple)


def test_wow_client():
    """
    Tests the Picture class
    Requires WoW open on a 24inches 2k monitor
    """
    # Screenshots of the monitor and WoW client
    wow_client = WoWclient()
    wow_client.find_screen()
    wow_client.update_client_image()
    wow_client.monitor.image.save(PROJECT_TEST_OUTPUTS / "monitor_screenshot.png")
