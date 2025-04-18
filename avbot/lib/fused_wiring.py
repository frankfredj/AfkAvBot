import time
import random
import pyautogui
import keyboard
from avbot.lib.screen import WoWclient, reload_client

from avbot.lib.utils import (
    convert_bbox_to_location,
    convert_location_to_bbox,
    get_monitor_bbox,
    get_bbox_center,
    get_mss_monitor_bbox,
    is_subbox,
    get_relative_location,
    get_absolute_location,
    Location,
    move_mouse,
    move_mouse_to_bbox,
    BBox,
    parse_keystrokes,
    perform_keystrokes,
)
from avbot.lib.exceptions import (
    WoWnotFoundException,
    MonitorNotFoundException,
    ImageNotFoundException,
)


def spawn_then_loot_target_dummy(
    client: WoWclient,
    target_dummy_key: str = "3",
) -> bool:
    """
    Spawn then loots a target dummy

    Args:
        client (WoWclient): The WoW client instance
        target_dummy_key (str): The target dummy keybind
    """
    try:
        # Locate the center of the client screen
        x, y = get_bbox_center(client.monitor.bbox)

        client.focus_client()
        client.reload_client(threshold=0.7)

        # Spawn the dummy
        move_mouse(x, y)
        time.sleep(random.uniform(0.1, 0.15))
        pyautogui.keyDown(target_dummy_key)
        time.sleep(random.uniform(0.1, 0.15))
        pyautogui.keyUp(target_dummy_key)
        time.sleep(random.uniform(0.1, 0.15))
        pyautogui.click()

        # Wait then loot
        time.sleep(random.uniform(18, 20))
        pyautogui.rightClick()

        return True

    except BaseException as e:
        print(e)
        return False


def farm_fused_wiring(
    client: WoWclient, target_dummy_key: str = "3", n: int = 30
) -> bool:
    """
    Spawn then loots a target dummies

    Args:
        client (WoWclient): The WoW client instance
        target_dummy_key (str): The target dummy keybind
        n (int): number of target dummies to be spawned and looted
    """
    for i in range(n):
        if not spawn_then_loot_target_dummy(client, target_dummy_key):
            return False
        # Wait for the post-loot dummy cooldown
        time.sleep(random.uniform(100, 102))

    print(f"Done looting {n} target dummies. Such hard work.")
    return True
