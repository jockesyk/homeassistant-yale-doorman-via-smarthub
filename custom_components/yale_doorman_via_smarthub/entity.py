from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, NAME, VERSION, ATTRIBUTION, MANUFACTURER, MODEL, HUBNAME

class YaleDoormanViaSmarthubEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self):
        return self.config_entry.entry_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "model": MODEL,
            "manufacturer": MANUFACTURER,
        }

    @property
    def device_state_attributes(self):
        return {
            "integration": NAME,
        }