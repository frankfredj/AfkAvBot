import pytest
from pathlib import Path

from PIL import Image

from avbot.lib.screen import WoWclient
from avbot.lib.movements import (
    rotate,
    moves,
    move_until_death,
    move_randomly_in_bg,
    mount_up,
)

from tests.constructs import build_wow_client_from_monitor_image

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_TEST_OUTPUTS = PROJECT_ROOT / "tests" / "outputs"
PROJECT_TEST_DATA = PROJECT_ROOT / "tests" / "data"
PACKAGE_DATA = PROJECT_ROOT / "avbot" / "data"


def swap_client_image(client: WoWclient, image_name: str):
    client.monitor.image = Image.open(PROJECT_TEST_DATA / f"{image_name}.png")
    client.image = client.monitor.image


@pytest.fixture
def wow_client():
    """Create and initialize a WoW client for testing."""
    client = WoWclient()
    client.find_screen()
    client.load_sub_images()
    client.load_movements()
    yield client


def test_rotate(wow_client):
    wow_client.focus_client()
    rotate(factor=0.125)


def test_moves(wow_client):
    wow_client.focus_client()
    # mounted = mount_up(wow_client, threshold=0.75)
    mounted = False
    # moves(wow_client.movements["move_out_of_cave"], mounted=mounted)
    moves(wow_client.movements["move_to_harpies"], mounted=mounted)


def test_move_until_death(wow_client):
    wow_client.image = Image.open(PROJECT_TEST_DATA / f"av_dead.png")
    wow_client.focus_client()
    for early_check in [True, False]:
        movement_completed = move_until_death(
            client=wow_client,
            movements=wow_client.movements["move_to_harpies"],
            update_image=False,
            early_check=early_check,
        )
        assert not movement_completed

    wow_client.update_client_image()
    for early_check in [True, False]:
        movement_completed = move_until_death(
            client=wow_client,
            movements=wow_client.movements["move_out_of_cave"],
            update_image=False,
            early_check=early_check,
        )
        assert movement_completed


def test_move_randomly_in_bg(wow_client):
    wow_client.focus_client()
    for i in range(10):
        mount_up(wow_client, threshold=0.75)
        move_randomly_in_bg(client=wow_client, n_movements=10)


def test_mount_up(wow_client):
    wow_client.focus_client()
    mount_up(wow_client)
