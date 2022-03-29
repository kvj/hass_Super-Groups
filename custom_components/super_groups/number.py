from homeassistant.components import number

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseNumberEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    entities = []
    for (key, value) in entries_by_domain(hass, entry, "number"):
        c = set_coordinator(hass, entry, key, value)
        await c.async_config_entry_first_refresh()
        entities.append(Entity(c))

    add_entities(entities)
    return True

class Entity(BaseNumberEntity, number.NumberEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_domain = "number"
        self._initial_state = 0

    def empty_from_state(self, state):
        return state.state

    @property
    def value(self):
        return self._native_value

    @property
    def unit_of_measurement(self):
        return self._all(list(map(lambda x: x[1], self._sensors())))

    @property
    def min_value(self):
        return max(self._all_values("min_value"), default=0)

    @property
    def max_value(self):
        return min(self._all_values("max_value"), default=100)

    @property
    def step(self):
        return self._all(self._all_values("max_value"))

    @property
    def mode(self):
        return self._all(self._all_values("mode"), default="auto")

    async def async_set_value(self, value) -> None:
        self._empty_state = value
        self.save_empty_state()
        await self._coordinator.async_call_service("set_value", {"value": value})