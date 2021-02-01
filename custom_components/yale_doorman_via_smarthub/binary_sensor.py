from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import (
    BINARY_SENSOR,
    BINARY_SENSOR_DEVICE_CLASS,
    DEFAULT_NAME,
    DOMAIN,
)
from .entity import YaleDoormanViaSmarthubEntity

import logging
_LOGGER: logging.Logger = logging.getLogger(__package__)

BITWISE_CLOSED = 16
BITWISE_LOCKED = 1

async def async_setup_entry(hass, entry, async_add_devices):
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        status = await coordinator.api.async_status()
        doors = []
        idx = 0
        for device_status in status["data"]["device_status"]:
            door = YaleDoormanViaSmarthubBinarySensor(coordinator, entry, idx)
            doors.append(door)
            idx = idx + 1
        async_add_devices(doors)
    except Exception as exception:
        _LOGGER.error(exception)

class YaleDoormanViaSmarthubBinarySensor(YaleDoormanViaSmarthubEntity, BinarySensorEntity):

    def __init__(self, coordinator, config_entry, idx):
        super().__init__(coordinator, config_entry)
        self.idx = idx

    @property
    def unique_id(self):
        return self.coordinator.data["data"]["device_status"][self.idx]["device_id"] + "_binary_sensor"

    @property
    def device_class(self):
        return BINARY_SENSOR_DEVICE_CLASS

    @property
    def name(self):
        try:
            name = self.coordinator.data["data"]["device_status"][self.idx]["name"]
            self.old_name = name
        except Exception as exception:
            name = self.old_name
        
        return name

    @property
    def is_on(self):
        try:
            door_status = int(self.coordinator.data["data"]["device_status"][self.idx]["minigw_lock_status"],16)
            self.old_door_status = door_status
        except Exception as exception:
            door_status = self.old_status
        
        if door_status & BITWISE_CLOSED:
            return False
        return True

    @property
    def icon(self):
        try:
            door_status = int(self.coordinator.data["data"]["device_status"][self.idx]["minigw_lock_status"],16)
            self.old_door_status = door_status
        except Exception as exception:
            door_status = self.old_status
        
        if door_status & BITWISE_CLOSED:
            if door_status & BITWISE_LOCKED:
                return "mdi:door-closed-lock"
            return "mdi:door-closed"
        return "mdi:door-open"