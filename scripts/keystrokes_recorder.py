from pynput import keyboard
import json
import time

# Dictionary to track key state
key_state = {
    'a': {'pressed': False, 'start_time': None},
    'w': {'pressed': False, 'start_time': None},
    's': {'pressed': False, 'start_time': None},
    'd': {'pressed': False, 'start_time': None},
    't': {'pressed': False, 'start_time': None}
}

# List to store completed key press events
key_events = []

# Get starting time of the script
start_time = time.time()


def on_press(key):
    try:
        key_char = key.char
        # Only track a, w, s, d keys
        if key_char in key_state and not key_state[key_char]['pressed']:
            # Mark key as pressed and record start time
            key_state[key_char]['pressed'] = True
            key_state[key_char]['start_time'] = time.time() - start_time
            print(f"Key {key_char} pressed at {key_state[key_char]['start_time']:.2f}s")
    except AttributeError:
        # Handle special keys
        pass


def on_release(key):
    try:
        key_char = key.char
        # Only track a, w, s, d keys
        if key_char in key_state and key_state[key_char]['pressed']:
            # Mark key as released and calculate duration
            release_time = time.time() - start_time
            event = {
                'key': key_char,
                'start_time': key_state[key_char]['start_time'],
                'end_time': release_time,
                'duration': release_time - key_state[key_char]['start_time']
            }
            key_events.append(event)
            key_state[key_char]['pressed'] = False
            print(f"Key {key_char} released at {release_time:.2f}s, duration: {event['duration']:.2f}s")
    except AttributeError:
        # Handle special keys
        pass

    # Stop listener and save data when escape key is pressed
    if key == keyboard.Key.esc:
        # Save the recorded events to a JSON file
        with open('keystroke_data.json', 'w') as f:
            json.dump(key_events, f, indent=4)
        print("Keystrokes saved to keystroke_data.json")
        return False


# Set up and start the listener
print("Recording keystrokes (a, w, s, d). Press ESC to stop and save.")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
