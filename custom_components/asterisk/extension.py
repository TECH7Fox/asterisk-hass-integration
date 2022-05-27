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
        self._state = status
        self._tech = tech
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_{extension}_state"
        self._astmanager.register_event("DeviceStateChange", self.handle_asterisk_event)

    def handle_asterisk_event(self, event, astmanager):
        """Handle events."""
        extension = event.get_header("Device")
        if extension == f"{self._tech}/{self._extension}":
            self._state = event.get_header("State")
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
            "via_device": (DOMAIN, f"{self._entry.entry_id}_server"),
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
        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = event.get_header("ConnectedLineName")
            self.hass.async_add_job(self.async_update_ha_state())

    def handle_hangup(self, event, astmanager):
        """Handle hangup."""
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
            "via_device": (DOMAIN, f"{self._entry.entry_id}_server"),
        }

    @property
    def name(self):
        """Callee number."""
        return f"{self._extension} Callee"

    @property
    def state(self):
        """Callee number."""
        return self._state

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
        extension = event.get_header("CallerIDNum")
        if (self._extension == extension):
            self._state = event.get_header("Channel")
            self.hass.async_add_job(self.async_update_ha_state())

    def handle_hangup(self, event, astmanager):
        """Handle Hangup."""
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
            "via_device": (DOMAIN, f"{self._entry.entry_id}_server"),
        }

    @property
    def name(self):
        """Channel."""
        return f"{self._extension} Channel"

    @property
    def state(self):
        """Channel."""
        return self._state

class RegisteredSensor(BinarySensorEntity):
    """Binary Sensor with Registered."""

    def __init__(self, hass, status, extension, tech, entry):
        """Setting up extension."""
        self._hass = hass
        self._extension = extension
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._state = (status != "Unavailable" and status != "Unknown")
        self._tech = tech
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_{extension}_registered"
        self._astmanager.register_event("EndpointDetail", self.handle_status_event)

    def handle_status_event(self, event, astmanager):
        """Handle Extension Status Event."""
        extension = event.get_header("ObjectName")
        status = event.get_header("DeviceState")
        if extension == self._extension:
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
            "via_device": (DOMAIN, f"{self._entry.entry_id}_server"),
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
        cdict = {"Action": "PJSIPShowEndpoint",
                 "Endpoint": self._extension}
        self._astmanager.send_action(cdict)