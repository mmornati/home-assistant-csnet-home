"""Coordinator Class to centralise all data fetching from CSNet Home."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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
        self._device_data = {"sensors": [], "common_data": {}, "water_data": {}}
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=self.update_interval,
        )

    async def _async_update_data(self):
        """Fetch data for all sensors."""

        _LOGGER.debug("Fetching all CSNet Home sensor data from API.")

        # Retrieve the CloudServiceAPI object from hass data
        cloud_api = self.hass.data[DOMAIN][self.entry_id]["api"]
        if not cloud_api:
            _LOGGER.error("No CloudServiceAPI instance found!")
            return

        device_data = await cloud_api.async_get_elements_data()
        water_data = await cloud_api.async_get_installation_devices_data()

        if device_data:
            self._device_data.update(device_data)
        if water_data:
            self._device_data["water_data"] = water_data

        return self._device_data

    def get_sensors_data(self):
        """Return the list of sensor data."""

        return self._device_data["sensors"]

    def get_common_data(self):
        """Return common data shared between all sensors."""

        return self._device_data["common_data"]

    def get_water_data(self):
        """Return water data from installation devices."""

        return self._device_data["water_data"]
