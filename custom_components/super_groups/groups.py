from .constants import DOMAIN, PLATFORMS
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.entity_registry import async_get_registry, async_entries_for_device
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.service import async_call_from_config

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
        states = self.states(domains=["light", "switch", "binary_sensor"])
        _LOGGER.debug("is_on: %s = %s", self.entity_id, states)
        if self._data.get("all_on") == True:
            return not _any([x.state == "on" for x in states], False)
        return _any([x.state == "on" for x in states], True)

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


_SERVICES = {
    "light": ["turn_on", "turn_off"],
    "switch": ["turn_on", "turn_off"],
    "binary_sensor": [],
    "climate": ["", "set_preset_mode", "set_fan_mode", "set_humidity", "set_swing_mode", "set_temperature", "set_aux_heat"],
}


class BaseEntity(CoordinatorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)
        self._coordinator = coordinator

    @property
    def available(self) -> bool:
        return not _any(self._coordinator.states(), "unavailable")

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
    def is_on(self) -> bool:
        return self._coordinator.is_on()

    def _all_values(self, name, domains=[]):

        return list(filter(
            lambda x: x != None, 
            [x.attributes.get(name) if name else x.state for x in self._coordinator.states(domains=domains)]
        ))

    def _avg(self, arr):
        total = 0
        for item in arr:
            total += item
        return total / len(arr) if len(arr) > 0 else None

    def _first(self, arr, default=None):
        if len(arr):
            return arr[0]
        return default

    def _all(self, arr, default=None):
        if len(arr):
            first = arr[0]
            for item in arr:
                if item != first:
                    return default
            return first
        return default