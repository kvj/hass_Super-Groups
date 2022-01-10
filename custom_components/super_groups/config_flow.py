from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from .constants import DOMAIN

import logging
import voluptuous as vol
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

def _validate(user_input):
    errors = {}
    return errors

def _gen_init_schema(data: dict):
    types = {vol.Required(x[0], default=data.get(x[0], True)): bool for x in entity_types}
    return vol.Schema({
        vol.Required("name", default=data.get("name")): cv.string,
        **types,
    })

def _gen_options_schema(data: dict):
    types = {vol.Required(x[0], default=data.get(x[0], False)): bool for x in entity_types}
    return vol.Schema({
        **types,
    })


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    # def async_get_options_flow(config_entry):
    #     return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input):
        return self.async_create_entry(
            title="Super Groups",
            options={},
            data={},
        )
        errors = None

        _LOGGER.debug(f"Input: {user_input}")
        if user_input:
            errors = _validate(user_input)
            if len(errors) == 0:
                return self.async_create_entry(
                    title=user_input.get("name"),
                    options=user_input,
                    data=dict(
                        name=user_input.get("name"), 
                    ),
                )

        if not user_input:
            user_input = dict(name="My Car")

        return self.async_show_form(
            step_id="user", data_schema=_gen_init_schema(user_input), errors=errors
        )

class OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        _LOGGER.debug(f"OptionsFlowHandler: {user_input} {self.config_entry}")
        return self.async_create_entry(title="", data=self.config_entry.as_dict()["options"])
        errors = None
        if user_input:
            errors = _validate(user_input)
            if len(errors) == 0:
                return self.async_create_entry(title="", data=user_input)
        else:
            user_input = self.config_entry.as_dict()["options"]

        return self.async_show_form(
            step_id="init", data_schema=_gen_options_schema(user_input), errors=errors
        )
