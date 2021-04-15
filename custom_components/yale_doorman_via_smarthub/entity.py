from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL
)

class YaleDoormanViaSmarthubEntity(CoordinatorEntity):
    
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry
    
    @property
    def unique_id(self):
        try:
            self._unique_id = self.coordinator.data["data"]["device_status"][self.idx]["device_id"]
            self._area = int(self.coordinator.data["data"]["device_status"][self.idx]["area"])
            self._zone = int(self.coordinator.data["data"]["device_status"][self.idx]["no"])
            self.old_unique_id = self._unique_id
        except Exception as exception:
            self._unique_id = self.old_unique_id
        
        return self._unique_id
    
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "model": MODEL,
            "manufacturer": MANUFACTURER,
        }
    
    @property
    def name(self):
        try:
            name = self.coordinator.data["data"]["device_status"][self.idx]["name"]
            self.old_name = name
        except Exception as exception:
            name = self.old_name
        
        return name
