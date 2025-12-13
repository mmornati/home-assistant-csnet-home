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
    CONF_MAX_TEMP_OVERRIDE,
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

    water_heater_sensors = [
        sensor for sensor in sensors_data if sensor.get("zone_id") == 3
    ]

    if not water_heater_sensors:
        _LOGGER.warning("No water heater sensors found in coordinator data.")

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

        # Store identifiers for reliable matching when parentName is empty
        self._parent_id = sensor_data.get("parent_id")
        self._device_id = sensor_data.get("device_id")

        # Use device_name as fallback when room_name is empty (common for Yutampo)
        room_name = sensor_data.get("room_name", "").strip()
        device_name = sensor_data.get("device_name", "Unknown")
        if not room_name or room_name == "Unknown Water Heater":
            # For Yutampo water heaters, parentName is often empty
            # Use device_name with a suffix to create a unique name
            self._attr_name = f"{device_name} DHW"
            _LOGGER.debug(
                "Water heater has empty room_name, using device_name: %s", device_name
            )
        else:
            self._attr_name = room_name

        # Temperature limits will be computed dynamically from API data
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
        )
        self._attr_operation_list = ["off", "eco", "performance"]

        # Initialize operation mode based on sensor data
        # Check both onOff (from API) and on_off (normalized) for compatibility
        # Use explicit None check to handle 0 (off) correctly
        on_off = self._sensor_data.get("on_off")
        if on_off is None:
            on_off = self._sensor_data.get("onOff", 1)
        doing_boost = self._sensor_data.get("doingBoost", False)

        if on_off == 0:
            self._attr_operation_mode = "off"
        elif doing_boost:
            self._attr_operation_mode = "performance"
        else:
            self._attr_operation_mode = "eco"

        # Use parent_id and device_id for unique_id to ensure uniqueness even with empty room_name
        self._attr_unique_id = (
            f"{DOMAIN}-water-heater-{self._parent_id}-{self._device_id}"
        )

        # Use the same naming logic as _attr_name for device info
        if not room_name or room_name == "Unknown Water Heater":
            device_display_name = f"{device_name} DHW"
        else:
            device_display_name = f"{device_name}-{room_name}"

        self._attr_device_info = DeviceInfo(
            name=device_display_name,
            manufacturer="Hitachi",
            model=f"{common_data.get('name', 'Unknown')} Remote Controller",
            sw_version=common_data.get("firmware"),
            identifiers={
                (
                    DOMAIN,
                    f"{device_name}-dhw-{self._parent_id}-{self._device_id}",
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
        current_temp = self._sensor_data.get("current_temperature")
        setting_temp = self._sensor_data.get("setting_temperature")

        # Log temperature values for debugging (especially useful for Yutampo issues)
        _LOGGER.debug(
            "Water heater %s temperatures - current: %s, target: %s",
            self._attr_name,
            current_temp,
            setting_temp,
        )

        # Handle potential temperature scaling issues
        # Some API responses might return temperatures multiplied by 10
        if current_temp is not None and current_temp > 200:
            _LOGGER.warning(
                "Water heater current temperature seems scaled (value: %s), dividing by 10",
                current_temp,
            )
            current_temp = current_temp / 10.0

        if setting_temp is not None and setting_temp > 200:
            _LOGGER.warning(
                "Water heater setting temperature seems scaled (value: %s), dividing by 10",
                setting_temp,
            )
            setting_temp = setting_temp / 10.0

        self._attr_current_temperature = current_temp
        self._attr_target_temperature = setting_temp

        # Update operation mode - check both onOff and on_off for compatibility
        # Use explicit None check to handle 0 (off) correctly
        on_off = self._sensor_data.get("on_off")
        if on_off is None:
            on_off = self._sensor_data.get("onOff", 1)
        doing_boost = self._sensor_data.get("doingBoost", False)

        _LOGGER.debug(
            "Water heater operation state - on_off: %s, doingBoost: %s",
            on_off,
            doing_boost,
        )

        if on_off == 0:
            self._attr_current_operation = "off"
        elif doing_boost:
            self._attr_current_operation = "performance"
        else:
            self._attr_current_operation = "eco"

    @property
    def current_operation(self) -> str | None:
        """Return current operation ie. eco, performance."""
        return self._attr_current_operation

    async def async_update(self):
        """Fetch new state data from the coordinator."""
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        sensors_data = coordinator.get_sensors_data()

        for sensor in sensors_data:
            if sensor.get("zone_id") == 3:
                # Match by parent_id and device_id for reliable matching
                # This handles cases where room_name is empty (common for Yutampo)
                if (
                    sensor.get("parent_id") == self._parent_id
                    and sensor.get("device_id") == self._device_id
                ):
                    self._sensor_data = sensor
                    self._update_attributes()
                    _LOGGER.debug(
                        "Updated water heater data: %s (parent_id: %s, device_id: %s)",
                        self._attr_name,
                        self._parent_id,
                        self._device_id,
                    )
                    return

        _LOGGER.warning(
            "No updated data found for water heater: %s (parent_id: %s, device_id: %s)",
            self._attr_name,
            self._parent_id,
            self._device_id,
        )

    @property
    def precision(self) -> float:
        """Return the precision of the system. Use whole degrees only."""
        return PRECISION_WHOLE

    @property
    def min_temp(self):
        """Return the minimum temperature for DHW from API data."""
        # DHW zone_id is 3, mode is always 1 (heat) for water heater
        # Get temperature limits from API (DHW min is typically constant at 30)
        # The API doesn't return a dhwMin, so use the static constant
        return WATER_HEATER_MIN_TEMPERATURE

    @property
    def max_temp(self):
        """Return the maximum temperature for DHW from API data.

        Priority order:
        1. User-configured override (if set)
        2. API-provided limit from heatingStatus
        3. Default DHW maximum (80°C)
        """
        # Check for user override first
        max_temp_override = self.entry.data.get(CONF_MAX_TEMP_OVERRIDE)
        if max_temp_override is not None:
            return max_temp_override

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
                self._sensor_data["doingBoost"] = operation_mode == "performance"
                self._attr_operation_mode = operation_mode

            _LOGGER.info("Set water heater operation : %s", operation_mode)
        else:
            _LOGGER.error("Failed to set water heater operation mode.")
