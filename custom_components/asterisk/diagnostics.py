from asterisk.ami import AMIClient, AutoReconnect
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CLIENT, DOMAIN, AUTO_RECONNECT


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, any]:
    """Return diagnostics for a config entry."""
    client: AMIClient = hass.data[DOMAIN][config_entry.entry_id][CLIENT]
    auto_reconnect: AutoReconnect = hass.data[DOMAIN][config_entry.entry_id][AUTO_RECONNECT]
    return {
        "AMI Client": {
            "Address": client._address,
            "Port": client._port,
            "AMI version": client._ami_version,
        },
        "Auto Reconnect": {
            "Alive": auto_reconnect.is_alive(),
            "Delay": auto_reconnect.delay,
            "Name": auto_reconnect.name,
            "Deamon": auto_reconnect.daemon,
        },
    }
