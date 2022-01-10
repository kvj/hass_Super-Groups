from .groups import Coordinator
from .constants import DOMAIN

import logging
import secrets

_LOGGER = logging.getLogger(__name__)

def entries_by_domain(hass, entry, domain):
    result = []
    data = entry.as_dict().get("data", {})
    for (key, value) in data.items():
        if value.get("domain", "") == domain or domain == None:
            result.append((key, value))
    return result

async def add_new_entry(hass, entry, request):
    data = entry.as_dict().get("data", {})
    _id = secrets.token_hex(8)
    data[_id] = {
        "title": request["title"],
        "all_on": request["all_on"],
        "domain": request["domain"],
        "items": request["items"]
    }
    await reload_config_entry(hass, entry, data)
    return _id

async def update_entry(hass, entry, entry_id, request):
    data = entry.as_dict().get("data", {})
    if entry_id in data:
        data[entry_id] = {
            **data[entry_id],
            "all_on": request["all_on"],
            "items": request["items"]
        }
        await reload_config_entry(hass, entry, data)

async def remove_entry(hass, entry, entry_id):
    data = entry.as_dict().get("data", {})
    if entry_id in data:
        del data[entry_id]
        await reload_config_entry(hass, entry, data)

async def reload_config_entry(hass, entry, data):
    hass.config_entries.async_update_entry(entry, data=data)
    await hass.config_entries.async_reload(entry.entry_id)

def set_coordinator(hass, entry, id, data):
    instance = Coordinator(hass, entry, {
        **data, 
        "id": id
    })
    hass.data[DOMAIN]["entries"][entry.entry_id][id] = instance
    return instance

def get_coordinator(hass, entry, id):
    return hass.data[DOMAIN]["entries"][entry.entry_id].get(id)

def get_config_entries(hass):
    return hass.config_entries.async_entries(DOMAIN)

def get_config_entry(hass, entry_id):
    entries = get_config_entries(hass)
    return next((x for x in get_config_entries(hass) if x.entry_id == entry_id), entries[0])

