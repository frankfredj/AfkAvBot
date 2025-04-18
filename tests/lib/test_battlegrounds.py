import pytest

from avbot.lib.screen import WoWclient
from avbot.lib.battlegrounds import (
    afk_bg,
)


@pytest.fixture
def wow_client():
    """Create and initialize a WoW client for testing."""
    client = WoWclient()
    client.find_screen()
    client.load_sub_images()
    client.load_movements()
    yield client


def test_afk_bg(wow_client):
    afk_bg(client=wow_client, n=3)
