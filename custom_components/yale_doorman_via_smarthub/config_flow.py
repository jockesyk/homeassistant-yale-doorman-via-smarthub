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
    CONF_ENABLE_BINARY_SENSOR,
    BINARY_SENSOR,
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
            except Exception as exception:
                _LOGGER.error(exception)
                self._errors["base"] = "auth"
        
        return await self._show_config_form(user_input)
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return YaleDoormanViaSmarthubOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str, 
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_PINCODE): str,
                    vol.Required(CONF_ENABLE_BINARY_SENSOR, default = False): bool
                }
            ),
            errors=self._errors,
        )

class YaleDoormanViaSmarthubOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
    
    async def async_step_init(self, user_input=None):
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
                    vol.Optional(CONF_PINCODE, default = self.config_entry.data.get(CONF_PINCODE)): str,
                    vol.Required(CONF_ENABLE_BINARY_SENSOR, default = self.config_entry.data.get(CONF_ENABLE_BINARY_SENSOR)): bool
                }
            ),
        )
    
    async def _update_options(self):
        reload_entities = False
        if self.config_entry.data.get(CONF_ENABLE_BINARY_SENSOR) != self.options.get(CONF_ENABLE_BINARY_SENSOR):
            reload_entities = True
        
        self.config_entry.data = self.options
        
        if reload_entities:
            if self.options.get(CONF_ENABLE_BINARY_SENSOR):
                #coordinator.platforms.append(BINARY_SENSOR)
                #self.hass.async_add_job(self.hass.config_entries.async_forward_entry_setup(self.config_entry, BINARY_SENSOR))
            else:
                #self.hass.config_entries.async_forward_entry_unload(self.config_entry, BINARY_SENSOR)
        
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )
