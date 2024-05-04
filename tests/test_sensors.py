from homeassistant.const import CONF_DEVICES
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.asterisk.const import CLIENT, DOMAIN

from .mock_ami_client import MockAMIClient


async def test_device_state_sensor(hass: HomeAssistant, config_entry: MockConfigEntry):
    """Test DeviceStateSensor."""
    client = MockAMIClient()
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        CLIENT: client,
        CONF_DEVICES: [
            {
                "tech": "PJSIP",
                "extension": "100",
                "status": "IN_USE",
            }
        ],
    }
    await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    await hass.async_block_till_done()

    client.trigger_event(
        {
            "Event": "DeviceStateChange",
            "State": "NOT_INUSE",
        }
    )

    await hass.async_block_till_done()
    sensor = hass.states.get("sensor.100_state")
    assert sensor is not None
    assert sensor.state == "Not in use"

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()


async def test_connected_line_sensor(
    hass: HomeAssistant, config_entry: MockConfigEntry
):
    """Test ConnectedLineSensor."""
    client = MockAMIClient()
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        CLIENT: client,
        CONF_DEVICES: [
            {
                "tech": "PJSIP",
                "extension": "100",
                "status": "IN_USE",
            }
        ],
    }
    await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    await hass.async_block_till_done()

    client.trigger_event(
        {
            "Event": "NewConnectedLine",
            "ConnectedLineNum": "100",
            "ConnectedLineName": "Test",
            "CallerIDNum": "101",
            "CallerIDName": "Test",
            "Exten": "102",
            "Context": "from-internal",
            "Channel": "PJSIP/100-00000000",
            "ChannelState": "6",
            "ChannelStateDesc": "Up",
            "State": "NOT_INUSE",
        }
    )

    await hass.async_block_till_done()
    sensor = hass.states.get("sensor.100_connected_line")
    assert sensor is not None
    assert sensor.state == "101"

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()


async def test_dtmf_sent_sensor(hass: HomeAssistant, config_entry: MockConfigEntry):
    """Test DTMFSentSensor."""
    client = MockAMIClient()
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        CLIENT: client,
        CONF_DEVICES: [
            {
                "tech": "PJSIP",
                "extension": "100",
                "status": "IN_USE",
            }
        ],
    }
    await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    await hass.async_block_till_done()

    sensor = hass.states.get("sensor.100_dtmf_sent")
    assert sensor is not None
    assert sensor.state == "unknown"

    client.trigger_event(
        {
            "Event": "DTMFBegin",
            "Direction": "Outbound",
            "Digit": "1",
            "Channel": "PJSIP/100-00000000",
            "CallerIDNum": "100",
            "CallerIDName": "Test",
            "ConnectedLineNum": "100",
            "ConnectedLineName": "Test",
            "Context": "from-internal",
        }
    )

    await hass.async_block_till_done()
    sensor = hass.states.get("sensor.100_dtmf_sent")
    assert sensor is not None
    assert sensor.state != "unknown"

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()


async def test_dtmf_received_sensor(hass: HomeAssistant, config_entry: MockConfigEntry):
    """Test DTMFReceivedSensor."""
    client = MockAMIClient()
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        CLIENT: client,
        CONF_DEVICES: [
            {
                "tech": "PJSIP",
                "extension": "100",
                "status": "IN_USE",
            }
        ],
    }
    await hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    await hass.async_block_till_done()

    sensor = hass.states.get("sensor.100_dtmf_received")
    assert sensor is not None
    assert sensor.state == "unknown"

    client.trigger_event(
        {
            "Event": "DTMFBegin",
            "Direction": "Inbound",
            "Digit": "1",
            "Channel": "PJSIP/100-00000000",
            "CallerIDNum": "100",
            "CallerIDName": "Test",
            "ConnectedLineNum": "100",
            "ConnectedLineName": "Test",
            "Context": "from-internal",
        }
    )

    await hass.async_block_till_done()
    sensor = hass.states.get("sensor.100_dtmf_received")
    assert sensor is not None
    assert sensor.state != "unknown"

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()
