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
        self._supported_features = 4 # Position
        self._initial_state = 0

    def empty_from_state(self, state):
        return state.attributes.get("current_position", self.empty_from_state)

    @property
    def current_cover_position(self):
        return self._avg(self._all_values("current_position"), default=self._empty_state)

    @property
    def current_cover_tilt_position(self):
        return self._avg(self._all_values("current_tilt_position"), default=0)

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
        if self.is_empty:
            return self._empty_state == 0
        return self._all(self._all_values(None, domains=["cover"])) == "closed"

    async def async_open_cover(self, **kwargs):
        return await self._coordinator.async_call_service("open_cover", kwargs)

    async def async_close_cover(self, **kwargs):
        return await self._coordinator.async_call_service("close_cover", kwargs)

    async def async_set_cover_position(self, **kwargs):
        self._empty_state = kwargs.get("position", self._empty_state)
        self.save_empty_state()
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

