from homeassistant.core import HomeAssistant
import pytest


@pytest.mark.asyncio
async def test_send_action(hass: HomeAssistant):
    """Test the Send Action service."""
    # TODO:
    # assert await hass.services.async_call(
    #     "asterisk",
    #     "send_action",
    #     {
    #         "action": "Ping",
    #     },
    # )
    assert True
