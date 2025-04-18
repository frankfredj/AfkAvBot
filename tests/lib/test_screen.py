import time

from pathlib import Path
from collections import namedtuple

from avbot.lib.screen import WoWcoordinates, WoWclient
from avbot.lib.battlegrounds import queue_and_enter_av, walk_out_and_mount, move_like_an_idiot, afk_bg
from avbot.lib.utils import move_mouse_to_bbox

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_TEST_OUTPUTS = PROJECT_ROOT / "tests" / "outputs"

BBox = namedtuple("BBox", ["left", "top", "width", "height"])


def test_wow_coordinates():
    """Tests the WoWlocation class"""
    wow_coordinates = WoWcoordinates()
    wow_coordinates.update_coordinates()

    assert isinstance(wow_coordinates.bbox, tuple)
    assert isinstance(wow_coordinates.location, tuple)


def test_wow_client():
    """
    Tests the Picture class
    Requires WoW open on a 24inches 2k monitor with AH open
    """
    # Screenshots of the monitor and WoW client
    wow_client = WoWclient()
    wow_client.find_screen()
    wow_client.update_client_image()
    wow_client.monitor.image.save(PROJECT_TEST_OUTPUTS / "monitor_screenshot.png")


def test_av_queue():
    """
    Tries to queue for AV
    """
    wow_client = WoWclient()
    wow_client.find_screen()
    wow_client.update_client_image()

    wow_client.load_sub_images()
    wow_client.load_keystrokes()

    queue_and_enter_av(wow_client)
    time.sleep(2 * 60)
    walk_out_and_mount(wow_client)


def test_move_like_an_idiot():
    wow_client = WoWclient()
    wow_client.find_screen()
    wow_client.update_client_image()

    wow_client.load_sub_images()

    wow_client.focus_client()
    for i in range(100):
        move_like_an_idiot(wow_client)


def test_afk_av():
    """
    AFKs 40 battlegrounds
    """
    wow_client = WoWclient()
    wow_client.find_screen()
    wow_client.update_client_image()

    wow_client.load_sub_images()
    wow_client.load_keystrokes()

    afk_bg(wow_client)


def test_locate_red_boxes():
    wow_client = WoWclient()
    wow_client.find_screen()
    wow_client.update_client_image()

    wow_client.load_sub_images()

    leave_battleground = wow_client.get_sub_image("leave_battleground")
    cancel_res = wow_client.get_sub_image("cancel_res")

    leave_battleground.update_location(wow_client)
    cancel_res.update_location(wow_client)
