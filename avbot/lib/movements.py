import time
import copy
import threading
import random
import pyautogui
from typing import Optional, List, Dict, Union, Tuple

import numpy as np

from avbot.lib.screen import WoWclient
from avbot.lib.utils import key_up_all, clear_keys
from avbot.lib.exceptions import MovementsNotFoundException
from avbot.constants import (
    TURN_360,
    TURN_90_FACTOR,
    TURN_180_FACTOR,
    TURN_270_FACTOR,
    W_SPEED,
    TURN_90_MOVING_FACTOR,
    TURN_180_MOVING_FACTOR,
    TURN_270_MOVING_FACTOR,
    TURN_360_MOVING_FACTOR,
)


y_known_idle = np.array([0.0, TURN_90_FACTOR, TURN_180_FACTOR, TURN_270_FACTOR, 1.0])
y_known_moving = np.array(
    [
        1.0,
        TURN_90_MOVING_FACTOR,
        TURN_180_MOVING_FACTOR,
        TURN_270_MOVING_FACTOR,
        TURN_360_MOVING_FACTOR,
    ]
)

x_known = np.array([0.0, 0.25, 0.5, 0.75, 1.0])


def rotate(factor: float, turn_left_key: str = "[", turn_right_key: str = "]"):
    """
    Rotates the character

    Args:

    """
    clear_keys()

    key = turn_left_key if factor < 0 else turn_right_key
    factor = abs(factor) % 1 if factor != 1 else factor
    adjustment = np.interp(factor, x_known, y_known_idle)

    pyautogui.keyDown(key)
    time.sleep(factor * adjustment * TURN_360)
    pyautogui.keyUp(key)


def move_forward(units: float, move_forward_key="w"):
    """
    Move forward.

    Args:
        units (float): Distance to move forward (in time units)
        move_forward_key (str): Key to move forward
    """
    clear_keys()
    pyautogui.keyDown(move_forward_key)
    time.sleep(units / W_SPEED)
    pyautogui.keyUp(move_forward_key)


def adjust_units(
    movements: List[Dict[str, float]], mounted: bool = False
) -> List[Dict[str, float]]:
    """Adjust units for mount speed"""
    if not mounted:
        return copy.deepcopy(movements)

    output = copy.deepcopy(movements)
    for movement in output:
        movement["units"] = movement["units"] / 2

    return output


def add_extra_stats_to_movements(movements: List[Dict[str, float]]):
    """Add extra statistics in place"""
    # Add the rotation coefficient and the target execution time
    for movement in movements:
        if movement["units"]:
            movement["rotation_coefficient"] = np.interp(
                movement["rotation"], x_known, y_known_idle
            )
        else:
            movement["rotation_coefficient"] = np.interp(
                movement["rotation"], x_known, y_known_moving
            )

        rotation = movement["rotation"]
        rotation_factor = abs(rotation) % 1 if rotation != 1 else rotation
        adjustment = np.interp(rotation_factor, x_known, y_known_moving)

        movement["rotation_time"] = rotation_factor * adjustment * TURN_360
        movement["forward_time"] = movement["units"] / W_SPEED
        movement["execution_time"] = max(
            movement["rotation_time"], movement["forward_time"]
        )


def preprocess_movements(movements: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Process a crude movements list"""
    add_extra_stats_to_movements(movements)

    # Create an equivalent movement path, but with intervals where the exec time
    # is at most 1 second for straight lines.
    output = []
    for movement in movements:
        # Small movements or very long turns are ok
        if (
            movement["execution_time"] <= 1
            or movement["rotation_time"] >= movement["forward_time"]
        ):
            output.append(copy.deepcopy(movement))
            continue

        split_movement = []
        # Add rotation
        if movement["rotation"]:
            units_moved_during_rotation = (
                movement["rotation_time"] / movement["execution_time"]
            ) * movement["units"]
            units_moved_after_rotation = movement["units"] - units_moved_during_rotation
            split_movement.append(
                {"units": units_moved_during_rotation, "rotation": movement["rotation"]}
            )
        else:
            units_moved_after_rotation = movement["units"]

        if units_moved_after_rotation:
            n_movements = units_moved_after_rotation / W_SPEED
            units = [W_SPEED for _ in range(int(n_movements))]
            remainder = n_movements % 1
            units.append(remainder * W_SPEED)
            split_movement += [{"units": unit, "rotation": 0} for unit in units]

        add_extra_stats_to_movements(split_movement)
        output += copy.deepcopy(split_movement)

    return output


def moves(
    movements: Union[List[Dict[str, float]], str],
    move_forward_key="w",
    turn_left_key: str = "[",
    turn_right_key: str = "]",
    stop_event: Optional[threading.Event] = None,
    mounted: bool = False,
) -> bool:
    """
    Move forward while rotating simultaneously.

    Args:
        movements (Union[List[Dict[str, float]], str]): the list of movements to perform
        move_forward_key (str): Key to move forward
        turn_left_key (str): Key to turn left
        turn_right_key (str): Key to turn right
        stop_event (Optional[threading.Event]): Death or bg end threading event
        mounted (bool): if we are mounted
    """
    clear_keys()
    move_forward_key_down = False
    processed_movements = preprocess_movements(adjust_units(movements, mounted))
    for movement in processed_movements:
        if stop_event and stop_event.is_set():
            print("Movement interrupted by stop event")
            clear_keys()
            return False

        turn_key = turn_left_key if movement["rotation"] < 0 else turn_right_key

        if not move_forward_key_down and movement["units"]:
            pyautogui.keyDown(move_forward_key)
            move_forward_key_down = True

        elif move_forward_key_down and not movement["units"]:
            pyautogui.keyUp(move_forward_key)

        if movement["rotation_time"] > movement["forward_time"]:
            # Start turn
            pyautogui.keyDown(turn_key)
            time.sleep(movement["forward_time"])
            # Stop moving forward while turning
            pyautogui.keyUp(move_forward_key)
            move_forward_key_down = False
            # Finish turn
            time.sleep(movement["execution_time"] - movement["forward_time"])
            pyautogui.keyUp(turn_key)

        elif movement["rotation_time"]:
            # Turn
            pyautogui.keyDown(turn_key)
            time.sleep(movement["rotation_time"])
            pyautogui.keyUp(turn_key)
            # Keep moving
            time.sleep(movement["execution_time"] - movement["rotation_time"])

        else:
            # Keep moving
            time.sleep(movement["execution_time"])

    clear_keys()
    return True


def move_until_death(
    client: WoWclient,
    movements: Union[List[Dict[str, float]], str],
    move_forward_key="w",
    turn_left_key: str = "[",
    turn_right_key: str = "]",
    threshold=0.9,
    grayscale=True,
    update_image: bool = True,
    early_check: bool = True,
) -> bool:
    """
    Move but stop when dead.

    Args:
        client (WoWclient): Wow client
        movements (Union[List[Dict[str, float]], str]): the list of movements to perform
        move_forward_key (str): Key to move forward
        turn_left_key (str): Key to turn left
        turn_right_key (str): Key to turn right
        threshold (float): image detection severity
        grayscale (float): image detection parameter
        update_image (bool): update client image
        early_check (bool): check if dead or bg over off the bat
    """
    # Load sub-images
    clear_keys()
    resurrection_sub_image = client.get_sub_image("resurrection")
    leave_battleground_sub_image = client.get_sub_image("leave_battleground")

    def update_stopping_conditions():
        resurrection_sub_image.update_location(
            client, threshold, grayscale, update_image
        )
        leave_battleground_sub_image.update_location(
            client, threshold, grayscale, update_image
        )

    def should_stop():
        update_stopping_conditions()
        return resurrection_sub_image.found or leave_battleground_sub_image.found

    if early_check and should_stop():
        return False

    # Flag to signal when to stop movement
    stop_event = threading.Event()

    # Thread function to check for resurrection image
    def check_for_death():
        while not stop_event.is_set():
            if should_stop():
                stop_event.set()
                break
            time.sleep(0.25)

    # Start the death check thread
    death_check_thread = threading.Thread(target=check_for_death)
    death_check_thread.daemon = True  # Make thread exit when main thread exits
    death_check_thread.start()

    # Start movement using existing move() function with stop_event
    movement_completed = moves(
        movements, move_forward_key, turn_left_key, turn_right_key, stop_event
    )

    # Movement is complete or was interrupted, stop the death check
    stop_event.set()
    death_check_thread.join(timeout=1.0)

    # Return True if the movements were executed
    clear_keys()
    return movement_completed


def generate_random_movements(
    n: int,
    units_uniform_params: Optional[Tuple[float, float]] = None,
    rotation_gaussian_params: Optional[Tuple[float, float]] = None,
) -> List[Dict[str, float]]:
    """
    Generates a random vector of movements.

    Args:
        n (int): the number of movements to be performed
        units_uniform_params (tuple): uniform distribution parameters for units
        rotation_gaussian_params (tuple): gaussian distribution parameters for rotation
    """
    a, b = units_uniform_params if units_uniform_params else 5, 40
    mu, sigma = rotation_gaussian_params if rotation_gaussian_params else 0.0, 0.2
    return [
        {"units": random.uniform(a, b), "rotation": random.gauss(mu, sigma)}
        for _ in range(n)
    ]


def move_randomly_in_bg(
    client: WoWclient,
    n_movements: int = 15,
    move_forward_key="w",
    turn_left_key: str = "[",
    turn_right_key: str = "]",
    threshold=0.9,
    grayscale=True,
    update_image: bool = True,
    units_uniform_params: Optional[Tuple[float, float]] = None,
    rotation_gaussian_params: Optional[Tuple[float, float]] = None,
) -> bool:
    """
    Move but stop when dead.

    Args:
        client (WoWclient): Wow client
        n_movements (int): the number of movements to be performed
        move_forward_key (str): Key to move forward
        turn_left_key (str): Key to turn left
        turn_right_key (str): Key to turn right
        threshold (float): image detection severity
        grayscale (float): image detection parameter
        update_image (bool): update client image
        units_uniform_params (tuple): uniform distribution parameters for units
        rotation_gaussian_params (tuple): gaussian distribution parameters for rotation
    """
    movements = generate_random_movements(
        n_movements, units_uniform_params, rotation_gaussian_params
    )
    return move_until_death(
        client,
        movements,
        move_forward_key,
        turn_left_key,
        turn_right_key,
        threshold,
        grayscale,
        update_image,
    )


def mount_up(
    client: WoWclient,
    mount_key: str = "t",
    threshold=0.9,
    grayscale=True,
    update_image: bool = True,
) -> bool:
    """
    Mount up if possible.

    Args:
        client (WoWclient): Wow client
        mount_key (str): Mount key
        threshold (float): image detection severity
        grayscale (float): image detection parameter
        update_image (bool): update client image
    """
    mount_subimage = client.get_sub_image("mount_icon")
    mount_subimage.update_location(client, threshold, grayscale, update_image)

    if not mount_subimage.found:
        key_up_all([mount_key])
        pyautogui.keyDown(mount_key)
        time.sleep(random.uniform(0.1, 0.2))
        pyautogui.keyUp(mount_key)
        time.sleep(random.uniform(3.0, 3.2))
        mount_subimage.update_location(client, threshold, grayscale, update_image)

    return mount_subimage.found
