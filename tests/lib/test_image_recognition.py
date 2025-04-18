import pytest
from pathlib import Path
from collections import namedtuple

from tests.constructs import build_wow_client_from_monitor_image

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_TEST_OUTPUTS = PROJECT_ROOT / "tests" / "outputs"
PROJECT_TEST_DATA = PROJECT_ROOT / "tests" / "data"
PACKAGE_DATA = PROJECT_ROOT / "avbot" / "data"

BBox = namedtuple("BBox", ["left", "top", "width", "height"])


@pytest.mark.parametrize(
    "client_image_name, subimage_name",
    [
        ("av_dead", "resurrection"),
        ("av_end", "leave_battleground"),
        ("av_enter_battle", "enter_battle"),
        ("av_instance_menu", "join_battle"),
        ("av_queuing_menu", "queue_for_battleground"),
    ],
)
def test_subimage_recognition(client_image_name, subimage_name):
    """
    Test if only the subimage yields a match

    :param client_image_name: Name of the client image file without extension
    :param subimage_name: Name of the subimage to search for
    :return:
    """
    client = build_wow_client_from_monitor_image(
        PROJECT_TEST_DATA / f"{client_image_name}.png"
    )
    client.load_sub_images()
    client.update_sub_images(update_client_image=False)

    located_images = [img.name for img in client.sub_images if img.found]
    assert len(located_images) == 1
    assert located_images[0].lower() == subimage_name.lower()
