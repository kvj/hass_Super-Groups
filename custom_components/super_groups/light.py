from homeassistant.components.light import (
    LightEntity,
)

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, add_entities):
    entities = []
    for (key, value) in entries_by_domain(hass, entry, "light"):
        c = set_coordinator(hass, entry, key, value)
        await c.async_config_entry_first_refresh()
        entities.append(Entity(c))

    add_entities(entities)
    return True


class Entity(BaseEntity, LightEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_domain = "light"

    async def async_turn_on(self, **kwargs):
        self._empty_state = True
        self.save_empty_state()
        return await self._coordinator.async_call_service("turn_on", kwargs)

    async def async_turn_off(self, **kwargs):
        self._empty_state = False
        self.save_empty_state()
        return await self._coordinator.async_call_service("turn_off", kwargs)

    @property
    def supported_color_modes(self):
        return self._union("supported_color_modes")

    @property
    def brightness(self):
        return self._avg(self._all_values("brightness"))

    @property
    def min_mireds(self):
        return min(self._all_values("min_mireds"))

    @property
    def max_mireds(self):
        return max(self._all_values("max_mireds"))

    @property
    def color_temp(self):
        return self._avg(self._all_values("color_temp"))
