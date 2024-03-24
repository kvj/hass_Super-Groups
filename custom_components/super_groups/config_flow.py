from collections.abc import Mapping
from typing import Any, cast

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector

from homeassistant.const import (
    CONF_NAME,
)

from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from .constants import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_INVERT,
    CONF_TOGGLE,
    CONF_TYPE,
    CONF_TYPES,
)

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITIES, description={"suggested_value": []}): selector({"entity": {"multiple": True}}),
    vol.Required(CONF_INVERT, description={"suggested_value": False}): selector({"boolean": {}}),
    vol.Optional(CONF_TOGGLE): selector({"entity": {"multiple": False}}),
})

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): selector({"text": {}}),
    vol.Required(CONF_TYPE, description={"suggested_value": "binary_sensor"}): selector({"select": {"options": CONF_TYPES,}}),
}).extend(OPTIONS_SCHEMA.schema)

async def _validate_options(step, user_input):
    _LOGGER.debug(f"_validate_options: {user_input}, {step}, {step.options}")
    user_input[CONF_TYPE] = step.options[CONF_TYPE]
    return user_input

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA, _validate_options),
}

class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        return cast(str, options[CONF_NAME])
