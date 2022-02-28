"""Asterisk platform."""
import logging

import voluptuous as vol
import json

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN, SW_VERSION
from homeassistant.const import CONF_HOST

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["asterisk"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required("extension"): cv.string})

async def async_setup_entry(hass, entry, async_add_entities):
    """Setting up every extension."""
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]

    entities = [AsteriskServer(hass, entry)]
    for device in devices:
        entities.append(AsteriskExtension(hass, device["status"], device["extension"], device["tech"], entry))
        entities.append(AsteriskCallee(hass, device["extension"], device["tech"], entry))
        _LOGGER.info(f"Setting up asterisk extension device for extension {device['tech']}{device['extension']}")

    async_add_entities(entities, True)

class AsteriskServer(SensorEntity):
    """Entity for a Asterisk server."""

    def __init__(self, hass, entry):
        """Setting up extension."""
        self._hass = hass
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._state = "Unknown"
        self._entry = entry
        self._unique_id = entry.entry_id
        _LOGGER.info("Asterisk server device initialized")

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
            "model": "Server",
            "configuration_url": f"http://{self._entry.data[CONF_HOST]}",
            "sw_version": SW_VERSION,
        }

    @property
    def name(self):
        """Extension name."""
        return f"PBX Server"

    @property
    def state(self):
        """Extension state."""
        return self._state

    def update(self):
        """Update."""
        self._state = self._astmanager.status()
        # _LOGGER.warning(f"Connected: {self._astmanager.connected()}")
        # connected = self._astmanager.connected()

class AsteriskExtension(SensorEntity):
    """Entity for a Asterisk extension."""

    def __init__(self, hass, status, extension, tech, entry):
        """Setting up extension."""
        self._hass = hass
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._extension = extension
        if (status != "Unknown"):
            self._state = "Idle"
        else:
            self._state = "Unknown"
        self._tech = tech
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_{extension}_state"
        self._astmanager.register_event("ExtensionStatus", self.handle_asterisk_event)
        _LOGGER.info("Asterisk extension device initialized")

    def handle_asterisk_event(self, event, astmanager):
        """Handle events."""
        _LOGGER.error("extension update: " + json.dumps(event.headers))

        extension = event.get_header("Exten")
        status = event.get_header("StatusText")
        tech = event.get_header("Channeltype")
        if extension == self._extension:
            _LOGGER.info(f"Got asterisk event for extension {extension}: {status}")
            if (status == "Unknown"): # Fix for Asterisk bug
                status = "Idle"
            self._state = status
            self._tech = tech
            if (status == "InUse"):
                event_data = {
                    "device_id": self.unique_id,
                    "type": "extension_inuse",
                }
                self._hass.bus.async_fire("asterisk_event", event_data)
            self.hass.async_add_job(self.async_update_ha_state())

    @property
    def unique_id(self) -> str:
        """Return a unique id for this instance."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._extension}")},
            "name": f"Extension {self._extension}",
            "manufacturer": "Asterisk",
            "model": self._tech,
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._entry.entry_id),
        }

    @property
    def name(self):
        """Extension state name."""
        return f"{self._extension} State"

    @property
    def state(self):
        """Extension state."""
        return self._state

    def update(self):
        """Update."""
        self._astmanager.extension_state(self._extension, "")
        # _LOGGER.error(f"Extension: {self._extension}, updated status: {result.get_header('Status')}") # temp

class AsteriskCallee(SensorEntity):
    """Entity for a Asterisk extension."""

    def __init__(self, hass, extension, tech, entry):
        """Setting up extension."""
        self._hass = hass
        self._extension = extension
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._state = "None"
        self._tech = tech
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_{extension}_callee"
        self._astmanager.register_event("Newchannel", self.handle_new_channel)
        self._astmanager.register_event("Hangup", self.handle_hangup)

    def handle_new_channel(self, event, astmanager):
        """Handle new channel."""
        _LOGGER.error("new channel: " + json.dumps(event.headers))

        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = event.get_header("Exten")

    def handle_hangup(self, event, astmanager):
        """Handle hangup."""

        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = "None"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this instance."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._extension}")},
            "name": f"Extension {self._extension}",
            "manufacturer": "Asterisk",
            "model": self._tech,
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._entry.entry_id),
        }

    @property
    def name(self):
        """Callee number."""
        return f"{self._extension} Callee"

    @property
    def state(self):
        """Callee number."""
        return self._state

    def update(self):
        """Update."""
        #self._astmanager.extension_state(self._extension, "")
        # _LOGGER.error(f"Extension: {self._extension}, updated status: {result.get_header('Status')}") # temp