from homeassistant.components import sensor

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseNumberEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    entities = []
    for (key, value) in entries_by_domain(hass, entry, "sensor"):
        c = set_coordinator(hass, entry, key, value)
        await c.async_config_entry_first_refresh()
        entities.append(Entity(c))

    add_entities(entities)
    return True

class Entity(BaseNumberEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_domain = "sensor"
        self._initial_state = None

    def empty_from_state(self, state):
        return state.state

    @property
    def device_class(self):
        return self._all(list(map(lambda x: x[2], self._sensors())))

    @property
    def native_value(self):
        return self._native_value

    @property
    def state_class(self):
        return self._all(self._all_values("state_class"), "measurement")

    @property
    def native_unit_of_measurement(self):
        return self._all(list(map(lambda x: x[1], self._sensors())))
