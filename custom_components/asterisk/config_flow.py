"""Config flow to configure Asterisk integration"""

import logging
from typing import Any

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

    async def async_step_hassio(self, discovery_info):
        """Handle supervisor discovery."""
        self._hassio_discovery = discovery_info.config
        await self._async_handle_discovery_without_unique_id()

        return await self.async_step_hassio_confirm()
    
    async def async_step_hassio_confirm(self, user_input):
        """Confirm Supervisor discovery."""
        if user_input is None and self._hassio_discovery is not None:
            return self.async_show_form(
                step_id="hassio_confirm",
                description_placeholders={"addon": self._hassio_discovery["addon"]},
            )

        return await self.async_step_user()

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