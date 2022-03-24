from homeassistant.components.binary_sensor import BinarySensorEntity

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    entities = []
    for (key, value) in entries_by_domain(hass, entry, "binary_sensor"):
        c = set_coordinator(hass, entry, key, value)
        await c.async_config_entry_first_refresh()
        entities.append(Entity(c))

    add_entities(entities)
    return True

class Entity(BaseEntity, BinarySensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_domain = "binary_sensor"
