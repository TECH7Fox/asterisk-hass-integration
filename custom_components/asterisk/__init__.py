"""Astisk Component."""
import logging

import asterisk.manager
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv

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

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Your controller/hub specific code."""

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
        return True
    except asterisk.manager.ManagerException as exception:
        _LOGGER.error("Error connecting to Asterisk: %s", exception.args[1])
        return False
