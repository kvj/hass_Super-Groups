from homeassistant.components.switch import SwitchEntity

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    entities = []
    for (key, value) in entries_by_domain(hass, entry, "switch"):
        c = set_coordinator(hass, entry, key, value)
        await c.async_config_entry_first_refresh()
        entities.append(Entity(c))

    add_entities(entities)
    return True

class Entity(BaseEntity, SwitchEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)

    async def async_turn_on(self, **kwargs):
        return await self._coordinator.async_call_service("turn_on", kwargs)

    async def async_turn_off(self, **kwargs):
        return await self._coordinator.async_call_service("turn_off", kwargs)

