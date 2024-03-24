from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import storage, event

from .constants import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_INVERT,
    CONF_TYPE,
    CONF_TOGGLE,
)

import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class Platform():

    def __init__(self, hass):
        self.hass = hass
        self._storage = storage.Store(hass, 1, DOMAIN)

    async def async_load(self):
        data_ = await self._storage.async_load()
        _LOGGER.debug(f"async_load(): Loaded stored data: {data_}")
        self._storage_data = data_ if data_ else {}

    def get_data(self, key: str, def_={}):
        if key in self._storage_data:
            return self._storage_data[key]
        return def_

    async def async_put_data(self, key: str, data):
        if data:
            self._storage_data = {
                **self._storage_data,
                key: data,
            }
        else:
            if key in self._storage_data:
                del self._storage_data[key]
        await self._storage.async_save(self._storage_data)


class Coordinator(DataUpdateCoordinator):

    def __init__(self, platform, entry):
        super().__init__(
            platform.hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update,
        )
        self._platform = platform
        self._entry = entry
        self._entry_id = entry.entry_id

        self._config = entry.as_dict()["options"]

    async def _async_update(self):
        return {}

    async def _async_update_state(self, data: dict):
        self.async_set_updated_data({
            **self.data,
            **data,
        })

    async def async_load(self):
        _LOGGER.debug(f"async_load: {self._config}")
        self._entity_ids = self._config.get(CONF_ENTITIES)
        if len(self._entity_ids):
            self._state_listener = event.async_track_state_change(self.hass, self._entity_ids, action=self._async_on_state_change)
        else:
            self._state_listener = None
        await self._async_recalculate_state(None)

    async def _async_on_state_change(self, entity_id: str, from_state, to_state):
        await self._async_recalculate_state(entity_id)

    def _state_to_bool(self, state) -> bool:
        if state.state == "on":
            return True
        elif state.state == "off":
            return False
        elif state.domain == "cover":
            return state.state == "open"
        elif state.state in (None, "unknown", "undefined", ""):
            return False
        try:
            return float(state.state) != 0
        except ValueError:
            pass
        return True

    async def _async_recalculate_state(self, entity_id: str):
        is_on = False
        states = {}
        for _id in self._entity_ids:
            if state := self.hass.states.get(_id):
                states[_id] = state
                _LOGGER.debug(f"_async_recalculate_state: state: {state.state}, is_on: {self._state_to_bool(state)}, type: {type(state.state)}")
                if self._state_to_bool(state):
                    is_on = True
        new_is_on = is_on if not self._config.get(CONF_INVERT) else not is_on
        old_is_on = self.data.get("on")
        await self._async_update_state({
            "on": new_is_on,
            "states": states,
        })
        if _id := self._config.get(CONF_TOGGLE):
            if new_is_on != old_is_on:
                await self.hass.services.async_call("homeassistant", "turn_on" if new_is_on else "turn_off", {
                    "entity_id": _id,
                }, blocking=False)


    async def async_unload(self):
        _LOGGER.debug(f"async_unload:")
        if self._state_listener:
            self._state_listener()

    def is_of_type(self, type_: str) -> bool:
        return self._config[CONF_TYPE] == type_

    async def async_forward_call(self, action, extra_args):
        MAPPING = {
            ("homeassistant.turn_on", "cover"): "cover.open_cover",
            ("homeassistant.turn_off", "cover"): "cover.close_cover",
        }
        calls = {}
        for _id in self._entity_ids:
            [domain, name] = _id.split(".")
            if new_action := MAPPING.get((action, domain)):
                calls[new_action] = calls.get(new_action, []) + [_id]
            else:
                calls[action] = calls.get(action, []) + [_id]
        for (action, _ids) in calls.items():
            [domain, name] = action.split(".")
            _LOGGER.debug(f"async_forward_call: call {domain} . {name} / {_ids}")
            await self.hass.services.async_call(domain, name, {
                "entity_id": _ids,
                **extra_args,
            }, blocking=False)


class BaseEntity(CoordinatorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("on")

    def with_name(self, id: str, name: str):
        self._attr_has_entity_name = True
        self._attr_unique_id = f"super_group_{self.coordinator._entry_id}_{id}"
        self._attr_name = name
        return self

    def attr(self, domain, name):
        result = []
        for state in self.coordinator.data.get("states", {}).values():
            if name in state.attributes:
                result.append(state.attributes[name])
        return result

    def attr_first(self, domain, name, def_value=None):
        for value in self.attr(domain, name):
            if value != None:
                return value
        return def_value

    def attr_fn(self, domain, name, fn, def_value=None):
        values = []
        for value in self.attr(domain, name):
            if value != None:
                values.append(value)
        return def_value if len(values) == 0 else fn(values)

class ToggleBaseEntity(BaseEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_forward_call("homeassistant.turn_on", kwargs)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_forward_call("homeassistant.turn_off", kwargs)
