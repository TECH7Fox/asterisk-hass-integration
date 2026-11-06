from homeassistant.const import CONF_DEVICES
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.asterisk.const import CLIENT, DOMAIN

from .mock_ami_client import MockAMIClient


from homeassistant.const import CONF_DEVICES
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.asterisk.const import CLIENT, DOMAIN

from .mock_ami_client import MockAMIClient


async def test_voicemail_status_sensor(
    hass: HomeAssistant, config_entry: MockConfigEntry
):
    """Test VoicemailStatusSensor."""
    from custom_components.asterisk.sensor import VoicemailStatusSensor

    client = MockAMIClient()
    # Setup required hass data
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        CLIENT: client,
    }

    device = {
        "tech": "PJSIP",
        "extension": "100",
        "status": "IN_USE",
    }

    # Create sensor directly
    sensor = VoicemailStatusSensor(hass, config_entry, device)

    # Check initial state (should be 2 from mock response)
    assert sensor.state == 2
    assert sensor.extra_state_attributes["new_messages"] == 2
    assert sensor.extra_state_attributes["old_messages"] == 3
    assert sensor.extra_state_attributes["total_messages"] == 5
    assert sensor.extra_state_attributes["mailbox"] == "100@default"
    assert sensor.icon == "mdi:voicemail"

    # Test MWI event handling by calling _update_from_response directly to avoid schedule_update_ha_state
    sensor._update_from_response(
        {
            "NewMessages": "1",
            "OldMessages": "4",
        }
    )

    # Check updated state
    assert sensor.state == 1
    assert sensor.extra_state_attributes["new_messages"] == 1
    assert sensor.extra_state_attributes["old_messages"] == 4
    assert sensor.extra_state_attributes["total_messages"] == 5

    # Test with no voicemails
    sensor._update_from_response(
        {
            "NewMessages": "0",
            "OldMessages": "2",
        }
    )

    assert sensor.state == 0
    assert sensor.icon == "mdi:email-outline"

    # Test sensor properties
    assert sensor.name == "100 Voicemail Status"
    assert sensor.unique_id == f"{config_entry.entry_id}_100_voicemail_status"


# async def test_device_state_sensor(hass: HomeAssistant, config_entry: MockConfigEntry):
#     """Test DeviceStateSensor."""
#     client = MockAMIClient()
#     hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
#         CLIENT: client,
#         CONF_DEVICES: [
#             {
#                 "tech": "PJSIP",
#                 "extension": "100",
#                 "status": "IN_USE",
#             }
#         ],
#     }
#     await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
#     await hass.async_block_till_done()

#     client.trigger_event(
#         {
#             "Event": "DeviceStateChange",
#             "State": "NOT_INUSE",
#         }
#     )

#     await hass.async_block_till_done()
#     sensor = hass.states.get("sensor.100_state")
#     assert sensor is not None
#     assert sensor.state == "Not in use"


# async def test_connected_line_sensor(
#     hass: HomeAssistant, config_entry: MockConfigEntry
# ):
#     """Test ConnectedLineSensor."""
#     client = MockAMIClient()
#     hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
#         CLIENT: client,
#         CONF_DEVICES: [
#             {
#                 "tech": "PJSIP",
#                 "extension": "100",
#                 "status": "IN_USE",
#             }
#         ],
#     }
#     await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
#     await hass.async_block_till_done()

#     client.trigger_event(
#         {
#             "Event": "NewConnectedLine",
#             "ConnectedLineNum": "100",
#             "ConnectedLineName": "Test",
#             "CallerIDNum": "101",
#             "CallerIDName": "Test",
#             "Exten": "102",
#             "Context": "from-internal",
#             "Channel": "PJSIP/100-00000000",
#             "ChannelState": "6",
#             "ChannelStateDesc": "Up",
#             "State": "NOT_INUSE",
#         }
#     )

#     await hass.async_block_till_done()
#     sensor = hass.states.get("sensor.100_connected_line")
#     assert sensor is not None
#     assert sensor.state == "101"


# async def test_dtmf_sent_sensor(hass: HomeAssistant, config_entry: MockConfigEntry):
#     """Test DTMFSentSensor."""
#     client = MockAMIClient()
#     hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
#         CLIENT: client,
#         CONF_DEVICES: [
#             {
#                 "tech": "PJSIP",
#                 "extension": "100",
#                 "status": "IN_USE",
#             }
#         ],
#     }
#     await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
#     await hass.async_block_till_done()

#     sensor = hass.states.get("sensor.100_dtmf_sent")
#     assert sensor is not None
#     assert sensor.state == "unknown"

#     client.trigger_event(
#         {
#             "Event": "DTMFBegin",
#             "Direction": "Outbound",
#             "Digit": "1",
#             "Channel": "PJSIP/100-00000000",
#             "CallerIDNum": "100",
#             "CallerIDName": "Test",
#             "ConnectedLineNum": "100",
#             "ConnectedLineName": "Test",
#             "Context": "from-internal",
#         }
#     )

#     await hass.async_block_till_done()
#     sensor = hass.states.get("sensor.100_dtmf_sent")
#     assert sensor is not None
#     assert sensor.state != "unknown"


# async def test_dtmf_received_sensor(hass: HomeAssistant, config_entry: MockConfigEntry):
#     """Test DTMFReceivedSensor."""
#     client = MockAMIClient()
#     hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
#         CLIENT: client,
#         CONF_DEVICES: [
#             {
#                 "tech": "PJSIP",
#                 "extension": "100",
#                 "status": "IN_USE",
#             }
#         ],
#     }
#     await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
#     await hass.async_block_till_done()

#     sensor = hass.states.get("sensor.100_dtmf_received")
#     assert sensor is not None
#     assert sensor.state == "unknown"

#     client.trigger_event(
#         {
#             "Event": "DTMFBegin",
#             "Direction": "Inbound",
#             "Digit": "1",
#             "Channel": "PJSIP/100-00000000",
#             "CallerIDNum": "100",
#             "CallerIDName": "Test",
#             "ConnectedLineNum": "100",
#             "ConnectedLineName": "Test",
#             "Context": "from-internal",
#         }
#     )

#     await hass.async_block_till_done()
#     sensor = hass.states.get("sensor.100_dtmf_received")
#     assert sensor is not None
#     assert sensor.state != "unknown"
