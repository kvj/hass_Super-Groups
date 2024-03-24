from homeassistant.components.switch import SwitchEntity

import logging

from .coordinator import ToggleBaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    if coordinator.is_of_type("switch"):
        add_entities([_Entity(coordinator)])
    return True

class _Entity(ToggleBaseEntity, SwitchEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"switch", coordinator._config["name"])
