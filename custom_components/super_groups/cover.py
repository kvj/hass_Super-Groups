from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)

import logging
import statistics

from .coordinator import BaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    if coordinator.is_of_type("cover"):
        add_entities([_Entity(coordinator)])
    return True

class _Entity(BaseEntity, CoverEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"cover", coordinator._config["name"])

    @property
    def supported_features(self):
        modes = 0
        for attr in self.attr("cover", "supported_features"):
            if attr:
                modes |= attr
        if modes == 0:
            modes = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        return modes

    @property
    def current_cover_position(self):
        return self.attr_fn("cover", "current_position", lambda x: statistics.mean(x), 100 if self.is_on else 0)

    @property
    def is_closed(self):
        return False if self.is_on else True

    async def async_open_cover(self, **kwargs):
        await self.coordinator.async_forward_call("homeassistant.turn_on", kwargs)

    async def async_close_cover(self, **kwargs):
        await self.coordinator.async_forward_call("homeassistant.turn_off", kwargs)

    async def async_set_cover_position(self, **kwargs):
        await self.coordinator.async_forward_call("cover.set_cover_position", kwargs)

    async def async_stop_cover(self, **kwargs):
        await self.coordinator.async_forward_call("cover.stop_cover", kwargs)
