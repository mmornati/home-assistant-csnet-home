"""Create a Climate Component for Home Assistant."""

import logging

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    HEATING_MAX_TEMPERATURE,
    HEATING_MIN_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the climate platform for CSNet Home."""
    _LOGGER.debug("Starting CSNet Home climate setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None
    # Add sensors based on the coordinator's data
    async_add_entities(
        [
            CSNetHomeClimate(
                hass,
                entry,
                sensor_data=sensor_data,
                common_data=coordinator.get_common_data()["device_status"][
                    sensor_data["device_id"]
                ],
            )
            for sensor_data in coordinator.get_sensors_data()
            if sensor_data.get("zone_id") != 3  # Skip if zone_id is 3
        ]
    )


class CSNetHomeClimate(ClimateEntity):
    """Representation of a thermostat (climate) entity."""

    def __init__(self, hass, entry, sensor_data, common_data):
        """Initialize the thermostat entity."""
        self.hass = hass
        self._sensor_data = sensor_data
        self._common_data = common_data
        self._attr_name = self._sensor_data["room_name"]
        self.entry = entry
        self._attr_min_temp = HEATING_MIN_TEMPERATURE
        self._attr_max_temp = HEATING_MAX_TEMPERATURE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
        self._attr_preset_modes = ["comfort", "eco"]
        if self._sensor_data["ecocomfort"] and self._sensor_data["ecocomfort"] == 0:
            self._attr_preset_mode = "eco"
        else:
            self._attr_preset_mode = "comfort"
        self._attr_supported_features = (
            self.supported_features.PRESET_MODE
            | self.supported_features.TARGET_TEMPERATURE
            | self.supported_features.TURN_ON
            | self.supported_features.TURN_OFF
        )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._sensor_data["current_temperature"]

    @property
    def hvac_mode(self):
        """Return the current operation mode."""
        # Operation mode can be COOL, HEAT, AUTO, OFF
        if self._sensor_data["on_off"] & self._sensor_data["on_off"] == 0:
            return "off"
        return "heat"

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self._sensor_data["ecocomfort"] & self._sensor_data["ecocomfort"] == 0:
            return "eco"
        return "comfort"

    @property
    def target_temperature(self):
        """Return the target temperature set by the user."""
        return self._sensor_data["setting_temperature"]

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-climate-{self._sensor_data['room_name']}"

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

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature for a room."""
        temperature = kwargs.get("temperature")
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.async_set_temperature(
            self._sensor_data["zone_id"],
            self._sensor_data["parent_id"],
            temperature=temperature,
        )
        if response:
            self._sensor_data["setting_temperature"] = temperature

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.async_on_off(
            self._sensor_data["zone_id"], self._sensor_data["parent_id"], hvac_mode
        )
        if response:
            self._sensor_data["on_off"] = 1 if hvac_mode == HVACMode.HEAT else 0

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.set_preset_modes(
            self._sensor_data["zone_id"], self._sensor_data["parent_id"], preset_mode
        )
        if response:
            self._sensor_data["ecocomfort"] = 1 if preset_mode == "eco" else 0

    async def async_update(self):
        """Update the thermostat data from the API."""
        _LOGGER.debug(
            "Updating CSNet Home refresh request %s", self._sensor_data["room_name"]
        )
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        if not coordinator:
            _LOGGER.error("No coordinator instance found!")
        await coordinator.async_request_refresh()
        self._sensor_data = next(
            (
                x
                for x in coordinator.get_sensors_data()
                if x.get("room_name") == self._attr_name
            ),
            None,
        )
        self._common_data = coordinator.get_common_data()
