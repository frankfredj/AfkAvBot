import time
import random
import pyautogui
import keyboard
from avbot.lib.screen import WoWclient

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


def queue_and_enter_av(
    client: WoWclient,
    target_name: str = "Thelman Slatefist",
    interact_with_target_key: str = "/",
    threshold: float = 0.75,
    grayscale: bool = True,
    max_wait_time: int = 400,
) -> bool:
    """
    Queue for Alterac Valley battleground and enter it by targeting and interacting with an NPC

    Args:
        client (WoWclient): The WoW client instance
        target_name (str): The name of the NPC to target
        interact_with_target_key (str): The key to press to interact with the target, default "/"
        threshold (float): The matching threshold for image recognition
        grayscale (bool): Whether to use grayscale for image recognition
        max_wait_time (int): Max wait time in seconds for a queue
    """
    # First, focus the WoW window
    client.focus_client()
    client.reload_client()

    # Now proceed with the rest of the function
    chat_typing_box = client.get_sub_image("chat_typing_box")
    chat_typing_box.update_location(client, threshold, grayscale)
    if chat_typing_box.found:
        # Click on the chat typing box
        move_mouse_to_bbox(chat_typing_box.absolute_bbox)

        # Select all existing text and delete it
        pyautogui.keyDown("ctrl")
        pyautogui.press("a")
        pyautogui.keyUp("ctrl")
        pyautogui.press("delete")

        # Type the target command
        pyautogui.write(f"/tar {target_name}")
        pyautogui.press("enter")

        # Update the chat typing box location - it should be gone
        chat_typing_box.update_location(client, threshold, grayscale)
        if chat_typing_box.found:
            print("Warning: Chat typing box still visible after targeting")
    else:
        # Press enter to open chat
        pyautogui.press("enter")
        time.sleep(0.5)  # Brief delay to ensure the chat opens

        # Verify that the chat typing box is now visible
        chat_typing_box.update_location(client, threshold, grayscale)
        if not chat_typing_box.found:
            print("Error: Chat typing box not found after pressing enter")
            return False

        # Click on the chat typing box
        move_mouse_to_bbox(chat_typing_box.absolute_bbox)
        time.sleep(0.5)

        # Type the target command
        pyautogui.write(f"/tar {target_name}")
        pyautogui.press("enter")

        # Update the chat typing box location - it should be gone
        chat_typing_box.update_location(client, threshold, grayscale)
        if chat_typing_box.found:
            print("Warning: Chat typing box still visible after targeting")

    # Wait for the targeting to complete
    time.sleep(0.5)

    # Interact with the target using the specified key
    pyautogui.press(interact_with_target_key)
    time.sleep(0.5)

    # Check for battleground queue confirmation
    queue_for_battleground = client.get_sub_image("queue_for_battleground")
    queue_for_battleground.update_location(client, threshold, grayscale)
    if queue_for_battleground.found:
        move_mouse_to_bbox(queue_for_battleground.absolute_bbox)
        print("Successfully opened dialog box")
        time.sleep(0.5)
    else:
        print("Warning: Dialog box not found")
        return False

    join_battle = client.get_sub_image("join_battle")
    join_battle.update_location(client, threshold, grayscale)
    if join_battle.found:
        move_mouse_to_bbox(join_battle.absolute_bbox)
        print("Successfully queued for battleground")
        time.sleep(0.5)
    else:
        print("Warning: Queue confirmation dialog not found")
        return False

    enter_battle = client.get_sub_image("enter_battle")
    enter_battle.update_location(client, threshold, grayscale)

    # Check for "enter battle" button and click it when it appears
    print(f"Waiting up to {max_wait_time} seconds for the battleground to pop...")
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        enter_battle.update_location(client, threshold, grayscale)
        if enter_battle.found:
            move_mouse_to_bbox(enter_battle.absolute_bbox)
            print("Entering battleground")
            return True
        time.sleep(2)

    print("Timed out waiting for enter battle prompt")
    return False


def walk_out_and_mount(client: WoWclient, i: int = 0, mount_key: str = "t") -> bool:
    """
    Walks to the AFK spot in Alterac Valley battleground by replaying recorded keystrokes

    Args:
        client (WoWclient): The WoW client instance
        i (int): start index
        mount_key (str): keybind to mount up

    Returns:
        bool: True if successfully walked to the AFK spot, False otherwise
    """
    client.focus_client()
    moves = client.keystrokes.get("move_out_and_mount")
    for move in moves:
        move["key"] = mount_key if move["key"] == "t" else move["key"]

    if not moves:
        return False

    perform_keystrokes(moves[i:])
    return True


def move_like_an_idiot(client: WoWclient) -> bool:
    """
    Names says it all.

    Args:
        client (WoWclient): The WoW client instance

    Returns:
        (bool): True if the move was performed

    """
    client.focus_client()
    cancel_res = client.get_sub_image("cancel_res")

    move_duration = random.uniform(5, 15)
    keys = ["w", "a", "d", "s"]
    for key in keys:
        pyautogui.keyUp(key)

    n_moves = int(random.uniform(5, 10))
    delta_t = move_duration / n_moves
    for i in range(n_moves):
        pyautogui.keyDown("w")

        key = None
        if random.randint(0, 1):
            key = "a" if random.randint(0, 1) else "d"
            pyautogui.keyDown("w")

        if key:
            pyautogui.keyDown(key)
            time.sleep(delta_t / 4)
            pyautogui.keyUp(key)
            time.sleep(3 * delta_t / 4)
        else:
            time.sleep(delta_t)

        cancel_res.update_location(client)
        if cancel_res.found:
            pyautogui.keyUp("w")
            return False

    pyautogui.keyUp("w")
    stop_moving()
    return True


def stop_moving():
    for key in ["a", "s", "d", "w"]:
        if keyboard.is_pressed(key):
            pyautogui.keyUp(key)


def afk_bg(
    client: WoWclient,
    n: int = 30,
    target_name: str = "Thelman Slatefist",
    interact_with_target_key: str = "/",
    mount_key: str = "t",
    threshold: float = 0.75,
    grayscale: bool = True,
    max_wait_time: int = 400,
) -> bool:
    """
    Queue for Alterac Valley battleground and enter it by targeting and interacting with an NPC

    Args:
        client (WoWclient): The WoW client instance
        n (int): number of games
        target_name (str): The name of the NPC to target
        interact_with_target_key (str): The key to press to interact with the target, default "/"
        mount_key (str): keybind to mount up, default "t"
        threshold (float): The matching threshold for image recognition
        grayscale (bool): Whether to use grayscale for image recognition
        max_wait_time (int): Max wait time in seconds for a queue
    """
    try:
        for i in range(n):
            queue_and_enter_av(
                client,
                target_name,
                interact_with_target_key,
                threshold,
                grayscale,
                max_wait_time,
            )
            time.sleep(2 * 60)
            walk_out_and_mount(client, mount_key=mount_key)

            leave_battleground = client.get_sub_image("leave_battleground")
            cancel_res = client.get_sub_image("cancel_res")

            while True:
                # Move randomly
                is_alive = move_like_an_idiot(client)
                # If the function returns False, then we died mid-move
                if not is_alive:
                    print("Info: character died. Waiting to be resurrected...")
                    stop_moving()
                    # Check if we can cancel our res for 61 seconds.
                    # If we can't, then we have been resurrected or the game is over
                    for k in range(61):
                        time.sleep(1)
                        cancel_res.update_location(client)
                        if not cancel_res.found():
                            # Mount up after being resurrected
                            print("Info: character was resurrected. Mounting up...")
                            pyautogui.keyDown("t")
                            time.sleep(0.5)
                            pyautogui.keyUp("t")
                            time.sleep(2)
                            break

                # Check if the game is over
                cancel_res.update_location(client)
                leave_battleground.update_location(client)

                if not cancel_res.found and leave_battleground.found:
                    break

            print("Info: AV battle is over. Leaving battleground...")
            stop_moving()
            move_mouse_to_bbox(leave_battleground.absolute_bbox)
            print(f"Complete battleground #{i + 1}. Good work!")
            time.sleep(20)

    except BaseException as e:
        print(e)
        return False

    return True
