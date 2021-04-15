from homeassistant.components.lock import LockEntity

from .const import (
    DOMAIN,
    CONF_PINCODE,
    BITWISE_LOCKED,
    BITWISE_CLOSED
)

from .entity import YaleDoormanViaSmarthubEntity
from .api import YaleDoormanViaSmarthubApiClient

import logging
_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass, entry, async_add_entities):
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        status = await coordinator.api.async_status()
        locks = []
        idx = 0
        for device_status in status["data"]["device_status"]:
            lock = YaleDoormanViaSmarthubLock(coordinator, entry, idx)
            locks.append(lock)
            idx = idx + 1
        async_add_entities(locks, True)
    except Exception as exception:
        _LOGGER.error(exception)

class YaleDoormanViaSmarthubLock(YaleDoormanViaSmarthubEntity, LockEntity):
    
    def __init__(self, coordinator, config_entry, idx):
        super().__init__(coordinator, config_entry)
        self.idx = idx
    
    async def async_lock(self, **kwargs):
        success = await self.coordinator.api.async_lock(self.unique_id,self._area,self._zone)
        if success:
            door_status = 15
            data = self.coordinator.data
            data["data"]["device_status"][self.idx]["minigw_lock_status"] = str(door_status)
            self.coordinator.async_set_updated_data(data)
        else:
            _LOGGER.info("Lock failed")
    
    async def async_unlock(self, **kwargs):
        pincode = self.config_entry.data.get(CONF_PINCODE)
        success = await self.coordinator.api.async_unlock(self.unique_id,self._area,self._zone,pincode)
        if success:
            door_status = 14
            data = self.coordinator.data
            data["data"]["device_status"][self.idx]["minigw_lock_status"] = str(door_status)
            self.coordinator.async_set_updated_data(data)
        else:
            _LOGGER.info("Unlock failed")
    
    @property
    def is_locked(self):
        try:
            door_status = int(self.coordinator.data["data"]["device_status"][self.idx]["minigw_lock_status"],16)
            self.old_door_status = door_status
        
        except Exception as exception:
            door_status = self.old_door_status
        
        if door_status & BITWISE_CLOSED:
            if door_status & BITWISE_LOCKED:
                return True
        return False
    
    @property
    def is_door_open(self):
        try:
            door_status = int(self.coordinator.data["data"]["device_status"][self.idx]["minigw_lock_status"],16)
            self.old_door_status = door_status
        except Exception as exception:
            door_status = self.old_door_status
        
        if door_status & BITWISE_CLOSED:
            return False
        return True
    
    @property
    def code_format(self):
        try:
            pincode = self.config_entry.data.get(CONF_PINCODE)
            if pincode:
                return None
        except Exception as exception:
            pass
        
        return "%d{6}"
    
    @property
    def icon(self):
        try:
            door_status = int(self.coordinator.data["data"]["device_status"][self.idx]["minigw_lock_status"],16)
            self.old_door_status = door_status
        except Exception as exception:
            door_status = self.old_door_status
        
        if door_status & BITWISE_CLOSED:
            if door_status & BITWISE_LOCKED:
                return "mdi:lock"
            return "mdi:lock-open-variant"
        return "mdi:door-open"
    
    @property
    def device_state_attributes(self):
        door = "closed"
        if self.is_door_open:
            door = "open"
        return {
            "door": door
        }
