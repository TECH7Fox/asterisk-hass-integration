from asterisk.ami import AMIClient
from homeassistant.helpers import device_registry as dr

from .const import CLIENT, DOMAIN


class AsteriskDeviceEntity:
    """Base entity for Asterisk devices."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        self._hass = hass
        self._device = device
        self._entry = entry
        self._unique_id_prefix = f"{entry.entry_id}_{device['extension']}"
        self._ami_client: AMIClient = hass.data[DOMAIN][entry.entry_id][CLIENT]
        self._name: str
        self._unique_id: str

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self._unique_id_prefix)},
            "name": f"{self._device['tech']}/{self._device['extension']}",
            "manufacturer": "Asterisk",
            "model": self._device["tech"],
            "via_device_id": dr.async_get_device_id_by_identifier(
                self._hass,
                (DOMAIN, f"{self._entry.entry_id}_server"),
                config_entry_id=self._entry.entry_id,
            ),
        }

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id
