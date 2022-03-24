from homeassistant.components import cover

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, add_entities):
    entities = []
    for (key, value) in entries_by_domain(hass, entry, "cover"):
        c = set_coordinator(hass, entry, key, value)
        await c.async_config_entry_first_refresh()
        entities.append(Entity(c))

    add_entities(entities)
    return True

class Entity(BaseEntity, cover.CoverEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_domain = "cover"

    @property
    def current_cover_position(self):
        return self._avg(self._all_values("current_cover_position"))

    @property
    def current_cover_tilt_position(self):
        return self._avg(self._all_values("current_cover_tilt_position"))

    def _is_any_state(self, state):
        return state in self._all_values(None, domains=["cover"])

    @property
    def is_opening(self):
        return self._is_any_state("opening")

    @property
    def is_closing(self):
        return self._is_any_state("closing")

    @property
    def is_closed(self):
        return self._all(self._all_values(None, domains=["cover"]))

    async def async_open_cover(self, **kwargs):
        return await self._coordinator.async_call_service("open_cover", kwargs)

    async def async_close_cover(self, **kwargs):
        return await self._coordinator.async_call_service("close_cover", kwargs)

    async def async_set_cover_position(self, **kwargs):
        return await self._coordinator.async_call_service("set_cover_position", kwargs)

    async def async_stop_cover(self, **kwargs):
        return await self._coordinator.async_call_service("stop_cover", kwargs)

    async def async_open_cover_tilt(self, **kwargs):
        return await self._coordinator.async_call_service("open_cover_tilt", kwargs)

    async def async_close_cover_tilt(self, **kwargs):
        return await self._coordinator.async_call_service("close_cover_tilt", kwargs)

    async def async_set_cover_tilt_position(self, **kwargs):
        return await self._coordinator.async_call_service("set_cover_tilt_position", kwargs)

    async def async_stop_cover_tilt(self, **kwargs):
        return await self._coordinator.async_call_service("stop_cover_tilt", kwargs)

