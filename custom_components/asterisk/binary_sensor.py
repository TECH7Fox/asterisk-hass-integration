import logging

from asterisk.ami import AMIClient, AutoReconnect, Event, SimpleAction
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICES

from .base import AsteriskDeviceEntity
from .const import AUTO_RECONNECT, CLIENT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Asterisk sensor platform."""
    devices = hass.data[DOMAIN][entry.entry_id][CONF_DEVICES]

    entities = [AMIConnected(hass, entry)]

    for device in devices:
        entities.append(RegisteredSensor(hass, entry, device))

    async_add_entities(entities, False)


class RegisteredSensor(AsteriskDeviceEntity, BinarySensorEntity):
    """Binary entity for the registered state."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        super().__init__(hass, entry, device)
        self._unique_id = f"{self._unique_id_prefix}_registered"
        self._name = f"{device['extension']} Registered"
        self._state = (
            device["status"] != "Unavailable" and device["status"] != "Unknown"
        )
        self._ami_client.add_event_listener(
            self.handle_state_change,
            white_list=["DeviceStateChange"],
            Device=f"{device['tech']}/{device['extension']}",
        )

    def handle_state_change(self, event: Event, **kwargs):
        """Handle an device state change event."""
        state = event["State"]
        self._state = state != "UNAVAILABLE" and state != "UNKNOWN"
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return registered state."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:phone-check" if self._state else "mdi:phone-off"


class AMIConnected(BinarySensorEntity):
    """Binary entity for the AMI connection state."""

    def __init__(self, hass, entry):
        """Initialize the sensor."""
        self._entry = entry
        self._unique_id = f"{self._entry.entry_id}_connected"
        self._name = "AMI Connected"
        self._state: bool = True
        self._ami_client: AMIClient = hass.data[DOMAIN][entry.entry_id][CLIENT]
        self._auto_reconnect: AutoReconnect = hass.data[DOMAIN][entry.entry_id][
            AUTO_RECONNECT
        ]
        self._auto_reconnect.on_disconnect = self.on_disconnect
        self._auto_reconnect.on_reconnect = self.on_reconnect
        f = self._ami_client.send_action(SimpleAction("CoreSettings"))
        self._asterisk_version = f.response.keys["AsteriskVersion"]

    def on_disconnect(self, client, response):
        _LOGGER.debug(f"Disconnected from AMI: {response}")
        client.disconnect()
        self._state = False
        self.async_write_ha_state()

    def on_reconnect(self, client, response):
        _LOGGER.debug(f"Reconnected to AMI: {response}")
        self._state = True
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_server")},
            "name": "Asterisk Server",
            "manufacturer": "Asterisk",
            "model": "PBX",
            "configuration_url": f"http://{self._entry.data['host']}",
            "sw_version": self._asterisk_version,
        }

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def is_on(self) -> bool:
        """Return connected state."""
        return self._state

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return BinarySensorDeviceClass.CONNECTIVITY
