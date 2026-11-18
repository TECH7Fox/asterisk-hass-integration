import inspect
from unittest.mock import patch

import pytest

from custom_components.asterisk import async_setup_entry
from custom_components.asterisk.const import DOMAIN

from .mock_ami_client import MockAMIClient, MockAutoReconnect


def _supports_return_response(hass) -> bool:
    """Return whether this HA test environment supports service responses."""
    return "return_response" in inspect.signature(hass.services.async_call).parameters


async def test_send_action_returns_response(hass, config_entry):
    """Test the send_action service returns the AMI response."""
    client = MockAMIClient()

    with patch("custom_components.asterisk.AMIClient", return_value=client), patch(
        "custom_components.asterisk.AutoReconnect", MockAutoReconnect
    ):
        assert await async_setup_entry(hass, config_entry)

    if not _supports_return_response(hass):
        pytest.skip("Home Assistant test environment does not support service responses")

    response = await hass.services.async_call(
        DOMAIN,
        "send_action",
        {"action": "Ping"},
        blocking=True,
        return_response=True,
    )

    assert response["response"]["Response"] == "Success"
    assert response["response"]["Message"] == "Pong"


async def test_get_conference_rooms_returns_open_room(hass, config_entry):
    """Test the conference room service returns room state."""
    client = MockAMIClient(
        confbridge_rooms=[
            {
                "Conference": "1029",
                "Parties": "2",
                "Marked": "0",
                "Locked": "No",
                "Muted": "No",
            }
        ]
    )

    with patch("custom_components.asterisk.AMIClient", return_value=client), patch(
        "custom_components.asterisk.AutoReconnect", MockAutoReconnect
    ):
        assert await async_setup_entry(hass, config_entry)

    if not _supports_return_response(hass):
        pytest.skip("Home Assistant test environment does not support service responses")

    response = await hass.services.async_call(
        DOMAIN,
        "get_conference_rooms",
        {"conference": "1029"},
        blocking=True,
        return_response=True,
    )

    assert response["is_open"] is True
    assert response["room_count"] == 1
    assert response["room"] == {
        "conference": "1029",
        "parties": 2,
        "marked": 0,
        "locked": False,
        "muted": False,
    }


async def test_get_conference_rooms_treats_no_active_conferences_as_empty(
    hass, config_entry
):
    """Test no active conferences is returned as an empty room list."""
    client = MockAMIClient(confbridge_error_message="No active conferences.")

    with patch("custom_components.asterisk.AMIClient", return_value=client), patch(
        "custom_components.asterisk.AutoReconnect", MockAutoReconnect
    ):
        assert await async_setup_entry(hass, config_entry)

    if not _supports_return_response(hass):
        pytest.skip("Home Assistant test environment does not support service responses")

    response = await hass.services.async_call(
        DOMAIN,
        "get_conference_rooms",
        {"conference": "1029"},
        blocking=True,
        return_response=True,
    )

    assert response["is_open"] is False
    assert response["room_count"] == 0
    assert response["rooms"] == []
    assert response["room"] is None
    assert response["complete"]["ListItems"] == "0"
