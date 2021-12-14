"""Provides device automations for Asterisk servers and extensions."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.automation import (
    AutomationActionType,
    AutomationTriggerInfo,
)
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

DEVICE = "device"

TRIGGER_TYPES = {"extension_inuse", "extension_idle"}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)

async def async_get_triggers(hass, device_id):
    """Return a list of triggers."""

    device_registry = await hass.helpers.device_registry.async_get_registry()
    device = device_registry.async_get(device_id)

    triggers = []

    # Determine which triggers are supported by this device_id ...

    triggers.append({
        CONF_PLATFORM: "device",
        CONF_DOMAIN: "asterisk",
        CONF_DEVICE_ID: device_id,
        CONF_TYPE: "extension_inuse",
    })

    triggers.append({
        CONF_PLATFORM: "device",
        CONF_DOMAIN: "asterisk",
        CONF_DEVICE_ID: device_id,
        CONF_TYPE: "extension_idle",
    })

    return triggers

async def async_attach_trigger(hass, config, action, automation_info):
    """Attach a trigger."""
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: "asterisk_event",
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_TYPE: config[CONF_TYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, automation_info, platform_type="device"
    )