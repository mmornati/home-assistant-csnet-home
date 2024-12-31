from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from datetime import timedelta
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CSNetHomeCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch all sensor data from the cloud API."""
    
    def __init__(self, hass: HomeAssistant, update_interval: int, entry_id: str):
        """Initialize the coordinator."""
        _LOGGER.debug("Configuring CSNetHome Coordinator")
        self.hass = hass
        self.entry_id = entry_id
        self.update_interval = timedelta(seconds=update_interval)
        self.sensors_data = []
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_method=self._async_update_data, update_interval=self.update_interval
        )

    async def _async_update_data(self):
        """Fetch data for all sensors."""
        _LOGGER.debug("Fetching all CSNet Home sensor data from API.")
        
         # Retrieve the CloudServiceAPI object from hass data
        cloud_api = self.hass.data[DOMAIN][self.entry_id]["api"]
        if not cloud_api:
            _LOGGER.error("No CloudServiceAPI instance found!")
            return
        
        sensor_data = await cloud_api.async_get_sensor_data()
        self.sensors_data = sensor_data
        return self.sensors_data
    
    def get_sensors_data(self):
        return self.sensors_data