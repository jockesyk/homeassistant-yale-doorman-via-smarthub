import asyncio
from datetime import timedelta
import logging
import os
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.translation import async_get_translations
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.json import load_json

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
    
    async def handle_download_log(call: ServiceCall) -> dict:
        """Handles the service action to download the event log."""
        _LOGGER.info("Calling service action to download Yale event log")

        try:
            coordinator: YaleDoormanViaSmarthubDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
            
            device_map = {} # Will store (area, zone) -> "Name"
            
            try:
                # Get device list from coordinator data (like in entity.py)
                device_list = coordinator.data.get("data", {}).get("device_status", [])
                for device in device_list:
                    try:
                        area = int(device.get("area"))
                        zone = int(device.get("no"))
                        name = device.get("name")
                        if area is not None and zone is not None and name:
                            device_map[(area, zone)] = name
                    except (TypeError, ValueError):
                        continue

                _LOGGER.debug(f"Built device map: {device_map}")
            except Exception as e:
                _LOGGER.error(f"Failed to build device map from coordinator data: {e}")

            # Get page count from service call
            max_pages = int(call.data.get("pages", 1))
            all_events = []

            for page_num in range(1, max_pages + 1):
                log_data = await coordinator.api.async_get_yale_event_log(page_number=str(page_num))
                log_events = log_data.get("data", [])
                _LOGGER.info(f"Downloaded page {str(page_num)} with {len(log_events)} events")
                all_events.extend(log_events)

            language = hass.config.language or "en"

            path = os.path.join(os.path.dirname(__file__), "translations", f"{language}.json")
            fallback_path = os.path.join(os.path.dirname(__file__), "translations", "en.json")
            try:
                with open(path, encoding="utf-8") as f:
                    translations = json.load(f)
            except FileNotFoundError:
                with open(fallback_path, encoding="utf-8") as f:
                    translations = json.load(f)
            
            event_type_map = translations.get("responses", {}).get("event_type", {})

            formatted_events = []
            for event in log_events:
                event_id = str(event.get("event_type"))
                event_area = event.get("area")
                event_zone = event.get("zone") 
                device_key = None
                device_name = "System" 

                try:
                    area_int = int(event_area)
                    zone_int = int(event_zone)
                    
                    if area_int > 0:
                        device_key = (area_int, zone_int)
                        device_name = device_map.get(
                            device_key, 
                            f"Unknown Device (A:{area_int}, Z:{zone_int})"
                        )
                except (TypeError, ValueError):
                    pass

                translated_event = event_type_map.get(event_id, f"Unknown event {event_id}")

                if event_id in range(1301,1399) or event_id in ["1602"]:
                    formatted_events.append({
                        "Time": event.get("time", "N/A"),
                        "Event": translated_event,
                    })
                elif event_id in ["1801", "1807", "1815", "1816", "3801", "3802"]:
                    formatted_events.append({
                        "Time": event.get("time", "N/A"),
                        "Event": translated_event,
                        "Device": device_name,
                    })
                else:
                    formatted_events.append({
                        "Time": event.get("time", "N/A"),
                        "Event": translated_event,
                        "Device": device_name,
                        "Name": event.get("name", ""),
                    })

            return {
                "event_log_table": formatted_events,
                "total_rows_returned": len(formatted_events),
                "pages_fetched": max_pages
#                "log_data": log_data
            }

        except Exception as e:
            _LOGGER.error(f"Could not download Yale event log: {e}")
            raise

    hass.services.async_register(
        DOMAIN, 
        "download_yale_event_log", 
        handle_download_log,
        supports_response=SupportsResponse.ONLY
    )
#end
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