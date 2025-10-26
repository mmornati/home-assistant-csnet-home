"""Water Heater Entity."""

# https://github.com/home-assistant/core/blob/dev/homeassistant/components/water_heater/__init__.py

import logging
from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import UnitOfTemperature, PRECISION_WHOLE
from homeassistant.helpers.device_registry import DeviceInfo
from typing import Any

from .const import (
    DOMAIN,
    WATER_HEATER_MAX_TEMPERATURE,
    WATER_HEATER_MIN_TEMPERATURE,
    SWIMMING_POOL_MAX_TEMPERATURE,
    SWIMMING_POOL_MIN_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Water Heater platform for CSNet Home."""
    _LOGGER.debug("Starting CSNet Home water heater setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None

    sensors_data = coordinator.get_sensors_data()

    # Include both water heater (zone_id=3) and swimming pool (zone_id=4)
    water_heater_sensors = [
        sensor for sensor in sensors_data if sensor.get("zone_id") in [3, 4]
    ]

    if not water_heater_sensors:
        _LOGGER.warning(
            "No water heater or swimming pool sensors found in coordinator data."
        )

    async_add_entities(
        CSNetHomeWaterHeater(
            hass,
            entry,
            sensor,
            coordinator.get_common_data()["device_status"].get(sensor["device_id"], {}),
        )
        for sensor in water_heater_sensors
    )


class CSNetHomeWaterHeater(WaterHeaterEntity):
    """Representation of a Water Heater entity."""

    def __init__(self, hass, entry, sensor_data, common_data):
        """Initialize the water heater entity."""
        self.hass = hass
        self.entry = entry
        self._sensor_data = sensor_data
        self._common_data = common_data
        self._available = True
        self._is_swimming_pool = sensor_data.get("zone_id") == 4

        # Set appropriate name based on zone type
        if self._is_swimming_pool:
            self._attr_name = sensor_data.get("room_name", "Unknown Swimming Pool")
        else:
            self._attr_name = sensor_data.get("room_name", "Unknown Water Heater")

        # Temperature limits will be computed dynamically from API data
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
        )

        # Swimming pools only support on/off, not eco/performance modes
        if self._is_swimming_pool:
            self._attr_operation_list = ["off", "on"]
        else:
            self._attr_operation_list = ["off", "eco", "performance"]

        # Initialize operation mode based on sensor data
        if self._is_swimming_pool:
            # Swimming pool only has on/off
            if self._sensor_data.get("on_off", 0) == 0:
                self._attr_operation_mode = "off"
            else:
                self._attr_operation_mode = "on"
        else:
            # Water heater has eco/performance modes
            if self._sensor_data.get("on_off", 0) == 0:
                self._attr_operation_mode = "off"
            elif self._sensor_data.get("doingBoost"):
                self._attr_operation_mode = "performance"
            else:
                self._attr_operation_mode = "eco"

        entity_type = "swimming-pool" if self._is_swimming_pool else "water-heater"
        self._attr_unique_id = (
            f"{DOMAIN}-{entity_type}-{sensor_data.get('room_name', 'unknown')}"
        )
        self._attr_device_info = DeviceInfo(
            name=f"{sensor_data.get('device_name', 'Unknown')}-{sensor_data.get('room_name', 'Unknown')}",
            manufacturer="Hitachi",
            model=f"{common_data.get('name', 'Unknown')} Remote Controller",
            sw_version=common_data.get("firmware"),
            identifiers={
                (
                    DOMAIN,
                    f"{sensor_data.get('device_name', 'Unknown')}-{sensor_data.get('room_name', 'Unknown')}",
                )
            },
        )

        self._update_attributes()

        _LOGGER.debug("Water heater entity initialized: %s", self._attr_name)
        _LOGGER.debug(
            "Water heater doingBoost: %s", self._sensor_data.get("doingBoost", False)
        )

    def _update_attributes(self):
        """Update the entity attributes from sensor data."""
        self._attr_current_temperature = self._sensor_data.get("current_temperature")
        self._attr_target_temperature = self._sensor_data.get("setting_temperature")

        _LOGGER.debug("_attr_current_operation: %s", self._sensor_data.get("on_off"))

        if self._is_swimming_pool:
            # Swimming pool only has on/off
            if self._sensor_data.get("on_off") == 0:
                self._attr_current_operation = "off"
            else:
                self._attr_current_operation = "on"
        else:
            # Water heater has eco/performance modes
            if self._sensor_data.get("doingBoost"):
                self._attr_current_operation = "performance"
            elif not self._sensor_data.get("doingBoost"):
                self._attr_current_operation = "eco"
            if self._sensor_data.get("on_off") == 0:
                self._attr_current_operation = "off"

    @property
    def current_operation(self) -> str | None:
        """Return current operation ie. eco, performance."""
        return self._attr_current_operation

    async def async_update(self):
        """Fetch new state data from the coordinator."""
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        sensors_data = coordinator.get_sensors_data()

        expected_zone_id = 4 if self._is_swimming_pool else 3
        for sensor in sensors_data:
            if (
                sensor.get("zone_id") == expected_zone_id
                and sensor.get("room_name") == self._attr_name
            ):
                self._sensor_data = sensor
                self._update_attributes()
                entity_type = (
                    "swimming pool" if self._is_swimming_pool else "water heater"
                )
                _LOGGER.debug("Updated %s data: %s", entity_type, self._attr_name)
                return

        entity_type = "swimming pool" if self._is_swimming_pool else "water heater"
        _LOGGER.warning(
            "No updated data found for %s: %s", entity_type, self._attr_name
        )

    @property
    def precision(self) -> float:
        """Return the precision of the system. Use whole degrees only."""
        return PRECISION_WHOLE

    @property
    def min_temp(self):
        """Return the minimum temperature from API data."""
        if self._is_swimming_pool:
            # Swimming pool has fixed minimum temperature
            return SWIMMING_POOL_MIN_TEMPERATURE

        # DHW zone_id is 3, mode is always 1 (heat) for water heater
        # Get temperature limits from API (DHW min is typically constant at 30)
        # The API doesn't return a dhwMin, so use the static constant
        return WATER_HEATER_MIN_TEMPERATURE

    @property
    def max_temp(self):
        """Return the maximum temperature from API data."""
        if self._is_swimming_pool:
            # Swimming pool has fixed maximum temperature
            return SWIMMING_POOL_MAX_TEMPERATURE

        # DHW zone_id is 3, mode is always 1 (heat) for water heater
        zone_id = 3
        mode = 1

        # Get installation devices data from coordinator
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        installation_devices_data = coordinator.get_installation_devices_data()

        # Get temperature limits from API
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        _, max_limit = cloud_api.get_temperature_limits(
            zone_id, mode, installation_devices_data
        )

        # Return API limit if available, otherwise use static default
        return max_limit if max_limit is not None else WATER_HEATER_MAX_TEMPERATURE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            _LOGGER.warning("No temperature provided for setting target temperature.")
            return

        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.async_set_temperature(
            self._sensor_data["zone_id"],
            self._sensor_data["parent_id"],
            self._sensor_data["mode"],
            temperature=temperature,
        )
        if response:
            self._sensor_data["setting_temperature"] = temperature
            self._attr_target_temperature = temperature
            _LOGGER.info("Set water heater target temperature to %s°C", temperature)
        else:
            _LOGGER.error("Failed to set water heater temperature.")

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        _LOGGER.warning("Operation mode: %s", operation_mode)
        response = await cloud_api.set_water_heater_mode(
            self._sensor_data["zone_id"], self._sensor_data["parent_id"], operation_mode
        )
        if response:
            if operation_mode == "off":
                self._sensor_data["on_off"] = 0
                self._attr_operation_mode = operation_mode
            else:
                self._sensor_data["on_off"] = 1
                if not self._is_swimming_pool:
                    # Only water heaters have doingBoost
                    self._sensor_data["doingBoost"] = operation_mode == "performance"
                self._attr_operation_mode = operation_mode

            entity_type = "swimming pool" if self._is_swimming_pool else "water heater"
            _LOGGER.info("Set %s operation : %s", entity_type, operation_mode)
        else:
            entity_type = "swimming pool" if self._is_swimming_pool else "water heater"
            _LOGGER.error("Failed to set %s operation mode.", entity_type)
