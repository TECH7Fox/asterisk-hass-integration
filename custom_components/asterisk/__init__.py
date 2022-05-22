"""Astisk Component."""
import logging
import json
from operator import truediv
from typing import Any

import asterisk.manager
import voluptuous as vol
from time import sleep
import os

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from aiohttp import web
from pathlib import Path
from homeassistant.helpers.typing import HomeAssistantType
from shutil import Error, copy, copyfile
from .const import DOMAIN

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5038
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "manager"

DATA_ASTERISK = "asterisk_manager"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.port,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)

def handle_shutdown(event, manager, hass, entry):
    _LOGGER.error("Asterisk shutting down.")

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    while True:
        sleep(30)
        try:
            manager.close()
            manager.connect(host, port)
            manager.login(username, password)
            _LOGGER.info("Succesfully reconnected.")
            break
        except asterisk.manager.ManagerException as exception:
            _LOGGER.error("Error reconnecting to Asterisk: %s", exception.args[1])

def handle_asterisk_event(event, manager, hass, entry):

    if (event.get_header("Event") == "EndpointList"):
        device = {
            "extension": event.get_header("ObjectName"),
            "status": event.get_header("DeviceState"),
            "tech": "PJSIP"
        }
    else:
        device = {
            "extension": event.get_header("ObjectName"),
            "status": event.get_header("DeviceState"),
            "tech": event.get_header("Channeltype")
        }

    hass.data[DOMAIN][entry.entry_id]["devices"].append(device)

async def async_setup_entry(hass, entry):
    """Your controller/hub specific code."""

    async def hangup_service(call) -> None:
        "Handle the service call."

        response = hass.data[DOMAIN][entry.entry_id]["manager"].hangup(
            call.data.get("channel")
        )
        
        _LOGGER.info("Hangup response: ", response)

    async def originate_service(call) -> None:
        "Handle the service call."

        response = hass.data[DOMAIN][entry.entry_id]["manager"].originate(
            call.data.get("channel"),
            call.data.get("exten"),
            call.data.get("context"),
            call.data.get("priority"),
            call.data.get("timeout") * 1000,
            call.data.get("application"),
            call.data.get("data"),
            call.data.get("caller_id"),
            True, # run_async
            call.data.get("earlymedia"),
            call.data.get("account"),
            call.data.get("variables")
        )

        _LOGGER.info("Originate response: ", response)

    hass.services.async_register(DOMAIN, "hangup", hangup_service)
    hass.services.async_register(DOMAIN, "originate", originate_service)

    manager = asterisk.manager.Manager()

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    try:
        manager.connect(host, port)
        manager.login(username, password)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            "devices": [],
            "manager": manager
        }
        _LOGGER.info("Successfully connected to Asterisk server")

        manager.register_event("Shutdown", lambda event, manager=manager, hass=hass, entry=entry: handle_shutdown(event, manager, hass, entry))
        manager.register_event("PeerEntry", lambda event, manager=manager, hass=hass, entry=entry: handle_asterisk_event(event, manager, hass, entry))
        manager.register_event("EndpointList", lambda event, manager=manager, hass=hass, entry=entry: handle_asterisk_event(event, manager, hass, entry))
        manager.sippeers()                                    # Get all SIP peers
        manager.send_action({"Action": "PJSIPShowEndpoints"}) # Get all PJSIP endpoints

        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                entry, "sensor"
            )
        )

        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                entry, "binary_sensor"
            )
        )

        return True
    except asterisk.manager.ManagerException as exception:
        _LOGGER.error("Error connecting to Asterisk: %s", exception.args[1])
        return False
