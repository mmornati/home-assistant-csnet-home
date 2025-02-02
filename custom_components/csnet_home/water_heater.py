"""Water Heater Entity."""

import logging
from homeassistant.components.water_heater import WaterHeaterEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from typing import Any

from custom_components.csnet_home.const import (
    DOMAIN,
    WATER_HEATER_MAX_TEMPERATURE,
    WATER_HEATER_MIN_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Water Heater platform for CSNet Home."""
    _LOGGER.debug("Starting CSNet Home water heater setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None
    # Add sensors based on the coordinator's data
    async_add_entities(
        [
            CSNetHomeWaterHeater(
                hass,
                entry,
                sensor_data=sensor_data,
                common_data=coordinator.get_common_data()["device_status"][
                    sensor_data["device_id"]
                ],
            )
            for sensor_data in coordinator.get_sensors_data()
            if sensor_data.get("zone_id") == 3  # Add only the water heater
        ]
    )


class CSNetHomeWaterHeater(WaterHeaterEntity):
    """Representation of a Water Heater entity."""

    def __init__(self, hass, entry, sensor_data, common_data):
        """Initialize the water heater entity."""
        self.hass = hass
        self._sensor_data = sensor_data
        self._common_data = common_data
        self.entry = entry
        self._attr_name = self._sensor_data["room_name"]
        self._current_temperature = None
        self._target_temperature = None
        self._operation_mode = None
        self._available = True
        self._attr_min_temp = WATER_HEATER_MIN_TEMPERATURE
        self._attr_max_temp = WATER_HEATER_MAX_TEMPERATURE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._sensor_data["current_temperature"]

    @property
    def target_temperature(self):
        """Return the target temperature set by the user."""
        return self._sensor_data["setting_temperature"]

    @property
    def current_operation(self):
        """Return the current operation mode."""
        return self._operation_mode

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-water-heater-{self._sensor_data['room_name']}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}",
            manufacturer="Hitachi",
            model=f"{self._common_data['name']} ATW-IOT-01",
            sw_version=self._common_data["firmware"],
            identifiers={
                (
                    DOMAIN,
                    f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}",
                )
            },
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.async_set_temperature(
            self._sensor_data["zone_id"],
            self._sensor_data["parent_id"],
            temperature=temperature,
        )
        if response:
            self._sensor_data["setting_temperature"] = temperature

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.set_water_heater_status(
            self._sensor_data["zone_id"], self._sensor_data["parent_id"], operation_mode
        )
        if response:
            self._operation_mode = operation_mode
