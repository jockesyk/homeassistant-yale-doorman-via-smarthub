from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol
import logging

from .api import YaleDoormanViaSmarthubApiClient
from .const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PINCODE,
    DOMAIN,
    PLATFORMS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)

class YaleDoormanViaSmarthubFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        self._errors = {}

    async def async_step_user(self, user_input=None):
        self._errors = {}
        
        if user_input is not None:
            
            try:
                session = async_create_clientsession(self.hass)
                client = YaleDoormanViaSmarthubApiClient(user_input[CONF_USERNAME], user_input[CONF_PASSWORD], session)
                result = await client.async_login()
                if result:
                    return self.async_create_entry(
                        title = user_input[CONF_USERNAME],
                        data = user_input, 
                    )
            except Exception as exception:  # pylint: disable=broad-except
                _LOGGER.error(exception)
                self._errors["base"] = "auth"
        
        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return YaleDoormanViaSmarthubOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str, 
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_PINCODE): str
                }
            ),
            errors=self._errors,
        )

class YaleDoormanViaSmarthubOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default = self.config_entry.data.get(CONF_USERNAME)): str, 
                    vol.Required(CONF_PASSWORD, default = self.config_entry.data.get(CONF_PASSWORD)): str,
                    vol.Optional(CONF_PINCODE, default = self.config_entry.data.get(CONF_PINCODE)): str
                }
            ),
        )

    async def _update_options(self):
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )