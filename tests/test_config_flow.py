from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import pytest

from custom_components.asterisk.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow(hass: HomeAssistant):
    """Test config flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["errors"] == {}
    assert result["step_id"] == "user"
