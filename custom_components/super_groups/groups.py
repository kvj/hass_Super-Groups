from .constants import DOMAIN, PLATFORMS
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.entity_registry import async_get_registry, async_entries_for_device
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.service import async_call_from_config
from homeassistant.helpers.restore_state import RestoreEntity

import logging
_LOGGER = logging.getLogger(__name__)


def _any(arr, val):
    for item in arr:
        if item == val:
            return True
    return False


class Coordinator(DataUpdateCoordinator):

    def __init__(self, hass, entry, data) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Super Groups",
            update_method=self.async_update,
        )
        self.entry = entry
        self._data = data

    async def async_config_entry_first_refresh(self):
        self._state_listener = async_track_state_change(
            self.hass,
            entity_ids=[x.entity_id for x in await self._all_entries()],
            action=self._async_on_state_change
        )
        return await super().async_config_entry_first_refresh()

    async def _async_on_state_change(self, entity_id, from_state, to_state):
        _LOGGER.debug("_async_on_state_change %s, %s -> %s",
                      entity_id, from_state, to_state)
        self.async_set_updated_data(await self.async_update())

    async def _all_entries(self):
        entity_reg = await async_get_registry(self.hass)
        result = dict()
        entry = self._data.get("items", {})
        for item in entry.get("entity_id", []):
            entity = entity_reg.async_get(item)
            if entity and not entity.disabled:
                result[entity.entity_id] = entity
        for item in entry.get("device_id", []):
            for entity in async_entries_for_device(entity_reg, item):
                result[entity.entity_id] = entity
        return filter(lambda x: x.entity_category != "diagnostic", result.values())

    def _with_valid_state(self, entry):
        state = self.hass.states.get(entry.entity_id)
        if not state:
            return None
        return (entry, state)

    @property
    def domain(self):
        return self._data["domain"]

    @property
    def unique_id(self):
        return "%s-%s" % (self.config_id, self.entity_id)

    async def async_update(self):
        entries = await self._all_entries()
        return list(filter(lambda x: x != None, map(lambda x: self._with_valid_state(x), entries)))

    async def async_unload(self):
        pass

    @property
    def entity_name(self):
        return self._data.get("title", self.entity_id)

    @property
    def entity_id(self):
        return self._data["id"]

    @property
    def config_id(self):
        return self.entry.entry_id

    def states(self, domains=[]):
        return list(
            filter(
                lambda x: x != None, 
                map(lambda x: x[1] if x[1].domain in domains or len(domains) == 0 else None, self.data)
            )
        )

    def is_on(self):
        def _is_on(domain, state):
            if domain in _ON_STATES:
                return state in _ON_STATES[domain]
            if domain in _OFF_STATES:
                return state not in _OFF_STATES[domain]
            return False
        states = [_is_on(x.domain, x.state) for x in self.states()]
        _LOGGER.debug("is_on: %s = %s", self.entity_id, states)
        if self._data.get("all_on") == True:
            return not _any(states, False)
        return _any(states, True)

    async def async_call_service(self, name, args):
        ids = {}
        for key in _SERVICES:
            ids[key] = set()
        for item in self.data:
            domain = item[1].domain
            if domain in ids and name in _SERVICES[domain]:
                ids[domain].add(item[1].entity_id)
        for (domain, entity_ids) in ids.items():
            if len(entity_ids) > 0:
                _LOGGER.debug("Calling: %s + %s, %s", domain, name, args)
                await async_call_from_config(self.hass, {
                    "service": "%s.%s" % (domain, name),
                    "entity_id": list(entity_ids),
                    "data": args
                })

_ON_STATES = {
    "light": ["on"],
    "switch": ["on"],
    "binary_sensor": ["on"],
}

_OFF_STATES = {
    "climate": ["off"],
    "cover": ["closed"],
    "sensor": [0, "0", "unknown"],
}

_SERVICES = {
    "light": ["turn_on", "turn_off"],
    "switch": ["turn_on", "turn_off"],
    "binary_sensor": [],
    "climate": ["set_hvac_mode", "set_preset_mode", "set_fan_mode", "set_humidity", "set_swing_mode", "set_temperature", "set_aux_heat"],
    "cover": ["open_cover", "close_cover", "set_cover_position", "stop_cover", "open_cover_tilt", "close_cover_tilt", "set_cover_tilt_position", "stop_cover_tilt"],
    "number": ["set_value"],
}


class BaseEntity(CoordinatorEntity, RestoreEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_domain = "domain"
        self._initial_state = False
        self._empty_state = None
        self._supported_features = 0

    @property
    def available(self) -> bool:
        return not _any(self._all_values(None), "unavailable")

    @property
    def device_class(self):
        return self._all(self._all_values("device_class", domains=[self._attr_domain]))

    def empty_from_state(self, state):
        return state.state == "on"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if state := await self.async_get_last_state():
            self._empty_state = self.empty_from_state(state)
        else:
            self._empty_state = self._initial_state
        _LOGGER.debug("async_added_to_hass: [%s] = %s", self.name, self._empty_state)

    @property
    def supported_features(self):
        if self.is_empty:
            return self._supported_features
        joined = 0
        for one in self._all_values("supported_features", domains=[self._attr_domain]):
            joined = joined | one
        return joined

    @property
    def name(self) -> str:
        return self._coordinator.entity_name

    @property
    def unique_id(self) -> str:
        return self._coordinator.unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("id", self._coordinator.entity_id)
            },
            "name": self.name,
        }

    @property
    def entries(self):
        return self._coordinator.data

    @property
    def is_empty(self):
        return len(self._coordinator.states()) == 0

    @property
    def is_on(self) -> bool:
        if not self.available:
            return None
        _LOGGER.debug("is_on: [%s] = %s, %s", self.name, self.is_empty, self._empty_state)
        if self.is_empty:
            return self._empty_state
        return self._coordinator.is_on()

    def _all_values(self, name, domains=[]):
        return list(filter(
            lambda x: x != None, 
            [x.attributes.get(name) if name else x.state for x in self._coordinator.states(domains=domains)]
        ))

    def _avg(self, arr, default=None):
        total = 0
        for item in arr:
            total += item
        return total / len(arr) if len(arr) > 0 else default

    def _first(self, arr, default=None):
        if len(arr):
            return arr[0]
        return default

    def _all(self, arr, default=None): 
        """Return value only when all values are the same, default otherwise"""
        if len(arr):
            first = arr[0]
            for item in arr:
                if item != first:
                    return default
            return first
        return default

    def _union(self, attr_name): # Union all values + preserve order
        all_vals = []
        for one in self._all_values(attr_name):
            for val in one:
                if val not in all_vals:
                    all_vals.append(val)
        return all_vals

    def save_empty_state(self):
        if self.is_empty:
            self.async_write_ha_state()

class BaseNumberEntity(BaseEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

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
    def _native_value(self):
        if not self.available:
            return None
        arr = list(map(lambda x: x[0], self._sensors()))
        fn = self._coordinator._data.get("stat", "avg")
        if len(arr) == 0:
            return self._empty_state
        if fn == "max":
            return max(arr)
        elif fn == "min":
            return min(arr)
        elif fn == "avg":
            return self._avg(arr)
        elif fn == "sum":
            return sum(arr)
        return None
