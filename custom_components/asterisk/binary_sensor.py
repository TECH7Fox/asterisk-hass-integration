import logging

from asterisk.ami import AMIClient, AutoReconnect, Event, SimpleAction
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICES

from .base import AsteriskDeviceEntity
from .const import (
    AMI_CONNECTED,
    AUTO_RECONNECT,
    CLIENT,
    DOMAIN,
    REGISTRATION_ENTITIES,
    REGISTRATIONS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Asterisk sensor platform."""
    devices = hass.data[DOMAIN][entry.entry_id][CONF_DEVICES]

    entities = [AMIConnected(hass, entry)]

    for device in devices:
        entities.append(RegisteredSensor(hass, entry, device))

    for registration in hass.data[DOMAIN][entry.entry_id][REGISTRATIONS]:
        entities.append(OutboundRegistrationSensor(hass, entry, registration))

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
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """Return registered state."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:phone-check" if self._state else "mdi:phone-off"


class OutboundRegistrationSensor(BinarySensorEntity):
    """Binary entity for the state of an outbound registration (trunk)."""

    def __init__(self, hass, entry, registration):
        """Initialize the sensor."""
        self._entry = entry
        self._registration = registration
        self._unique_id = (
            f"{entry.entry_id}_{registration['name']}_outbound_registration"
        )
        self._name = f"{registration['name']} Outbound Registration"
        self._state = registration["status"] == "Registered"
        self._data = hass.data[DOMAIN][entry.entry_id]
        self._data[REGISTRATION_ENTITIES].append(self)
        self._ami_client: AMIClient = self._data[CLIENT]
        self._ami_client.add_event_listener(
            self.handle_registry,
            white_list=["Registry"],
            ChannelType="PJSIP",
            Username=registration["client_uri"],
            Domain=registration["server_uri"],
        )
        # Registry events sent while AMI is disconnected (e.g. during an
        # Asterisk restart) are lost, so the state is re-read on reconnect.
        # While disconnected the sensor is unavailable.
        self._ami_client.add_event_listener(
            self.handle_detail,
            white_list=["OutboundRegistrationDetail"],
            ObjectName=registration["name"],
        )

    def handle_registry(self, event: Event, **kwargs):
        """Handle a registry event for this registration."""
        self._state = event["Status"] == "Registered"
        self.schedule_update_ha_state()

    def handle_detail(self, event: Event, **kwargs):
        """Handle the registration details sent after a reconnect."""
        self._state = event["Status"] == "Registered"
        self.schedule_update_ha_state()

    @property
    def device_info(self):
        """Attach to the endpoint device with the same name, if any."""
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._registration['name']}")},
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
    def available(self) -> bool:
        """Return False while the AMI connection is down."""
        return self._data[AMI_CONNECTED]

    @property
    def is_on(self) -> bool:
        """Return registered state."""
        return self._state

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def extra_state_attributes(self):
        """Return the registration URIs."""
        return {
            "client_uri": self._registration["client_uri"],
            "server_uri": self._registration["server_uri"],
        }


class AMIConnected(BinarySensorEntity):
    """Binary entity for the AMI connection state."""

    def __init__(self, hass, entry):
        """Initialize the sensor."""
        self._entry = entry
        self._unique_id = f"{self._entry.entry_id}_connected"
        self._name = "AMI Connected"
        self._state: bool = True
        self._data = hass.data[DOMAIN][entry.entry_id]
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
        self._data[AMI_CONNECTED] = False
        self.schedule_update_ha_state()
        for entity in self._data[REGISTRATION_ENTITIES]:
            entity.schedule_update_ha_state()

    def on_reconnect(self, client, response):
        _LOGGER.debug(f"Reconnected to AMI: {response}")
        self._state = True
        self._data[AMI_CONNECTED] = True
        self.schedule_update_ha_state()
        for entity in self._data[REGISTRATION_ENTITIES]:
            entity.schedule_update_ha_state()
        # Refresh outbound registrations, events during the outage were missed
        try:
            client.send_action(SimpleAction("PJSIPShowRegistrationsOutbound"))
        except Exception as e:
            _LOGGER.debug("Failed to refresh outbound registrations: %s", e)

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
