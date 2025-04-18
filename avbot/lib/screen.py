import time
import pyautogui
import cv2
import numpy as np
import psutil
import json
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Union
from PIL import Image
from screeninfo import get_monitors, Monitor
from mss import mss
from datetime import datetime
import pygetwindow as gw
from collections import namedtuple
from pathlib import Path

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
    BBox,
)
from avbot.lib.exceptions import (
    WoWnotFoundException,
    MonitorNotFoundException,
    ImageNotFoundException,
)


@dataclass
class WoWcoordinates:
    """Represents the coordinates of a WoW client"""

    process_name: str = "WowClassic.exe"
    process_title: str = "World of Warcraft"
    bbox: Optional[namedtuple] = None
    location: Optional[namedtuple] = None
    open: Optional[bool] = False

    def __repr__(self):
        return f"Process Name: {self.process_name}\nLocation: {self.location}"

    def __eq__(self, other):
        return (
            self.process_name == other.process_name
            and self.process_title == other.process_title
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.process_name)

    def update_status(self):
        self.open = any(
            process.name() == self.process_name for process in psutil.process_iter()
        )

    def update_coordinates(self):
        self.update_status()
        if not self.open:
            raise WoWnotFoundException(f"{self.process_name}  is closed")

        windows = gw.getWindowsWithTitle(self.process_title)
        if not windows:
            raise WoWnotFoundException(
                f"No windows with title {self.process_title} were found"
            )

        bbox = namedtuple("bbox", ["left", "top", "width", "height"])
        self.bbox = bbox(*windows[0].box)
        self.location = convert_bbox_to_location(self.bbox)


@dataclass
class Monitor:
    """Represents a monitor"""

    name: Optional[str] = None
    number: Optional[int] = None
    bbox: Optional[namedtuple] = None
    location: Optional[namedtuple] = None
    image: Optional[Image] = None
    timestamp: Optional[datetime] = None

    def __repr__(self):
        return f"Process Name: {self.name}\nLocation: {self.location}"

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def update_monitor_image(self):
        if not isinstance(self.number, int):
            raise ValueError(
                f"Expecting a valid monitor number, got {self.number} instead"
            )

        with mss() as sct:
            monitor = sct.monitors[self.number]
            sct_img = sct.grab(monitor)
            # Convert to PIL Image
            self.image = Image.frombytes(
                "RGB", sct_img.size, sct_img.bgra, "raw", "BGRX"
            )
            self.timestamp = datetime.now()


@dataclass
class SubImage:
    """Represents a specific section of the client screen"""

    name: str = ""
    bbox: Optional[BBox] = None
    location: Optional[Location] = None
    absolute_location: Optional[Location] = None
    absolute_bbox: Optional[BBox] = None
    found: bool = False
    image: Optional[Image] = None
    timestamp: Optional[datetime] = None

    def __repr__(self):
        return f"SubImage Name: {self.name}\nLocation: {self.location}"

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def set_bbox_or_location(self):
        if self.bbox and not self.location:
            self.location = convert_bbox_to_location(self.bbox)
        if not self.bbox and self.location:
            self.bbox = convert_location_to_bbox(self.location)

        if self.absolute_bbox and not self.absolute_location:
            self.absolute_location = convert_bbox_to_location(self.absolute_bbox)
        if not self.absolute_bbox and self.absolute_location:
            self.absolute_bbox = convert_location_to_bbox(self.absolute_location)

    def update_image(self, client: "WoWclient"):
        with mss() as _sct:
            self.image = client.monitor.image.crop(self.location)
            self.timestamp = datetime.now()

    def update_location(
        self,
        client: "WoWclient",
        threshold=0.9,
        grayscale=True,
        update_image: bool = True,
    ):
        self.location = None
        self.bbox = None
        self.absolute_location = None
        self.absolute_bbox = None

        if not self.image:
            return

        self.found, self.location = find_image(
            client, self.image, threshold, grayscale, update_image
        )

        if self.found:
            self.absolute_location = get_absolute_location(
                client.wow_coordinates.location, self.location
            )
            self.set_bbox_or_location()

        self.timestamp = datetime.now()


@dataclass
class WoWclient:
    """Represents a WoW client"""

    process_name: Optional[str] = "WowClassic.exe"
    process_title: Optional[str] = "World of Warcraft"

    wow_coordinates: Optional[WoWcoordinates] = None
    monitor: Optional[Monitor] = None
    monitor_relative_location: Optional[namedtuple] = None
    image: Optional[Image.Image] = None
    timestamp: Optional[datetime] = None

    sub_images: List[SubImage] = field(default_factory=list)
    movements: dict = field(default_factory=dict)

    def __repr__(self):
        return (
            f"Process Name: {self.process_name} | Process title: {self.process_title}"
        )

    def __eq__(self, other):
        return (
            self.process_name == self.process_name
            and self.process_title == self.process_title
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.process_name)

    def find_screen(self):
        if not isinstance(self.wow_coordinates, WoWcoordinates):
            self.wow_coordinates = WoWcoordinates(
                process_name=self.process_name, process_title=self.process_title
            )

        self.wow_coordinates.update_coordinates()
        monitors = [
            monitor
            for monitor in get_monitors()
            if is_subbox(get_monitor_bbox(monitor), self.wow_coordinates.bbox)
        ]
        if not monitors:
            raise MonitorNotFoundException(
                f"Could not find monitor corresponding to {self.wow_coordinates}"
            )
        if len(monitors) > 1:
            raise ValueError(f"Expected 1 monitor match, got {len(monitors)} instead")

        monitor = monitors[0]
        self.monitor = Monitor(name=monitor.name, bbox=get_monitor_bbox(monitor))
        self.monitor.location = convert_bbox_to_location(self.monitor.bbox)

        with mss() as sct:
            mss_monitors = sct.monitors
            for i in range(1, len(mss_monitors)):
                monitor_bbox = get_mss_monitor_bbox(mss_monitors[i])
                if monitor_bbox == self.monitor.bbox:
                    self.monitor.number = i

        if not self.monitor.number:
            raise MonitorNotFoundException(
                f"Could not find monitor number corresponding to {self.monitor}"
            )

        self.monitor_relative_location = get_relative_location(
            self.monitor.bbox, self.wow_coordinates.bbox
        )

    def update_client_image(self):
        if not self.monitor_relative_location:
            self.find_screen()

        self.monitor.update_monitor_image()
        with mss() as _sct:
            self.image = self.monitor.image.crop(self.monitor_relative_location)
            self.timestamp = datetime.now()

    def load_sub_images(self):
        """Load all images from the data directory and create SubImage objects"""
        # Path to the data directory (assuming the module structure from the screenshot)
        module_dir = Path(__file__).parent.parent
        data_dir = module_dir / "data"

        # Common image extensions
        image_extensions = [".png", ".jpg", ".jpeg"]

        if not data_dir.exists():
            print(f"Warning: Data directory not found at {data_dir}")
            return

        # Load each image file and create a SubImage
        for file_path in data_dir.iterdir():
            if file_path.suffix.lower() in image_extensions and not get_image_from_list(
                file_path.stem, self.sub_images, raise_error=False
            ):
                try:
                    # Load the image using PIL
                    img = Image.open(file_path)

                    # Create a SubImage with just the image attribute
                    sub_image = SubImage(
                        name=file_path.stem,  # Using filename without extension as name
                        image=img,
                    )

                    # Add to the list
                    self.sub_images.append(sub_image)
                except Exception as e:
                    print(f"Error loading image {file_path}: {e}")

    def load_movements(self):
        """Load all json files from the data directory and create keystroke records"""
        # Path to the data directory (assuming the module structure from the screenshot)
        module_dir = Path(__file__).parent.parent
        movements_dir = module_dir / "movements"

        if not movements_dir.exists():
            print(f"Warning: Data directory not found at {movements_dir}")
            return

        # Load each json file
        for file_path in movements_dir.iterdir():
            if file_path.suffix.lower() == ".json" and not self.movements.get(
                file_path.stem
            ):
                try:
                    # Open and read the JSON file
                    with open(file_path, "r") as f:
                        movements_data = json.load(f)

                    # Store the data in the movements dictionary using the filename (without extension) as the key
                    self.movements[file_path.stem] = movements_data

                    print(f"Loaded movement data from {file_path.name}")
                except json.JSONDecodeError:
                    print(f"Error: Could not parse JSON in {file_path}")
                except Exception as e:
                    print(f"Error loading {file_path}: {str(e)}")

    def update_sub_image(
        self,
        name: str,
        threshold: float = 0.9,
        grayscale: bool = True,
        update_client_image: bool = True,
    ):
        image = get_image_from_list(name, self.sub_images)
        image.update_location(
            self,
            threshold=threshold,
            grayscale=grayscale,
            update_image=update_client_image,
        )

    def update_sub_images(
        self,
        threshold: float = 0.9,
        grayscale: bool = True,
        update_client_image: bool = True,
    ):
        for img in self.sub_images:
            img.update_location(
                self,
                threshold=threshold,
                grayscale=grayscale,
                update_image=update_client_image,
            )

    def get_sub_image(self, name: str):
        return get_image_from_list(name, self.sub_images)

    def focus_client(self):
        focus_client(self)

    def reload_client(self, threshold: float = 0.9, grayscale: bool = True):
        reload_client(self, threshold, grayscale)


def find_image(
    client: WoWclient,
    template_image: Image.Image,
    threshold: float = 0.9,
    grayscale: bool = True,
    update_image: bool = True,
) -> Tuple[bool, Optional[Location]]:
    """
    Search for a template image within the WoW client screen.

    Args:
        client (WoWclient): The WoW client instance
        template_image (PIL.Image): The template image to search for
        threshold (float): The matching threshold (0-1), higher values require closer matches
        grayscale (bool): Whether to convert images to grayscale before matching
        update_image (bool): Updates the image before attempting to locate the subimage

    Returns:
        Tuple[bool, Optional[Location]]:
            - A boolean indicating if the image was found
            - If found, a Location namedtuple with left, top, right, bottom; None otherwise
    """
    # Refresh the client image first
    if update_image:
        client.update_client_image()

    # Convert PIL images to numpy arrays for OpenCV
    client_img = np.array(client.image)
    template_img = np.array(template_image)

    # Convert images to BGR format for OpenCV
    if client_img.shape[2] == 4:  # If RGBA
        client_img = client_img[:, :, :3]
    if template_img.shape[2] == 4:  # If RGBA
        template_img = template_img[:, :, :3]

    # Convert RGB to BGR (OpenCV format)
    client_img = cv2.cvtColor(client_img, cv2.COLOR_RGB2BGR)
    template_img = cv2.cvtColor(template_img, cv2.COLOR_RGB2BGR)

    # Convert to grayscale if requested (improves matching in many cases)
    if grayscale:
        client_img = cv2.cvtColor(client_img, cv2.COLOR_BGR2GRAY)
        template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

    # Get template dimensions
    h, w = template_img.shape[:2]

    # Use template matching
    method = cv2.TM_CCOEFF_NORMED
    result = cv2.matchTemplate(client_img, template_img, method)

    # Find the best match
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # For TM_CCOEFF_NORMED, the max value is our best match
    if max_val >= threshold:
        # Create a Location namedtuple (left, top, right, bottom)
        match_location = Location(
            left=max_loc[0], top=max_loc[1], right=max_loc[0] + w, bottom=max_loc[1] + h
        )
        return True, match_location

    return False, None


def get_image_from_list(
    name: str, image_list: List[SubImage], raise_error: bool = True
) -> Union[SubImage, None]:
    """
    Retrieve a SubImage with the specified name from a list of SubImages.

    Args:
        name (str): The name of the SubImage to find
        image_list (List[SubImage]): The list of SubImages to search
        raise_error (bool): Raises an error if the image is not found

    Returns:
        SubImage: The found SubImage object

    Raises:
        ImageNotFoundException: If no SubImage with the given name is found
    """
    for image in image_list:
        if image.name.lower().strip() == name.lower().strip():
            return image

    if raise_error:
        raise ImageNotFoundException(f"SubImage with name '{name}' not found")

    return None


def focus_client(client: WoWclient):
    """
    Focus the client

    Args:
        client (WoWclient): The WoW client instance
    """
    wow_windows = gw.getWindowsWithTitle(client.process_title)
    if not wow_windows:
        print(f"Error: Could not find window with title '{client.process_title}'")
        return

    try:
        wow_window = wow_windows[0]
        wow_window.activate()
        time.sleep(0.5)  # Give time for window to gain focus
    except Exception as e:
        print(f"Error focusing WoW window: {e}")
        return


def reload_client(client: WoWclient, threshold: float = 0.9, grayscale: bool = True):
    """
    Reloads the client

    Args:
        client (WoWclient): The WoW client instance
        threshold (float): The matching threshold for image recognition
        grayscale (bool): Whether to use grayscale for image recognition
    """
    chat_typing_box = get_image_from_list("chat_typing_box", client.sub_images)
    chat_typing_box.update_location(client, threshold, grayscale)
    if chat_typing_box.found:
        # Click on the chat typing box
        x, y = get_bbox_center(chat_typing_box.absolute_bbox)
        move_mouse(x, y)
        pyautogui.click()

        # Select all existing text and delete it
        pyautogui.keyDown("ctrl")
        pyautogui.press("a")
        pyautogui.keyUp("ctrl")
        pyautogui.press("delete")

        # Type the target command
        pyautogui.write(f"/rl")
        pyautogui.press("enter")

    else:
        # Press enter to open chat
        pyautogui.press("enter")
        time.sleep(0.5)  # Brief delay to ensure the chat opens

        # Verify that the chat typing box is now visible
        chat_typing_box.update_location(client, threshold, grayscale)
        if not chat_typing_box.found:
            print("Error: Chat typing box not found after pressing enter")
            return

        # Click on the chat typing box
        x, y = get_bbox_center(chat_typing_box.absolute_bbox)
        move_mouse(x, y)
        pyautogui.click()
        time.sleep(0.5)

        # Type the target command
        pyautogui.write(f"/rl")
        pyautogui.press("enter")

    # Wait for the targeting to complete
    time.sleep(5)
