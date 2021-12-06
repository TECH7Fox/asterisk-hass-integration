"""Asterisk platform."""
import logging

import voluptuous as vol
import json

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["asterisk"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required("extension"): cv.string})

async def async_setup_entry(hass, entry, async_add_entities):
    """Setting up every extension."""
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]

    entities = [AsteriskServer(hass, entry.entry_id)]
    for device in devices:
        entities.append(AsteriskExtension(hass, device, entry.entry_id))
        _LOGGER.info(f"Setting up asterisk extension device for extension {device}")

    async_add_entities(entities, True)

class AsteriskServer(SensorEntity):
    """Entity for a Asterisk server."""

    def __init__(self, hass, entry_id):
        """Setting up extension."""
        self._hass = hass
        self._astmanager = hass.data[DOMAIN][entry_id]["manager"]
        self._state = "Unknown"
        self._unique_id = f"{entry_id}"
        self._astmanager.register_event("Status", self.handle_asterisk_event)
        _LOGGER.info("Asterisk server device initialized")

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
            "model": "Server", #self._tech
        }

    @property
    def name(self):
        """Extension name."""
        return f"Asterisk Server"

    @property
    def state(self):
        """Extension state."""
        return self._state

    def update(self):
        """Update."""
        self._state = self._astmanager.status()
        # connected = self._astmanager.connected()

class AsteriskExtension(SensorEntity):
    """Entity for a Asterisk extension."""

    def __init__(self, hass, extension, entry_id):
        """Setting up extension."""
        self._hass = hass
        self._astmanager = hass.data[DOMAIN][entry_id]["manager"]
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