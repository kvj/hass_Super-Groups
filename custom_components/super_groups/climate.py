from homeassistant.components import climate
from homeassistant.const import (
    TEMP_CELSIUS,
)

import logging

from .integration import entries_by_domain, set_coordinator
from .groups import BaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, add_entities):
    entities = []
    for (key, value) in entries_by_domain(hass, entry, "climate"):
        c = set_coordinator(hass, entry, key, value)
        await c.async_config_entry_first_refresh()
        entities.append(Entity(c))

    add_entities(entities)
    return True

class Entity(BaseEntity, climate.ClimateEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_domain = "climate"
        self._initial_state = 20
        self._supported_features = 1 # Temperature

    def empty_from_state(self, state):
        return state.attributes.get("temperature", self._empty_state)

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS # For now

    @property
    def current_temperature(self):
        return self._avg(self._all_values("current_temperature"))

    @property
    def current_humidity(self):
        return self._avg(self._all_values("current_humidity"))

    @property
    def target_temperature(self):
        return self._avg(self._all_values("temperature"), self._empty_state)

    @property
    def target_humidity(self):
        return self._avg(self._all_values("humidity"))

    @property
    def min_temp(self):
        return max(self._all_values("min_temp"), default=None)

    @property
    def max_temp(self):
        return min(self._all_values("max_temp"), default=None)

    @property
    def min_humidity(self):
        return max(self._all_values("min_humidity"), default=None)

    @property
    def max_humidity(self):
        return min(self._all_values("max_humidity"), default=None)

    @property
    def hvac_action(self):
        if self.is_empty:
            return "heating"
        return self._all(self._all_values("hvac_action"), "off")

    @property
    def hvac_mode(self):
        if not self.available:
            return None
        if self.is_empty:
            return "heat"
        return self._all(self._all_values(None, domains=["climate"]), "off")

    @property
    def hvac_modes(self):
        if self.is_empty:
            return ["heat"]
        return self._union("hvac_modes")

    @property
    def preset_mode(self):
        return self._all(self._all_values("preset_mode"), "none")

    @property
    def preset_modes(self):
        if self.is_empty:
            return ["none"]
        return self._union("preset_modes")

    @property
    def fan_mode(self):
        return self._all(self._all_values("fan_mode"), "off")

    @property
    def fan_modes(self):
        return self._union("fan_modes")

    @property
    def swing_mode(self):
        return self._all(self._all_values("swing_mode"), "off")

    @property
    def swing_modes(self):
        return self._union("swing_modes")

    @property
    def is_aux_heat(self):
        return self._all(self._all_values("is_aux_heat"), False)

    async def async_set_hvac_mode(self, **kwargs):
        return await self._coordinator.async_call_service("set_hvac_mode", kwargs)

    async def async_set_preset_mode(self, **kwargs):
        return await self._coordinator.async_call_service("set_preset_mode", kwargs)

    async def async_set_fan_mode(self, **kwargs):
        return await self._coordinator.async_call_service("set_fan_mode", kwargs)

    async def async_set_humidity(self, **kwargs):
        return await self._coordinator.async_call_service("set_humidity", kwargs)

    async def async_set_swing_mode(self, **kwargs):
        return await self._coordinator.async_call_service("set_swing_mode", kwargs)

    async def async_set_temperature(self, **kwargs):
        self._empty_state = kwargs.get("temperature", self._empty_state)
        self.save_empty_state()
        return await self._coordinator.async_call_service("set_temperature", kwargs)

    async def async_turn_aux_heat_on(self):
        return await self._coordinator.async_call_service("set_aux_heat", {"aux_heat": True})

    async def async_turn_aux_heat_off(self):
        return await self._coordinator.async_call_service("set_aux_heat", {"aux_heat": False})
