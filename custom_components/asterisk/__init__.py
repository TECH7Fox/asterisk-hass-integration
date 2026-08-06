import asyncio
import logging
import re

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

from .const import (
    AUTO_RECONNECT,
    CLIENT,
    DOMAIN,
    EVENT_USER_EVENT,
    PJSIP_LOADED,
    PLATFORMS,
    SIP_LOADED,
)

_LOGGER = logging.getLogger(__name__)


def normalize_ami_key(key: str) -> str:
    """Normalize AMI event keys to Home Assistant event data keys."""
    key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return key.replace("-", "_").lower()


def ami_user_event_data(event: Event) -> dict:
    """Convert an AMI UserEvent to Home Assistant event data."""
    return {
        "event": event.name,
        **{normalize_ami_key(key): value for key, value in event.keys.items()},
    }


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

    def devices_complete(event: Event, **kwargs):
        sip_loaded = hass.data[DOMAIN][entry.entry_id][SIP_LOADED]
        pjsip_loaded = hass.data[DOMAIN][entry.entry_id][PJSIP_LOADED]
        if event.name == "PeerlistComplete":
            _LOGGER.debug("SIP loaded.")
            sip_loaded = True
            hass.data[DOMAIN][entry.entry_id][SIP_LOADED] = True
        elif event.name == "EndpointListComplete":
            _LOGGER.debug("PJSIP loaded.")
            pjsip_loaded = True
            hass.data[DOMAIN][entry.entry_id][PJSIP_LOADED] = True
        
        if sip_loaded and pjsip_loaded:
            _LOGGER.debug("Both SIP and PJSIP loaded. Loading platforms.")
            asyncio.run_coroutine_threadsafe(
                hass.config_entries.async_forward_entry_setups(entry, PLATFORMS),
                hass.loop
            )

    def forward_user_event(event: Event, **kwargs):
        """Forward AMI UserEvent events to the Home Assistant event bus."""
        event_data = ami_user_event_data(event)
        _LOGGER.debug("Forwarding AMI UserEvent: %s", event_data)
        hass.loop.call_soon_threadsafe(
            hass.bus.async_fire,
            EVENT_USER_EVENT,
            event_data,
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
    }
    hass.services.async_register(DOMAIN, "send_action", send_action_service)

    client.add_event_listener(forward_user_event, white_list=["UserEvent"])

    client.add_event_listener(create_SIP_device, white_list=["PeerEntry"])
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
