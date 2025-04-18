import time
import random
import pyautogui
from avbot.lib.screen import WoWclient

from avbot.lib.movements import move_until_death, mount_up, move_randomly_in_bg
from avbot.lib.utils import (
    move_mouse_to_bbox,
    clear_keys,
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
    clear_keys()
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


def walk_out_and_mount(
    client: WoWclient,
    move_forward_key="w",
    turn_left_key: str = "[",
    turn_right_key: str = "]",
    threshold: float = 0.75,
    grayscale: bool = True,
    mount_key: str = "t",
) -> bool:
    """
    Walks to the AFK spot in Alterac Valley battleground by replaying recorded keystrokes

    Args:
        client (WoWclient): The WoW client instance
        move_forward_key (str): Key to move forward
        turn_left_key (str): Key to turn left
        turn_right_key (str): Key to turn right
        threshold (float): image detection severity
        grayscale (float): image detection parameter
        mount_key (str): keybind to mount up

    Returns:
        bool: True if successfully walked to the AFK spot, False otherwise
    """
    clear_keys()
    client.focus_client()
    movements = client.movements.get("move_out_of_cave")

    if not movements:
        return False

    move_until_death(
        client,
        movements,
        move_forward_key,
        turn_left_key,
        turn_right_key,
        threshold,
        grayscale,
    )
    mount_up(client, mount_key)
    return True


def afk_bg(
    client: WoWclient,
    n: int = 30,
    target_name: str = "Thelman Slatefist",
    interact_with_target_key: str = "/",
    mount_key: str = "t",
    move_forward_key="w",
    turn_left_key: str = "[",
    turn_right_key: str = "]",
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
        move_forward_key (str): Key to move forward
        turn_left_key (str): Key to turn left
        turn_right_key (str): Key to turn right
        threshold (float): The matching threshold for image recognition
        grayscale (bool): Whether to use grayscale for image recognition
        max_wait_time (int): Max wait time in seconds for a queue
    """
    client.focus_client()
    clear_keys()
    # Use batches of 10 movements
    n_movements = 10

    was_dead = False
    leave_battleground = client.get_sub_image("leave_battleground")
    cancel_res = client.get_sub_image("cancel_res")

    def update_status():
        leave_battleground.update_location(client, threshold, grayscale)
        cancel_res.update_location(client, threshold, grayscale)

    def is_dead():
        update_status()
        return cancel_res.found and not leave_battleground.found

    def bg_is_over():
        update_status()
        return not cancel_res.found and leave_battleground.found

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
            time.sleep(random.uniform(115, 120))
            move_until_death(
                client,
                client.movements.get("move_out_of_cave"),
                move_forward_key,
                turn_left_key,
                turn_right_key,
                threshold,
                grayscale,
            )
            mount_up(client, mount_key, threshold=0.75)

            # Routine to walk to initial spot
            move_until_death(
                client,
                client.movements.get("move_to_harpies"),
                move_forward_key,
                turn_left_key,
                turn_right_key,
                threshold,
                grayscale,
            )

            while True:
                # Move randomly
                if not is_dead():
                    if not was_dead:
                        # Mount up if not already mounted, then move randomly
                        mount_up(client, mount_key, threshold, grayscale)
                        move_randomly_in_bg(
                            client,
                            n_movements,
                            move_forward_key,
                            turn_left_key,
                            turn_right_key,
                            threshold,
                            grayscale,
                        )
                    else:
                        # Move 100 units away from the graveyard in a straight line after being resurrected
                        move_until_death(
                            client,
                            [{"units": 100, "rotation": 0.0}],
                            move_forward_key,
                            turn_left_key,
                            turn_right_key,
                            threshold,
                            grayscale,
                        )
                        was_dead = False
                else:
                    clear_keys()

                if bg_is_over():
                    break

                elif is_dead():
                    clear_keys()
                    was_dead = True
                    time.sleep(5)

            clear_keys()
            print("Info: AV battle is over. Leaving battleground...")
            move_mouse_to_bbox(leave_battleground.absolute_bbox)
            print(f"Complete battleground #{i + 1}. Good work!")
            time.sleep(random.uniform(10, 15))

    except BaseException as e:
        print(e)
        return False

    return True
