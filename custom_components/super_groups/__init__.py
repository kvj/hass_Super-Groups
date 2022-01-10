from __future__ import annotations

from .integration import (get_config_entry, get_config_entries,
                          entries_by_domain, add_new_entry, update_entry, remove_entry)

from .constants import DOMAIN, PLATFORMS
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.components import websocket_api
from .frontend import locate_dir

import voluptuous as vol

import logging
from copy import copy

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    _LOGGER.debug("Setup platform: %s", entry)
    hass.data[DOMAIN]["entries"][entry.entry_id] = dict()
    entry.async_on_unload(entry.add_update_listener(update_listener))
    for p in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, p))
    return True


async def update_listener(hass, entry):
    pass
    # await get_coordinator(hass, entry).async_request_refresh()


async def async_unload_entry(hass, entry):
    for p in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, p)
    hass.data[DOMAIN]["entries"].pop(entry.entry_id)
    return True


async def async_setup(hass, config) -> bool:
    hass.data[DOMAIN] = dict(data=copy(config.get(DOMAIN, {})), entries={})
    _LOGGER.debug(f"__init__::async_setup: {config}, {locate_dir}")
    hass.http.register_static_path(
        "/super_groups_ui", "%s/dist" % (locate_dir()), cache_headers=False)
    await async_register_panel(
        hass,
        "super_groups",
        "super-groups-panel",
        sidebar_title="Super Groups",
        sidebar_icon="mdi:hexagon-multiple",
        module_url="/super_groups_ui/index.js",
        embed_iframe=False,
        require_admin=True
    )
    hass.components.websocket_api.async_register_command(ws_get_entries)
    hass.components.websocket_api.async_register_command(ws_add_entry)
    hass.components.websocket_api.async_register_command(ws_update_entry)
    hass.components.websocket_api.async_register_command(ws_remove_entry)
    return True

_ICON_MAP = {
    "light": "mdi:lightbulb",
    "binary_sensor": "mdi:checkbox-marked-circle",
    "switch": "mdi:flash"
}


@websocket_api.websocket_command({
    vol.Required("type"): "super_groups/get_entries",
    vol.Optional("config_id"): str,
})
@websocket_api.async_response
async def ws_get_entries(hass, connection, msg: dict):
    _LOGGER.debug("ws_get_entries: %s", msg)
    entry = get_config_entry(hass, msg.get("config_id"))
    all_entries = get_config_entries(hass)
    groups = entries_by_domain(hass, entry, None)
    connection.send_result(msg["id"], {
        "items": [{
            "id": x[0],
            "title": x[1].get("title", x[0]),
            "icon": _ICON_MAP.get(x[1]["domain"]),
            "domain": x[1]["domain"],
            "all_on": x[1]["all_on"],
            "entry": x[1]["items"],
        } for x in groups],
        "configs": [{
            "id": x.entry_id,
            "title": x.title,
            "selected": x.entry_id == entry.entry_id
        } for x in all_entries]
    })

_ITEM_SCHEMA = vol.Schema({
    vol.Required("area_id"): [str],
    vol.Required("device_id"): [str],
    vol.Required("entity_id"): [str],
})


@websocket_api.websocket_command({
    vol.Required("type"): "super_groups/add_entry",
    vol.Optional("config_id"): str,
    vol.Required("title"): str,
    vol.Required("domain"): str,
    vol.Required("all_on"): bool,
    vol.Required("items"): _ITEM_SCHEMA
})
@websocket_api.async_response
async def ws_add_entry(hass, connection, msg: dict):
    _LOGGER.debug("ws_add_entry: %s", msg)
    entry = get_config_entry(hass, msg.get("config_id"))
    new_id = await add_new_entry(hass, entry, msg)
    connection.send_result(msg["id"], {
        "id": new_id
    })


@websocket_api.websocket_command({
    vol.Required("type"): "super_groups/update_entry",
    vol.Optional("config_id"): str,
    vol.Required("entry_id"): str,
    vol.Required("all_on"): bool,
    vol.Required("items"): _ITEM_SCHEMA
})
@websocket_api.async_response
async def ws_update_entry(hass, connection, msg: dict):
    _LOGGER.debug("ws_add_entry: %s", msg)
    entry = get_config_entry(hass, msg.get("config_id"))
    await update_entry(hass, entry, msg.get("entry_id"), msg)
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command({
    vol.Required("type"): "super_groups/remove_entry",
    vol.Optional("config_id"): str,
    vol.Required("entry_id"): str
})
@websocket_api.async_response
async def ws_remove_entry(hass, connection, msg: dict):
    _LOGGER.debug("ws_remove_entry: %s", msg)
    entry = get_config_entry(hass, msg.get("config_id"))
    await remove_entry(hass, entry, msg.get("entry_id"))
    connection.send_result(msg["id"], {})
