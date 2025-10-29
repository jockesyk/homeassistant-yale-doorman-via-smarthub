import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import YaleDoormanViaSmarthubApiClient

from .const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_ENABLE_BINARY_SENSOR,
    DOMAIN,
    PLATFORMS,
    LOCK,
    BINARY_SENSOR,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)
    
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    enable_binary_sensor = entry.data.get(CONF_ENABLE_BINARY_SENSOR)
    
    session = async_get_clientsession(hass)
    client = YaleDoormanViaSmarthubApiClient(username, password, session)
    
    coordinator = YaleDoormanViaSmarthubDataUpdateCoordinator(hass, client=client)
    await coordinator.async_refresh()
    
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    coordinator.platforms.append(LOCK)
    if enable_binary_sensor:
        coordinator.platforms.append(BINARY_SENSOR)
    await hass.config_entries.async_forward_entry_setups(entry, coordinator.platforms)
    
    entry.add_update_listener(async_reload_entry)
    return True

class YaleDoormanViaSmarthubDataUpdateCoordinator(DataUpdateCoordinator):
    
    def __init__(self, hass: HomeAssistant, client: YaleDoormanViaSmarthubApiClient) -> None:
        self.api = client
        self.platforms = []
        
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        try:
            status = await self.api.async_status()
            return status
        except Exception as exception:
            _LOGGER.info(exception)
            raise UpdateFailed() from exception
    
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unloaded

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
