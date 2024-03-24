from homeassistant.components.binary_sensor import BinarySensorEntity

import logging

from .coordinator import BaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    if coordinator.is_of_type("binary_sensor"):
        add_entities([_Entity(coordinator)])
    return True

class _Entity(BaseEntity, BinarySensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"binary_sensor", coordinator._config["name"])

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("on")
