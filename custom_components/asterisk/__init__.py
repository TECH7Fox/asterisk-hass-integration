import asyncio
import logging
import threading
import uuid
from typing import Any, Dict, Optional, Tuple

import voluptuous as vol
from asterisk.ami import AMIClient, AutoReconnect, Event, SimpleAction
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)

try:
    from homeassistant.exceptions import ServiceValidationError
except ImportError:  # pragma: no cover - compatibility fallback for older HA
    ServiceValidationError = HomeAssistantError

try:
    from homeassistant.core import ServiceResponse, SupportsResponse
except ImportError:  # pragma: no cover - compatibility fallback for older HA
    ServiceResponse = Dict[str, Any]
    SupportsResponse = None

from .const import AUTO_RECONNECT, CLIENT, DOMAIN, PLATFORMS, SIP_LOADED, PJSIP_LOADED

_LOGGER = logging.getLogger(__name__)

CONF_ACTION = "action"
CONF_PARAMETERS = "parameters"
CONF_ENTRY_ID = "entry_id"
CONF_CONFERENCE = "conference"
CONF_TIMEOUT = "timeout"
DATA_SERVICES_REGISTERED = "_services_registered"
DEFAULT_ACTION_TIMEOUT = 10
SERVICE_GET_CONFERENCE_ROOMS = "get_conference_rooms"
SERVICE_SEND_ACTION = "send_action"
NO_ACTIVE_CONFERENCES_MARKERS = ("no active", "conference")

SEND_ACTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACTION): str,
        vol.Optional(CONF_PARAMETERS, default={}): dict,
        vol.Optional(CONF_ENTRY_ID): str,
    }
)
GET_CONFERENCE_ROOMS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CONFERENCE): str,
        vol.Optional(CONF_ENTRY_ID): str,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_ACTION_TIMEOUT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=60)
        ),
    }
)


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up the Asterisk integration."""
    _async_setup_services(hass)
    return True


def _iter_loaded_entries(hass: HomeAssistant):
    """Yield loaded config entry payloads."""
    for entry_id, data in hass.data.get(DOMAIN, {}).items():
        if isinstance(data, dict) and CLIENT in data:
            yield entry_id, data


def _resolve_service_entry(
    hass: HomeAssistant, requested_entry_id: Optional[str]
) -> Tuple[str, dict]:
    """Resolve which config entry a service call should use."""
    loaded_entries = dict(_iter_loaded_entries(hass))

    if not loaded_entries:
        raise ServiceValidationError("No loaded Asterisk config entries found.")

    if requested_entry_id is None:
        if len(loaded_entries) == 1:
            return next(iter(loaded_entries.items()))

        raise ServiceValidationError(
            "Multiple Asterisk config entries are loaded. Provide entry_id."
        )

    if requested_entry_id not in loaded_entries:
        raise ServiceValidationError(
            f"Asterisk config entry '{requested_entry_id}' is not loaded."
        )

    return requested_entry_id, loaded_entries[requested_entry_id]


def _message_to_dict(message: Any) -> dict:
    """Convert AMI responses/events to plain dictionaries."""
    data = dict(getattr(message, "keys", {}) or {})
    name = getattr(message, "name", None)

    if name is not None:
        data.setdefault("Event", name)

    if hasattr(message, "is_error"):
        try:
            data["success"] = not message.is_error()
        except Exception:  # pragma: no cover - defensive for third-party objects
            pass

    return data


def _response_message(response: Any) -> str:
    """Extract the most useful AMI response message."""
    response_data = _message_to_dict(response)
    return (
        response_data.get("Message")
        or response_data.get("Response")
        or "Unknown AMI response"
    )


def _is_no_active_conferences_response(response: Any) -> bool:
    """Return True when Asterisk reports an empty ConfBridge room list."""
    try:
        if not response.is_error():
            return False
    except Exception:  # pragma: no cover - defensive for third-party objects
        return False

    response_message = _response_message(response).lower()
    return all(marker in response_message for marker in NO_ACTIVE_CONFERENCES_MARKERS)


def _coerce_int(value: Any) -> Any:
    """Convert numeric strings to integers when possible."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _yes_no_to_bool(value: Any) -> Any:
    """Convert Asterisk Yes/No values to booleans."""
    if value == "Yes":
        return True
    if value == "No":
        return False
    return value


def _normalize_confbridge_room(room: dict) -> dict:
    """Normalize a ConfBridge room payload for Home Assistant consumers."""
    return {
        "conference": room.get("Conference"),
        "parties": _coerce_int(room.get("Parties")),
        "marked": _coerce_int(room.get("Marked")),
        "locked": _yes_no_to_bool(room.get("Locked")),
        "muted": _yes_no_to_bool(room.get("Muted")),
    }


def _remove_event_listeners(client: AMIClient, listeners) -> None:
    """Remove AMI event listeners when the client supports it."""
    remove_listener = getattr(client, "remove_event_listener", None)
    if not callable(remove_listener):
        return

    for listener in listeners:
        if listener is None:
            continue
        try:
            remove_listener(listener)
        except Exception:  # pragma: no cover - best effort cleanup
            _LOGGER.debug("Failed to remove temporary AMI event listener")


async def _async_send_action(
    hass: HomeAssistant,
    client: AMIClient,
    action: SimpleAction,
    disconnected_message: str,
):
    """Send a synchronous AMI action without blocking the HA event loop."""
    try:
        return await hass.async_add_executor_job(client.send_action, action)
    except BrokenPipeError as err:
        raise HomeAssistantError(disconnected_message) from err


def _async_setup_services(hass: HomeAssistant) -> None:
    """Register Home Assistant services for the integration."""
    hass.data.setdefault(DOMAIN, {})
    if hass.data[DOMAIN].get(DATA_SERVICES_REGISTERED):
        return

    async def send_action_service(call: ServiceCall):
        """Send an AMI action, optionally returning the immediate response."""
        entry_id, entry_data = _resolve_service_entry(
            hass, call.data.get(CONF_ENTRY_ID)
        )
        action = SimpleAction(
            call.data[CONF_ACTION], **(call.data.get(CONF_PARAMETERS) or {})
        )
        _LOGGER.debug("Sending action: %s", action)

        future = await _async_send_action(
            hass,
            entry_data[CLIENT],
            action,
            "Failed to send action: AMI disconnected",
        )
        response = future.response
        _LOGGER.debug("Action response: %s", response)

        if response.is_error():
            raise HomeAssistantError(_response_message(response))

        if getattr(call, "return_response", False):
            return {
                "entry_id": entry_id,
                "response": _message_to_dict(response),
            }

        return None

    async def get_conference_rooms_service(call: ServiceCall) -> ServiceResponse:
        """Return the active ConfBridge conference rooms."""
        entry_id, entry_data = _resolve_service_entry(
            hass, call.data.get(CONF_ENTRY_ID)
        )
        client = entry_data[CLIENT]
        requested_conference = call.data.get(CONF_CONFERENCE)
        timeout = call.data[CONF_TIMEOUT]
        action_id = f"ha-confbridge-{uuid.uuid4()}"
        action = SimpleAction("ConfbridgeListRooms", ActionID=action_id)
        listeners = []
        rooms = []
        rooms_lock = threading.Lock()
        completion = hass.loop.create_future()
        response = None

        def handle_room(event: Event, **kwargs):
            """Collect each ConfBridge room event."""
            with rooms_lock:
                rooms.append(_normalize_confbridge_room(_message_to_dict(event)))

        def handle_complete(event: Event, **kwargs):
            """Resolve once the room listing is complete."""

            def _finish():
                if not completion.done():
                    completion.set_result(_message_to_dict(event))

            hass.loop.call_soon_threadsafe(_finish)

        try:
            listeners.append(
                client.add_event_listener(
                    handle_room,
                    white_list=["ConfbridgeListRooms"],
                    ActionID=action_id,
                )
            )
            listeners.append(
                client.add_event_listener(
                    handle_complete,
                    white_list=["ConfbridgeListRoomsComplete"],
                    ActionID=action_id,
                )
            )

            future = await _async_send_action(
                hass,
                client,
                action,
                "Failed to list conference rooms: AMI disconnected",
            )
            response = future.response
            _LOGGER.debug("ConfbridgeListRooms response: %s", response)

            if response.is_error():
                if _is_no_active_conferences_response(response):
                    complete = {
                        "Event": "ConfbridgeListRoomsComplete",
                        "ActionID": action_id,
                        "EventList": "Complete",
                        "ListItems": "0",
                    }
                else:
                    raise HomeAssistantError(_response_message(response))
            else:
                complete = await asyncio.wait_for(completion, timeout=timeout)
        except asyncio.TimeoutError as err:
            raise HomeAssistantError(
                "Timed out waiting for ConfbridgeListRoomsComplete"
            ) from err
        finally:
            _remove_event_listeners(client, listeners)

        with rooms_lock:
            room_list = list(rooms)

        result = {
            "entry_id": entry_id,
            "response": _message_to_dict(response),
            "complete": complete,
            "room_count": len(room_list),
            "rooms": room_list,
        }

        if requested_conference is not None:
            room = next(
                (
                    conference_room
                    for conference_room in room_list
                    if conference_room["conference"] == requested_conference
                ),
                None,
            )
            result.update(
                {
                    "conference": requested_conference,
                    "is_open": room is not None,
                    "room": room,
                }
            )

        return result

    send_action_kwargs = {"schema": SEND_ACTION_SCHEMA}
    get_conference_rooms_kwargs = {"schema": GET_CONFERENCE_ROOMS_SCHEMA}

    if SupportsResponse is not None:
        send_action_kwargs["supports_response"] = SupportsResponse.OPTIONAL
        get_conference_rooms_kwargs["supports_response"] = SupportsResponse.ONLY

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_ACTION,
        send_action_service,
        **send_action_kwargs,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_CONFERENCE_ROOMS,
        get_conference_rooms_service,
        **get_conference_rooms_kwargs,
    )
    hass.data[DOMAIN][DATA_SERVICES_REGISTERED] = True


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
    _async_setup_services(hass)

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
