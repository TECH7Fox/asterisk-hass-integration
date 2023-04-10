from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult, AbortFlow
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
import voluptuous as vol
import logging
from .const import DOMAIN
from asterisk.ami import AMIClient

_LOGGER = logging.getLogger(__name__)

class AsteriskConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Asterisk."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    reauth_entry: ConfigEntry | None = None

    async def _show_form(self, errors: dict[str, str] | None = None) -> FlowResult:
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=5038): int,
                vol.Required(CONF_USERNAME, default="admin"): str,
                vol.Optional(CONF_PASSWORD, default=""): str,
            }),
            errors=errors or {},
        )
    
    async def _test_ami(self, host, port, username, password):
        """Tests the AMI connection."""        
        errors = {}
        client = AMIClient(address=host, port=port)
        try:
            future = client.login(username=username, secret=password)
            if future.response.is_error():
                _LOGGER.debug("Failed to connect to AMI: %s", future.response.keys['Message'])
                errors["base"] =  f"invalid_auth"

            client.logoff()
            client.disconnect()
        except Exception as e:
            _LOGGER.debug("Failed to connect to AMI: %s", e)
            errors["base"] = f"cannot_connect"

        return errors

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return await self._show_form()

        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        errors = {}

        await self.async_set_unique_id(f"{host}:{port}")
        
        if self.reauth_entry is None:
            try:
                self._abort_if_unique_id_configured()
            except AbortFlow:
                errors["base"] = f"already_configured"
                return await self._show_form(errors)

        result = await self._test_ami(host, port, username, password)
        if result:
            return await self._show_form(result)

        return self.async_create_entry(title=f"AMI {host}:{port}", data=user_input)

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    #################### Reauth ####################

    reauth_entry: ConfigEntry | None = None

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({
                    vol.Required(CONF_USERNAME, default="admin"): str,
                    vol.Optional(CONF_PASSWORD, default=""): str,
                }),
            )
        
        user_input[CONF_HOST] = self.reauth_entry.data[CONF_HOST]
        user_input[CONF_PORT] = self.reauth_entry.data[CONF_PORT]
        
        result = await self._test_ami(
            user_input[CONF_HOST],
            user_input[CONF_PORT],
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD]
        )
        if result:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({
                    vol.Required(CONF_USERNAME, default="admin"): str,
                    vol.Optional(CONF_PASSWORD, default=""): str,
                }),
                errors=result,
            )
        
        self.hass.config_entries.async_update_entry(self.reauth_entry, data=user_input)
        await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
        return self.async_abort(reason="reauth_successful")
