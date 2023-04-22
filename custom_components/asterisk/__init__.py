import asyncio
import logging

from asterisk.ami import AMIClient, AutoReconnect, Event, SimpleAction
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import AUTO_RECONNECT, CLIENT, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup up a config entry."""

    def create_PJSIP_device(event: Event, **kwargs):
        _LOGGER.debug("Creating PJSIP device: %s", event)
        device = {
            "extension": event["ObjectName"],
            "tech": "PJSIP",
            "status": event["DeviceState"],
        }
        hass.data[DOMAIN][entry.entry_id][CONF_DEVICES].append(device)

    # def create_SIP_device(event: Event, **kwargs):
    #     _LOGGER.debug("Creating SIP device: %s", event)
    #     device = {
    #         "extension": event["ObjectName"],
    #         "tech": "SIP",
    #         "status": event["Status"],
    #     }
    #     hass.data[DOMAIN][entry.entry_id][CONF_DEVICES].append(device)

    def devices_complete(event: Event, **kwargs):
        _LOGGER.debug("Done getting devices. Loading platforms.")
        for component in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, component)
            )

    async def send_action_service(call) -> None:
        "Send action service."

        action = SimpleAction(call.data.get("action"), **call.data.get("parameters"))
        _LOGGER.debug("Sending action: %s", action)

        try:
            f = hass.data[DOMAIN][entry.entry_id][CLIENT].send_action(action)
            _LOGGER.debug("Action response: %s", f.response)
        except BrokenPipeError:
            _LOGGER.warning("Failed to send action: AMI Disconnected")

    client = AMIClient(
        address=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        timeout=10,
    )
    auto_reconnect = AutoReconnect(client, delay=3)
    try:
        future = client.login(
            username=entry.data[CONF_USERNAME],
            secret=entry.data[CONF_PASSWORD],
        )
        _LOGGER.debug("Login response: %s", future.response)
        if future.response.is_error():
            raise ConfigEntryAuthFailed(future.response.keys["Message"])
    except ConfigEntryAuthFailed:
        raise
    except Exception as e:
        raise ConfigEntryNotReady(e)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        CLIENT: client,
        AUTO_RECONNECT: auto_reconnect,
        CONF_DEVICES: [],
    }
    hass.services.async_register(DOMAIN, "send_action", send_action_service)

    # TODO: Add support for SIP
    # client.add_event_listener(create_SIP_device, white_list=["PeerEntry"])
    # client.add_event_listener(devices_complete, white_list=["PeerlistComplete"])
    # client.send_action(SimpleAction("SIPpeers"))

    # Create self._sip_loaded and self._pjsip_loaded
    # If action fails because module is not loaded, set to True

    client.add_event_listener(create_PJSIP_device, white_list=["EndpointList"])
    client.add_event_listener(devices_complete, white_list=["EndpointListComplete"])
    client.send_action(SimpleAction("PJSIPShowEndpoints"))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[CLIENT]

    client.logoff()
    client.disconnect()

    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    return await async_setup_entry(hass, entry)
