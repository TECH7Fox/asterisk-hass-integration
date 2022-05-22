"""Asterisk extension entities."""
import logging
from custom_components.asterisk.server import AsteriskServer

import voluptuous as vol
import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN, SW_VERSION
from homeassistant.const import CONF_HOST

_LOGGER = logging.getLogger(__name__)

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
        _LOGGER.warning("extension update: " + json.dumps(event.headers))

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
        #result = self._astmanager.extension_state(self._extension,"")
        #self._state = result.get_header("StatusText")
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
        _LOGGER.warning("new channel: " + json.dumps(event.headers))

        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = event.get_header("Exten")
            self.hass.async_add_job(self.async_update_ha_state())

    def handle_hangup(self, event, astmanager):
        """Handle hangup."""

        _LOGGER.warning("new hangup: " + json.dumps(event.headers))

        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = "None"
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
        """Callee number."""
        return f"{self._extension} Callee"

    @property
    def state(self):
        """Callee number."""
        return self._state

    def update(self):
        """Update."""
        # _LOGGER.error(f"Extension: {self._extension}, updated status: {result.get_header('Status')}") # temp

class CurrentChannelSensor(SensorEntity):
    """Sensor with Current Channel."""

    def __init__(self, hass, extension, tech, entry):
        """Setting up extension."""
        self._hass = hass
        self._extension = extension
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._state = "None"
        self._tech = tech
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_{extension}_channel"
        self._astmanager.register_event("Newchannel", self.handle_new_channel)
        self._astmanager.register_event("Hangup", self.handle_hangup)

    def handle_new_channel(self, event, astmanager):
        """Handle new channel."""
        _LOGGER.warning("new channel: " + json.dumps(event.headers))

        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = event.get_header("Channel")
            self.hass.async_add_job(self.async_update_ha_state())

    def handle_hangup(self, event, astmanager):
        """Handle Hangup."""
        _LOGGER.warning("new hangup: " + json.dumps(event.headers))

        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = "None"
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
        """Channel."""
        return f"{self._extension} Channel"

    @property
    def state(self):
        """Channel."""
        return self._state

    def update(self):
        """Update."""
        # _LOGGER.error(f"Extension: {self._extension}, updated status: {result.get_header('Status')}") # temp

class RegisteredSensor(BinarySensorEntity):
    """Binary Sensor with Registered."""

    def __init__(self, hass, status, extension, tech, entry):
        """Setting up extension."""
        self._hass = hass
        self._extension = extension
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._state = (status != "Unavailable" and status != "Unknown")
        _LOGGER.error("status: " + status)
        _LOGGER.error( self._state)
        self._tech = tech
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_{extension}_registered"
        self._astmanager.register_event("ExtensionStatus", self.handle_status_event)

    def handle_status_event(self, event, astmanager):
        """Handle Extension Status Event."""
        _LOGGER.warning("registered extensionStatus event: " + json.dumps(event.headers))
        status = event.get_header("StatusText")
        self._state = (status != "Unavailable" and status != "Unknown")
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
        """Registered."""
        return f"{self._extension} Registered"

    @property
    def is_on(self):
        """Registered."""
        return self._state

    def update(self):
        """Update."""
        #result = self._astmanager.extension_state(self._extension,"")
        #self._state = result.get_header("StatusText")
        # _LOGGER.error(f"Extension: {self._extension}, updated status: {result.get_header('Status')}") # temp