"""Config flow to configure Asterisk integration"""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AsteriskConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Asterisk integration config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow"""
        self._host = vol.UNDEFINED
        self._port = vol.UNDEFINED
        self._username = vol.UNDEFINED
        self._password = vol.UNDEFINED

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            self._host = user_input["host"]
            self._port = user_input["port"]
            self._username = user_input["username"]
            self._password = user_input["password"]

            # Steps for login checking and error handling needed here

            return self.async_create_entry(
                title=user_input[CONF_HOST],
                data=user_input,
                description_placeholders={"docs_url": "asterisk.com"},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): cv.string,
                    vol.Optional(CONF_PORT, default="5038"): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={"docs_url": "asterisk.com"},
            errors=errors,
        )

    async def async_step_import(self, user_input):
        """Import a config flow from configuration."""

        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        # code for validating login information and error handling needed

        return self.async_create_entry(
            title=f"{host} (from configuration)",
            data={
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_USERNAME: username,
                CONF_PASSWORD: password
            },
        )