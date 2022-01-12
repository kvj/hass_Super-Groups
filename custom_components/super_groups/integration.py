from homeassistant.helpers import entity_registry, device_registry

from .groups import Coordinator
from .constants import DOMAIN

import logging
import secrets

_LOGGER = logging.getLogger(__name__)

def entries_by_domain(hass, entry, domain):
    result = []
    data = entry.as_dict().get("data", {})
    for (key, value) in data.items():
        if value.get("domain", "") == domain:
            result.append((key, value))
    return result

_ICON_MAP = {
    "light": "mdi:lightbulb",
    "binary_sensor": "mdi:checkbox-marked-circle",
    "switch": "mdi:flash"
}

def entries_from_registry(hass, entity_reg, device_reg, entry, id):
    coordinator = get_coordinator(hass, entry, id)
    entity_id = entity_reg.async_get_entity_id(coordinator.domain, DOMAIN, coordinator.unique_id) if coordinator else None
    entity = entity_reg.async_get(entity_id) if entity_id else None
    device = device_reg.async_get(entity.device_id) if entity and entity.device_id else None
    return entity, device

def make_items_list(entity_reg, device_reg, items):
    result = []
    for item in items.get("entity_id", []):
        if entity := entity_reg.async_get(item):
            result.append({
                "id": item, 
                "title": entity.name or entity.original_name, 
                "type": "entity"
            })
    for item in items.get("device_id", []):
        if entity := device_reg.async_get(item):
            result.append({
                "id": item, 
                "title": entity.name_by_user or entity.name, 
                "type": "device"
            })
    return result

async def async_all_entries(hass, entry):
    result = []
    entity_reg = await entity_registry.async_get_registry(hass)
    device_reg = device_registry.async_get(hass)
    data = entry.as_dict().get("data", {})
    for (key, value) in data.items():
        entity, device = entries_from_registry(hass, entity_reg, device_reg, entry, key)
        title = (device.name_by_user if device.name_by_user else device.name) if device else value.get("title", key)
        items = value.get("items", {})
        result.append({
            "id": key,
            "title": title,
            "domain": value.get("domain"),
            "all_on": value.get("all_on", False),
            "icon": entity.icon if entity and entity.icon else _ICON_MAP.get(value.get("domain")),
            "entry": items,
            "members": make_items_list(entity_reg, device_reg, items)
        })
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
    entity_reg = await entity_registry.async_get_registry(hass)
    device_reg = device_registry.async_get(hass)
    entity, device = entries_from_registry(hass, entity_reg, device_reg, entry, entry_id)
    if entity:
        entity_reg.async_remove(entity.entity_id)
    if device:
        device_reg.async_remove_device(device.id)
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
    if len(entries) == 0:
        return None
    return next((x for x in get_config_entries(hass) if x.entry_id == entry_id), entries[0])

