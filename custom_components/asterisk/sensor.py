import logging

from asterisk.ami import Event, SimpleAction
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import CONF_DEVICES
from homeassistant.util.dt import now

from .base import AsteriskDeviceEntity
from .const import DOMAIN, STATE_ICONS, STATES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Asterisk sensor platform."""
    devices = hass.data[DOMAIN][entry.entry_id][CONF_DEVICES]

    entities = []

    for device in devices:
        entities.append(DeviceStateSensor(hass, entry, device))
        entities.append(ConnectedLineSensor(hass, entry, device))
        entities.append(DTMFSentSensor(hass, entry, device))
        entities.append(DTMFReceivedSensor(hass, entry, device))
        entities.append(VoicemailStatusSensor(hass, entry, device))

    async_add_entities(entities, False)


class DeviceStateSensor(AsteriskDeviceEntity, SensorEntity):
    """Sensor entity for the device state."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        super().__init__(hass, entry, device)
        self._unique_id = f"{self._unique_id_prefix}_state"
        self._name = f"{device['extension']} State"
        self._state = device["status"]
        self._ami_client.add_event_listener(
            self.handle_event,
            white_list=["DeviceStateChange"],
            Device=f"{device['tech']}/{device['extension']}",
        )

    def handle_event(self, event: Event, **kwargs):
        """Handle an endpoint update event."""
        state = event["State"]
        self._state = STATES.get(state, STATES["UNKNOWN"])
        self.schedule_update_ha_state()

    @property
    def state(self) -> str:
        """Return registered state."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return STATE_ICONS.get(self._state, STATE_ICONS["Unknown"])


class ConnectedLineSensor(AsteriskDeviceEntity, SensorEntity):
    """Sensor entity for the connected line number."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        super().__init__(hass, entry, device)
        self._unique_id = f"{self._unique_id_prefix}_connected_line"
        self._name = f"{device['extension']} Connected Line"
        self._state = "None"
        self._extra_attributes = {}
        self._ami_client.add_event_listener(
            self.handle_new_connected_line,
            white_list=["NewConnectedLine"],
            CallerIDNum=device["extension"],
        )
        self._ami_client.add_event_listener(
            self.handle_new_connected_line,
            white_list=["NewConnectedLine"],
            ConnectedLineNum=device["extension"],
        )
        self._ami_client.add_event_listener(
            self.handle_hangup,
            white_list=["Hangup"],
            CallerIDNum=device["extension"],
        )
        self._ami_client.add_event_listener(
            self.handle_new_channel,
            white_list=["Newchannel"],
            CallerIDNum=device["extension"],
        )

    def handle_new_connected_line(self, event: Event, **kwargs):
        """Handle an NewConnectedLine event."""
        if event["ConnectedLineNum"] != self._device["extension"]:
            self._state = event["ConnectedLineNum"]
        else:
            self._state = event["CallerIDNum"]
        self._extra_attributes = {
            "Channel": event["Channel"],
            "ChannelState": event["ChannelState"],
            "ChannelStateDesc": event["ChannelStateDesc"],
            "CallerIDNum": event["CallerIDNum"],
            "CallerIDName": event["CallerIDName"],
            "ConnectedLineNum": event["ConnectedLineNum"],
            "ConnectedLineName": event["ConnectedLineName"],
            "Exten": event["Exten"],
            "Context": event["Context"],
        }
        self.schedule_update_ha_state()

    def handle_hangup(self, event: Event, **kwargs):
        """Handle an Hangup event."""
        if event["Cause"] != "26":
            self._state = "None"
            self._extra_attributes = {
                "Channel": event["Channel"],
                "ChannelState": event["ChannelState"],
                "ChannelStateDesc": event["ChannelStateDesc"],
                "CallerIDNum": event["CallerIDNum"],
                "CallerIDName": event["CallerIDName"],
                "ConnectedLineNum": event["ConnectedLineNum"],
                "ConnectedLineName": event["ConnectedLineName"],
                "Exten": event["Exten"],
                "Context": event["Context"],
                "Cause": event["Cause"],
                "Cause-txt": event["Cause-txt"],
            }
            self.schedule_update_ha_state()

    def handle_new_channel(self, event: Event, **kwargs):
        """Handle an NewChannel event."""
        self._state = "None"
        self._extra_attributes = {
            "Channel": event["Channel"],
            "ChannelState": event["ChannelState"],
            "ChannelStateDesc": event["ChannelStateDesc"],
            "CallerIDNum": event["CallerIDNum"],
            "CallerIDName": event["CallerIDName"],
            "ConnectedLineNum": event["ConnectedLineNum"],
            "ConnectedLineName": event["ConnectedLineName"],
            "Exten": event["Exten"],
            "Context": event["Context"],
        }
        self.schedule_update_ha_state()

    @property
    def state(self) -> str:
        """Return registered state."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_attributes

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return (
            "mdi:phone-remove"
            if self._state == "None"
            else "mdi:phone-incoming-outgoing"
        )


class DTMFSentSensor(AsteriskDeviceEntity, SensorEntity):
    """Sensor entity with the latest DTMF sent."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        super().__init__(hass, entry, device)
        self._unique_id = f"{self._unique_id_prefix}_dtmf_sent"
        self._name = f"{device['extension']} DTMF Sent"
        self._state = None
        self._extra_attributes = {}
        self._ami_client.add_event_listener(
            self.handle_dtmf,
            white_list=["DTMFBegin"],
            ConnectedLineNum=device["extension"],
            Direction="Sent",
        )

    def handle_dtmf(self, event: Event, **kwargs):
        """Handle an DTMF event."""
        self._state = now()
        self._extra_attributes = {
            "Channel": event["Channel"],
            "Digit": event["Digit"],
            "CallerIDNum": event["CallerIDNum"],
            "CallerIDName": event["CallerIDName"],
            "ConnectedLineNum": event["ConnectedLineNum"],
            "ConnectedLineName": event["ConnectedLineName"],
            "Context": event["Context"],
        }
        self.schedule_update_ha_state()

    @property
    def state(self) -> str:
        """Return registered state."""
        return self._state

    @property
    def device_class(self) -> SensorDeviceClass:
        return SensorDeviceClass.TIMESTAMP

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_attributes


class DTMFReceivedSensor(AsteriskDeviceEntity, SensorEntity):
    """Sensor entity with the latest DTMF received."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        super().__init__(hass, entry, device)
        self._unique_id = f"{self._unique_id_prefix}_dtmf_received"
        self._name = f"{device['extension']} DTMF Received"
        self._state = None
        self._extra_attributes = {}
        self._ami_client.add_event_listener(
            self.handle_dtmf,
            white_list=["DTMFBegin"],
            ConnectedLineNum=device["extension"],
            Direction="Received",
        )

    def handle_dtmf(self, event: Event, **kwargs):
        """Handle an DTMF event."""
        self._state = now()
        self._extra_attributes = {
            "Channel": event["Channel"],
            "Digit": event["Digit"],
            "ConnectedLineNum": event["ConnectedLineNum"],
            "ConnectedLineName": event["ConnectedLineName"],
            "Context": event["Context"],
        }
        self.schedule_update_ha_state()

    @property
    def state(self) -> str:
        """Return registered state."""
        return self._state

    @property
    def device_class(self) -> SensorDeviceClass:
        return SensorDeviceClass.TIMESTAMP

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_attributes


class VoicemailStatusSensor(AsteriskDeviceEntity, SensorEntity):
    """Sensor entity for voicemail status."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        super().__init__(hass, entry, device)
        self._unique_id = f"{self._unique_id_prefix}_voicemail_status"
        self._name = f"{device['extension']} Voicemail Status"
        self._state = 0
        self._extra_attributes = {}
        self._mailbox = f"{device['extension']}@default"

        # Listen for MWI (Message Waiting Indicator) events
        self._ami_client.add_event_listener(
            self.handle_mwi,
            white_list=["MWI"],
            Mailbox=self._mailbox,
        )

        # Get initial voicemail status
        self._get_initial_status()

    def _get_initial_status(self):
        """Get initial voicemail status using MailboxStatus action."""
        try:
            future = self._ami_client.send_action(
                SimpleAction("MailboxStatus", Mailbox=self._mailbox)
            )
            if future.response and not future.response.is_error():
                self._update_from_response(future.response.keys)
        except Exception as e:
            _LOGGER.warning(
                f"Failed to get initial voicemail status for {self._mailbox}: {e}"
            )

    def _update_from_response(self, response_data):
        """Update sensor state from AMI response data."""
        try:
            new_messages = int(response_data.get("NewMessages", 0))
            old_messages = int(response_data.get("OldMessages", 0))

            self._state = new_messages
            self._extra_attributes = {
                "new_messages": new_messages,
                "old_messages": old_messages,
                "total_messages": new_messages + old_messages,
                "mailbox": self._mailbox,
            }
        except (ValueError, TypeError) as e:
            _LOGGER.warning(
                f"Failed to parse voicemail status data for {self._mailbox}: {e}"
            )

    def handle_mwi(self, event: Event, **kwargs):
        """Handle MWI (Message Waiting Indicator) event."""
        try:
            new_messages = int(event.get("New", 0))
            old_messages = int(event.get("Old", 0))

            self._state = new_messages
            self._extra_attributes = {
                "new_messages": new_messages,
                "old_messages": old_messages,
                "total_messages": new_messages + old_messages,
                "mailbox": event.get("Mailbox", self._mailbox),
            }
            self.schedule_update_ha_state()
        except (ValueError, TypeError) as e:
            _LOGGER.warning(f"Failed to parse MWI event for {self._mailbox}: {e}")

    @property
    def state(self) -> int:
        """Return the number of new voicemail messages."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_attributes

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:voicemail" if self._state > 0 else "mdi:email-outline"
