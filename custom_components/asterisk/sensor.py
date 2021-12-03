"""Asterisk platform."""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["asterisk"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required("extension"): cv.string})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setting up every extension."""
    extension = config.get("extension")
    _LOGGER.info(f"Setting up asterisk extension device for extension {extension}")
    add_devices([AsteriskExtension(hass, extension)], True)
    #await async_setup_platform(hass, {}, async_add_entities)

async def async_setup_entry(hass, entry, async_add_devices):
    """Setting up every extension."""
    extension = hass.data[DOMAIN][entry.entry_id]
    entry_id = entry.entry_id
    _LOGGER.warning(f"Setting up asterisk extension device for extension {extension}")
    async_add_devices([AsteriskExtension(hass, extension, entry_id)], True)

class AsteriskExtension(SensorEntity):
    """Entity for a Asterisk extension."""

    def __init__(self, hass, extension, entry_id):
        """Setting up extension."""
        self._hass = hass
        self._astmanager = hass.data[DOMAIN]["manager"]
        self._extension = extension
        self._state = "Unknown"
        self._unique_id = f"{entry_id}_{extension}"
        self._astmanager.register_event("ExtensionStatus", self.handle_asterisk_event)
        _LOGGER.info("Asterisk extension device initialized")

    def handle_asterisk_event(self, event, astmanager):
        """Handle events."""
        extension = event.get_header("Exten")
        status = event.get_header("StatusText")
        if extension == self._extension:
            _LOGGER.info(f"Got asterisk event for extension {extension}: {status}")
            self._state = status
            self.hass.async_add_job(self.async_update_ha_state())

    @property
    def unique_id(self) -> str:
        """Return a unique id for this instance."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": self.name,
            "manufacturer": "Asterisk",
            "model": "SIP", #self._tech
        }

    @property
    def name(self):
        """Extension name."""
        return f"Asterisk Extension {self._extension}"

    @property
    def state(self):
        """Extension state."""
        return self._state

    def update(self):
        """Update."""
        result = self._astmanager.extension_state(self._extension, "")
        self._state = result.get_header("StatusText")
