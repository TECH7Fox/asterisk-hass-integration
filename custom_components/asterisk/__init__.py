"""Astisk Component."""
import logging
import json
from typing import Any

import asterisk.manager
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5038
DEFAULT_USERNAME = "manager"
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

def handle_asterisk_event(event, manager, hass, entry):
    _LOGGER.error("event.headers: " + json.dumps(event.headers))
    _LOGGER.error("ObjectName: " + event.get_header("ObjectName"))
    _extension = event.get_header("ObjectName")
    entry.title=f"{_extension} (from configuration)",
    entry.data={
        "extension": _extension
    }
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

def setup(hass, config):
    """Your controller/hub specific code."""

    if DOMAIN not in config:
        # There is an entry and nothing in configuration.yaml
        _LOGGER.info("no Asterisk config in configuration.yaml")
        return True

    _LOGGER.error("SETTING UP FROM SETUP")

    manager = asterisk.manager.Manager()

    host = config[DOMAIN].get(CONF_HOST, DEFAULT_HOST)
    port = config[DOMAIN].get(CONF_PORT, DEFAULT_PORT)
    username = config[DOMAIN].get(CONF_USERNAME, DEFAULT_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD, DEFAULT_PASSWORD)
    _LOGGER.info("Asterisk component is now set up")
    try:
        manager.connect(host, port)
        manager.login(username, password)
        hass.data[DOMAIN] = manager
        _LOGGER.info("Successfully connected to Asterisk server")
        manager.register_event("PeerEntry", handle_asterisk_event)
        manager.sippeers()
        return True
    except asterisk.manager.ManagerException as exception:
        _LOGGER.error("Error connecting to Asterisk: %s", exception.args[1])
        _LOGGER.error(f"Host: {host}, Port: {port}, Username: {username}, Password: {password}")
        return False

async def async_setup_entry(hass, entry):
    """Your controller/hub specific code."""

    _LOGGER.error("SETTING UP FROM ENTRY")

    manager = asterisk.manager.Manager()

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    _LOGGER.info("Asterisk component is now set up")
    try:
        manager.connect(host, port)
        manager.login(username, password)
        hass.data[DOMAIN] = manager
        _LOGGER.info("Successfully connected to Asterisk server")
        manager.register_event("PeerEntry", lambda event, manager=manager, hass=hass, entry=entry: handle_asterisk_event(event, manager, hass, entry))
        manager.sippeers()
        return True
    except asterisk.manager.ManagerException as exception:
        _LOGGER.error("Error connecting to Asterisk: %s", exception.args[1])
        _LOGGER.error(f"Host: {host}, Port: {port}, Username: {username}, Password: {password}")
        return False