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
        return self._avg(self._all_values("temperature"))

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
        return self._all(self._all_values("hvac_action"), "off")

    @property
    def hvac_mode(self):
        if not self.available:
            return None
        return self._all(self._all_values(None, domains=["climate"]), "off")

    @property
    def hvac_modes(self):
        all_modes = set()
        for one in self._all_values("hvac_modes"):
            all_modes = all_modes.union(one)
        return list(all_modes)

    @property
    def preset_mode(self):
        return self._all(self._all_values("preset_mode"), "none")

    @property
    def preset_modes(self):
        all_modes = set()
        for one in self._all_values("preset_modes"):
            all_modes = all_modes.union(one)
        return list(all_modes)

    @property
    def is_aux_heat(self):
        return self._all(self._all_values("is_aux_heat"), False)

    @property
    def supported_features(self):
        joined = 0
        for one in self._all_values("supported_features"):
            joined = joined | one
        return joined

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
        return await self._coordinator.async_call_service("set_temperature", kwargs)

    async def async_turn_aux_heat_on(self):
        return await self._coordinator.async_call_service("set_aux_heat", {"aux_heat": True})

    async def async_turn_aux_heat_off(self):
        return await self._coordinator.async_call_service("set_aux_heat", {"aux_heat": False})
