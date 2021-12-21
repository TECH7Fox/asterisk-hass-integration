"""Astisk Component."""
import logging
import json
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
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from shutil import Error, copy, copyfile
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

def register_static_path(app: web.Application, url_path: str, path):
    """Register static path with CORS for Chromecast"""

    async def serve_file(request):
        return web.FileResponse(path)

    route = app.router.add_route("GET", url_path, serve_file)
    if 'allow_all_cors' in app:
        app['allow_all_cors'](route)
    elif 'allow_cors' in app:
        app['allow_cors'](route)

def handle_asterisk_event(event, manager, hass, entry):
    # _LOGGER.error("event.headers: " + json.dumps(event.headers))

    device = {
        "extension": event.get_header("ObjectName"),
        "status": event.get_header("Status"),
        "tech": event.get_header("Channeltype")
    }

    hass.data[DOMAIN][entry.entry_id]["devices"].append(device)


async def async_setup_entry(hass, entry):
    """Your controller/hub specific code."""

    async def handle_hangup(call) -> None:
        "Handle the service call."

        extension = call.data.get("extension")

        hass.data[DOMAIN][entry.entry_id]["manager"].hangup(extension)

    hass.services.async_register(DOMAIN, "hangup", handle_hangup)

    manager = asterisk.manager.Manager()

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    _LOGGER.info("Asterisk component is now set up")
    try:
        manager.connect(host, port)
        manager.login(username, password)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            "devices": [],
            "manager": manager
        }
        _LOGGER.info("Successfully connected to Asterisk server")
        manager.register_event("PeerEntry", lambda event, manager=manager, hass=hass, entry=entry: handle_asterisk_event(event, manager, hass, entry))
        manager.sippeers()

        sleep(5)
        
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                entry, "sensor"
            )
        )

        # make folders if they don't exists.
        try:
            os.mkdir('/config/www')
        except OSError as error:
            _LOGGER.warning(error)

        try:
            os.mkdir('/config/www/asterisk')
        except OSError as error:
            _LOGGER.warning(error)

        try:
            copyfile('/config/custom_components/asterisk/www/sipjs-card.js', '/config/www/asterisk/sipjs-card.js')
            copyfile('/config/custom_components/asterisk/www/ringtone.mp3', '/config/www/asterisk/ringtone.mp3')
            copyfile('/config/custom_components/asterisk/www/ringback.mp3', '/config/www/asterisk/ringback.mp3')
        except IOError as error:
            _LOGGER.error(error)
            

        url_path = '/asterisk/sipjs-card.js'
        path = Path(__file__).parent / 'www/sipjs-card.js'
        register_static_path(hass.http.app, url_path, path)

        resources: ResourceStorageCollection = hass.data['lovelace']['resources']

        await resources.async_get_info()

        exists = False

        for item in resources.async_items():
            if item['url'] == '/asterisk/sipjs-card.js':
                exists = True
        
        if not exists:
            try:
                await resources.async_create_item({'res_type': 'module', 'url': '/asterisk/sipjs-card.js'})
            except Exception as error:
               _LOGGER.warning("Failed to add resource. Add /asterisk/sipjs-card.js manually.")
        else:
            _LOGGER.info("Resource already exists")

        return True
    except asterisk.manager.ManagerException as exception:
        _LOGGER.error("Error connecting to Asterisk: %s", exception.args[1])
        _LOGGER.error(f"Host: {host}, Port: {port}, Username: {username}, Password: {password}")
        return False