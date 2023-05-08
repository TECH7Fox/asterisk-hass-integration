from asterisk.ami import AMIClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CLIENT, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, any]:
    """Return diagnostics for a config entry."""
    client: AMIClient = hass.data[DOMAIN][config_entry.entry_id][CLIENT]
    return {
        "AMI Client": {
            "Address": client._address,
            "Port": client._port,
            "AMI version": client._ami_version,
            "Timeout": client._timeout,
            "Listeners count": client._listeners.count(),
            "Action count": client._action_counter,
            "Encoding error count": client.encoding_errors.count(),
        }
    }
