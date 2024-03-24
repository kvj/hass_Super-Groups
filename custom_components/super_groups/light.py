from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)

import logging
import statistics

from .coordinator import ToggleBaseEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    if coordinator.is_of_type("light"):
        add_entities([_Entity(coordinator)])
    return True

class _Entity(ToggleBaseEntity, LightEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"light", coordinator._config["name"])

    @property
    def supported_color_modes(self):
        modes = set()
        for attr in self.attr("light", "supported_color_modes"):
            if attr:
                modes |= set(attr)
        if len(modes) == 0:
            modes.add(ColorMode.ONOFF)
        return modes

    @property
    def color_mode(self):
        return self.attr_first("light", "color_mode", ColorMode.ONOFF)

    @property
    def brightness(self):
        return self.attr_fn("light", "brightness", lambda x: statistics.mean(x))

    @property
    def rgb_color(self):
        return self.attr_first("light", "rgb_color")

    @property
    def rgbw_color(self):
        return self.attr_first("light", "rgbw_color")
