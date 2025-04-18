import math
import time
import keyboard
import inspect
import sys
from collections import namedtuple
from typing import Tuple, List, Dict, Optional, Callable
from random import randint, uniform

import pyautogui
import numpy as np

# Define the namedtuples once at module level
Location = namedtuple("Location", ["left", "top", "right", "bottom"])
BBox = namedtuple("BBox", ["left", "top", "width", "height"])


def convert_bbox_to_location(bbox: BBox) -> Location:
    """Convert a bounding box to location coordinates.

    Args:
        bbox (BBox): Bounding box with left, top, width, height

    Returns:
        Location: Location with left, top, right, bottom
    """
    return Location(bbox.left, bbox.top, bbox.left + bbox.width, bbox.top + bbox.height)


def convert_location_to_bbox(location: Location) -> BBox:
    """Convert location coordinates to a bounding box.

    Args:
        location (Location): Location with left, top, right, bottom

    Returns:
        BBox: Bounding box with left, top, width, height
    """
    return BBox(
        location.left,
        location.top,
        location.right - location.left,
        location.bottom - location.top,
    )


def get_monitor_bbox(monitor: namedtuple) -> BBox:
    return BBox(
        monitor.x,
        monitor.y,
        monitor.width,
        monitor.height,
    )


def get_mss_monitor_bbox(mss_monitors: dict) -> BBox:
    return BBox(
        mss_monitors["left"],
        mss_monitors["top"],
        mss_monitors["width"],
        mss_monitors["height"],
    )


def is_subbox(bbox: BBox, sub_bbox: BBox) -> bool:
    """Checks if sub_bbox is inside bbox

    Args:
        bbox (BBox): the outer bbox
        sub_bbox (BBox): the inner bbox

    Return:
        (bool) True or False
    """
    return (
        bbox.left <= sub_bbox.left
        and bbox.top <= sub_bbox.top
        and bbox.width >= sub_bbox.width
        and bbox.height >= sub_bbox.height
    )


def get_relative_location(bbox: BBox, sub_bbox: BBox) -> Location:
    """Gets the sub_bbox relative location with respect to bbox

    Args:
        bbox (BBox): the outer bbox
        sub_bbox (BBox): the inner bbox

    Return:
        (BBox) The relative location
    """
    if not is_subbox(bbox, sub_bbox):
        raise ValueError(f"{sub_bbox} is not a sub-bbox of {bbox}")

    return Location(
        sub_bbox.left - bbox.left,
        sub_bbox.top - bbox.top,
        sub_bbox.left - bbox.left + sub_bbox.width,
        sub_bbox.top - bbox.top + sub_bbox.height,
    )


def get_absolute_location(
    screen_location: Location, image_location: Location
) -> Location:
    """Combines two locations

    Args:
        screen_location (Location): the screen location
        image_location (Location): the image location

    Return:
        (BBox) The relative location
    """
    return Location(
        screen_location.left + image_location.left,
        screen_location.top + image_location.top,
        screen_location.left + image_location.right,
        screen_location.top + image_location.bottom,
    )


def get_bbox_center(bbox: BBox) -> Tuple[int, int]:
    """Returns the coordinates of the center"""
    return round(bbox.left + bbox.width // 2), round(bbox.top + bbox.height // 2)


def move_mouse(x, y):
    """Moves the mouse without being too obvious about the botting"""
    current_x, current_y = pyautogui.position().x, pyautogui.position().y
    distance = math.sqrt((x - current_x) ** 2 + (y - current_y) ** 2)
    noise_factor = math.ceil(0.01 * distance)

    n_points = randint(5, 10)
    points_x = np.linspace(start=current_x, stop=x, num=n_points)[1:]
    points_y = np.linspace(start=current_y, stop=y, num=n_points)[1:]

    # Add noise
    points_x[:-1] += np.random.normal(loc=0, scale=noise_factor, size=n_points - 2)
    points_y[:-1] += np.random.normal(loc=0, scale=noise_factor, size=n_points - 2)

    duration = round(uniform(0.1, 0.2) / (n_points - 1), 10)
    for point_x, point_y in zip(points_x, points_y):
        pyautogui.moveTo(point_x, point_y, duration=duration)


def move_mouse_to_bbox(bbox: BBox, click: bool = True):
    x, y = get_bbox_center(bbox)
    move_mouse(x, y)
    if click:
        pyautogui.click()


def parse_keystrokes(keystrokes: List[dict]) -> List[dict]:
    press = [
        {"time": stroke["start_time"], "action": "press", "key": stroke["key"]}
        for stroke in keystrokes
    ]
    release = [
        {"time": stroke["end_time"], "action": "release", "key": stroke["key"]}
        for stroke in keystrokes
    ]
    actions = sorted(press + release, key=lambda x: x["time"])

    start_time = actions[0]["time"]
    for action in actions:
        action["time"] -= start_time

    return actions


def perform_keystrokes(parsed_keystrokes: Optional[List[dict]]) -> bool:
    """
    Performs a sequence of keystrokes as defined in the parsed keystrokes list.

    Args:
        parsed_keystrokes (List[dict]): List of keystroke actions with time, action, and key

    Returns:
        bool: True if completed successfully, False otherwise
    """
    if not parsed_keystrokes:
        return False

    # Keep track of which keys are currently pressed to ensure release on error
    pressed_keys = set()

    try:
        for i, keystroke in enumerate(parsed_keystrokes[:-1]):
            # Perform the action
            if keystroke["action"] == "press":
                pyautogui.keyDown(keystroke["key"])
                pressed_keys.add(keystroke["key"])
            elif keystroke["action"] == "release":
                pyautogui.keyUp(keystroke["key"])
                pressed_keys.discard(
                    keystroke["key"]
                )  # Use discard instead of remove to avoid errors

            waiting_time = parsed_keystrokes[i + 1]["time"] - keystroke["time"]
            time.sleep(waiting_time)

        # Handle the last keystroke
        keystroke = parsed_keystrokes[-1]
        if keystroke["action"] == "press":
            pyautogui.keyDown(keystroke["key"])
            pressed_keys.add(keystroke["key"])
        elif keystroke["action"] == "release":
            pyautogui.keyUp(keystroke["key"])
            pressed_keys.discard(keystroke["key"])

        return True

    except Exception as e:
        print(f"Error during keystroke sequence: {e}")
        # Release all keys that are still pressed to prevent them being stuck
        for key in pressed_keys:
            try:
                pyautogui.keyUp(key)
                print(f"Released key {key} after error")
            except Exception as release_error:
                print(f"Failed to release key {key}: {release_error}")
        return False


def key_up_all(keys: List[str]):
    for key in keys:
        if keyboard.is_pressed(key):
            pyautogui.keyUp(key)


def clear_keys():
    """Call this function from within any function to clear all keys ending with '_key'"""
    # Get the frame of the calling function
    frame = sys._getframe(1)  # 1 = previous stack frame (the calling function)

    # Get the local variables of the calling function
    locals_dict = frame.f_locals

    # Extract values for parameters ending with '_key'
    key_values = [value for name, value in locals_dict.items() if name.endswith("_key")]
    for key in key_values:
        pyautogui.keyUp(key)

    # Clear the keys
    key_up_all(key_values)
