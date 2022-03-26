from homeassistant.components import sensor

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseEntity
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

class Entity(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_domain = "sensor"

    def _sensor(self, state):
        if state.domain == "sensor":
            if state.state in (None, "unknown", "unavailable"):
                return (0, state.attributes.get("unit_of_measurement"), state.attributes.get("device_class"))
            return (float(state.state), state.attributes.get("unit_of_measurement"), state.attributes.get("device_class"))
        elif state.domain == "number":
            return (float(state.state), None, None)
        elif state.domain == "binary_sensor":
            return (100 if state.state == "on" else 0, "%", "percentage")
        elif state.domain == "light":
            if "brightness" in state.attributes:
                return (round(state.attributes["brightness"] * 100 / 255), "%", "percentage")
            return (100 if state.state == "on" else 0, "%", "percentage")
        elif state.domain == "switch":
            return (100 if state.state == "on" else 0, "%", "percentage")
        elif state.domain == "cover":
            if "current_position" in state.attributes:
                return (state.attributes["current_position"], "%", "percentage")
            return (100 if state.state == "open" else 0, "%", "percentage")
        elif state.domain == "climate":
            if "current_temperature" in state.attributes:
                return (state.attributes["current_temperature"], "°C", "temperature")
            return (0 if state.state == "off" else 100, "%", "percentage")
        return (0, None, None)

    def _sensors(self):
        return map(lambda x: self._sensor(x), self._coordinator.states())

    @property
    def device_class(self):
        return self._all(list(map(lambda x: x[2], self._sensors())))

    @property
    def native_value(self):
        if not self.available:
            return None
        arr = list(map(lambda x: x[0], self._sensors()))
        fn = self._coordinator._data.get("stat", "avg")
        # _LOGGER.debug("native_value %s = %s, %s - %s", self.name, arr, list(self._sensors()), self._coordinator._data)
        if len(arr) == 0:
            return None
        if fn == "max":
            return max(arr)
        elif fn == "min":
            return min(arr)
        elif fn == "avg":
            return self._avg(arr)
        elif fn == "sum":
            return sum(arr)
        return None

    @property
    def state_class(self):
        return self._all(self._all_values("state_class"), "measurement")

    @property
    def native_unit_of_measurement(self):
        return self._all(list(map(lambda x: x[1], self._sensors())))

        
