"""Asterisk platform."""
import logging
from custom_components.asterisk.server import AsteriskServer
from custom_components.asterisk.extension import AsteriskExtension, AsteriskCallee, CurrentChannelSensor, RegisteredSensor

import voluptuous as vol
import json

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN, SW_VERSION
from homeassistant.const import CONF_HOST

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["asterisk"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required("extension"): cv.string})

async def async_setup_entry(hass, entry, async_add_entities):
    """Setting up every extension."""
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]

    entities = [AsteriskServer(hass, entry)]
    for device in devices:
        _LOGGER.info(f"Setting up asterisk extension device for extension {device['tech']}{device['extension']}")
        entities.append(AsteriskExtension(hass, device["status"], device["extension"], device["tech"], entry))
        entities.append(AsteriskCallee(hass, device["extension"], device["tech"], entry))
        entities.append(CurrentChannelSensor(hass, device["extension"], device["tech"], entry))
        entities.append(RegisteredSensor(hass, device["extension"], device["tech"], entry))
    async_add_entities(entities, True)