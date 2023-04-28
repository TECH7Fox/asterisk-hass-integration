"""pytest fixtures."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.asterisk.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def config_entry():
    """Fixture representing a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="test",
        data={
            "host": "localhost",
            "port": 5038,
            "username": "admin",
            "password": "admin",
        },
    )
