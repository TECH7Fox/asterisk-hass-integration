"""Asterisk server entities."""
import logging

import voluptuous as vol
import json
from datetime import date, datetime

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN, SW_VERSION
from homeassistant.const import CONF_HOST

_LOGGER = logging.getLogger(__name__)

class ChannelDTMF(SensorEntity):
    """Sensor with latest DTMF signal."""

    def __init__(self, hass, entry):
        """Setting up extension."""
        self._hass = hass
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._state = "Unknown"
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_dtmf"
        self._dtmf = {
            "channel": None,
            "digit": None,
            "extension": None,
            "callerid_number": None,
            "connected_line_number": None
        }
        self._astmanager.register_event("DTMFBegin", self.handle_asterisk_event)

    def handle_asterisk_event(self, event, astmanager):
        """Handle events."""
        extension = event.get_header("CallerIDNum")
        direction = event.get_header("Direction")
        if direction == "Sent":
            self._state = datetime.now()
            self._dtmf = {
                "channel": event.get_header("Channel"),
                "digit": event.get_header("Digit"),
                "extension": event.get_header("Exten"),
                "callerid_number": event.get_header("CallerIDNum"),
                "connected_line_number": event.get_header("ConnectedLineNum")
            }
            self.hass.async_add_job(self.async_update_ha_state())

    @property
    def unique_id(self) -> str:
        """Return a unique id for this instance."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": "Asterisk Server",
            "manufacturer": "Asterisk",
            "model": "Server",
            "configuration_url": f"http://{self._entry.data[CONF_HOST]}",
            "sw_version": SW_VERSION,
        }

    @property
    def name(self):
        """Extension name."""
        return f"Latest DTMF Signal"

    @property
    def state(self):
        """DTMF Datetime."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._dtmf

class AsteriskServer(SensorEntity):
    """Entity for a Asterisk server."""

    def __init__(self, hass, entry):
        """Setting up extension."""
        self._hass = hass
        self._astmanager = hass.data[DOMAIN][entry.entry_id]["manager"]
        self._state = "Unknown"
        self._entry = entry
        self._unique_id = f"{entry.entry_id}_server"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this instance."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": "Asterisk Server",
            "manufacturer": "Asterisk",
            "model": "Server",
            "configuration_url": f"http://{self._entry.data[CONF_HOST]}",
            "sw_version": SW_VERSION,
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
        if not self._astmanager.connected():
            self._state = "Disconnected"
        else:
            self._state = self._astmanager.status()