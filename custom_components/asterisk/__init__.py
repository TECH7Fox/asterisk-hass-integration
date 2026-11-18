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

from .const import AUTO_RECONNECT, CLIENT, DOMAIN, PLATFORMS, SIP_LOADED, PJSIP_LOADED, SCCP_LOADED, IAX_LOADED

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

    def create_SIP_device(event: Event, **kwargs):
        _LOGGER.debug("Creating SIP device: %s", event)
        device = {
            "extension": event["ObjectName"],
            "tech": "SIP",
            "status": event["Status"],
        }
        hass.data[DOMAIN][entry.entry_id][CONF_DEVICES].append(device)

    def create_SCCP_device(event: Event, **kwargs):
        _LOGGER.debug("Creating SCCP device: %s", event)
        device = {
            "extension": event["Name"],
            "tech": "SCCP",
            "status": event["ObjectType"],
        }
        hass.data[DOMAIN][entry.entry_id][CONF_DEVICES].append(device)

    def create_IAX_device(event: Event, **kwargs):
        _LOGGER.debug("Creating IAX device: %s", event)
        device = {
            "extension": event["ObjectName"],
            "tech": "IAX",
            "status": event["Status"],
        }
        hass.data[DOMAIN][entry.entry_id][CONF_DEVICES].append(device)

    def devices_complete(event: Event, **kwargs):
        sip_loaded = hass.data[DOMAIN][entry.entry_id][SIP_LOADED]
        pjsip_loaded = hass.data[DOMAIN][entry.entry_id][PJSIP_LOADED]
        sccp_loaded = hass.data[DOMAIN][entry.entry_id][SCCP_LOADED]
        iax_loaded = hass.data[DOMAIN][entry.entry_id][IAX_LOADED]
        if sip_loaded == False and event.name == "PeerlistComplete":
            _LOGGER.debug("SIP loaded.")
            hass.data[DOMAIN][entry.entry_id][SIP_LOADED] = True
        elif pjsip_loaded == False and event.name == "EndpointListComplete":
            _LOGGER.debug("PJSIP loaded.")
            hass.data[DOMAIN][entry.entry_id][PJSIP_LOADED] = True
        elif sccp_loaded == False and event.name == "SCCPListLinesComplete":
            _LOGGER.debug("SCCP loaded.")
            hass.data[DOMAIN][entry.entry_id][SCCP_LOADED] = True
        elif iax_loaded == False and event.name == "PeerlistComplete":
            _LOGGER.debug("IAX loaded.")
            hass.data[DOMAIN][entry.entry_id][IAX_LOADED] = True

        if sip_loaded and pjsip_loaded and sccp_loaded and iax_loaded:
            _LOGGER.debug("SIP, PJSIP, SCCP and IAX loaded. Loading platforms.")
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
        SIP_LOADED: False,
        PJSIP_LOADED: False,
        SCCP_LOADED: False,
        IAX_LOADED: False,
    }
    hass.services.async_register(DOMAIN, "send_action", send_action_service)

    client.add_event_listener(create_SIP_device, white_list=["PeerEntry"], Channeltype='SIP')
    client.add_event_listener(devices_complete, white_list=["PeerlistComplete"])
    f = client.send_action(SimpleAction("SIPpeers"))
    if f.response.is_error():
        _LOGGER.debug("SIP module not loaded. Skipping SIP devices.")
        hass.data[DOMAIN][entry.entry_id][SIP_LOADED] = True

    client.add_event_listener(create_PJSIP_device, white_list=["EndpointList"])
    client.add_event_listener(devices_complete, white_list=["EndpointListComplete"])
    f = client.send_action(SimpleAction("PJSIPShowEndpoints"))
    if f.response.is_error():
       _LOGGER.debug("PJSIP module not loaded. Skipping PJSIP devices.")
       hass.data[DOMAIN][entry.entry_id][PJSIP_LOADED] = True

    client.add_event_listener(create_SCCP_device, white_list=["LineEntry"])
    client.add_event_listener(devices_complete, white_list=["SCCPListLinesComplete"])
    f = client.send_action(SimpleAction("SCCPListLines"))
    if f.response.is_error():
       _LOGGER.debug("SCCP module not loaded. Skipping SCCP devices.")
       hass.data[DOMAIN][entry.entry_id][SCCP_LOADED] = True

    client.add_event_listener(create_IAX_device, white_list=["PeerEntry"], Channeltype='IAX')
    client.add_event_listener(devices_complete, white_list=["PeerlistComplete"])
    f = client.send_action(SimpleAction("IAXpeerList"))
    if f.response.is_error():
        _LOGGER.debug("IAX module not loaded. Skipping IAX devices.")
        hass.data[DOMAIN][entry.entry_id][IAX_LOADED] = True

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
