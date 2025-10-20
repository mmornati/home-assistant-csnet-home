"""Support for CSNet Home sensors."""

import logging

from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfVolumeFlowRate,
    UnitOfSpeed,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import STATE_ON, STATE_OFF

from .const import DOMAIN
from .coordinator import CSNetHomeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors for CSNet Home."""
    _LOGGER.debug("Starting CSNet Home sensor setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None

    sensors = []
    for sensor_data in coordinator.get_sensors_data():
        common_data = coordinator.get_common_data()["device_status"][
            sensor_data["device_id"]
        ]

        sensors.append(
            CSNetHomeSensor(
                coordinator,
                sensor_data,
                common_data,
                "current_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
            )
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator,
                sensor_data,
                common_data,
                "setting_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
            )
        )
        sensors.append(
            CSNetHomeSensor(coordinator, sensor_data, common_data, "mode", "enum")
        )
        sensors.append(
            CSNetHomeSensor(coordinator, sensor_data, common_data, "on_off", "enum")
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "doingBoost", "binary"
            )
        )

    # Add installation devices sensors
    installation_devices_data = coordinator.get_installation_devices_data()
    if installation_devices_data:
        # Create a global device for installation-level sensors
        global_device_data = {
            "device_name": "Installation",
            "device_id": "global",
            "room_name": "Global",
            "parent_id": "global",
            "room_id": "global",
        }

        # Water-related sensors
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "water_speed",
                "water_speed",
                UnitOfSpeed.METERS_PER_SECOND,
                "Water Speed",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "water_debit",
                "water_debit",
                UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                "Water Debit",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "in_water_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "In Water Temperature",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "out_water_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Out Water Temperature",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "set_water_temperature_ttwo",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Set Water Temperature TTWO",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "water_pressure",
                "pressure",
                UnitOfPressure.BAR,
                "Water Pressure",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "out_exchanger_water_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Out Exchanger Water Temperature",
            )
        )

        # Heat device sensors
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "defrost",
                "binary",
                None,
                "Defrost",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "mix_valve_position",
                "percentage",
                "%",
                "Mix Valve Position",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "external_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "External Temperature",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "mean_external_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Mean External Temperature",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "working_electric_heater",
                "enum",
                None,
                "Working Electric Heater",
            )
        )

    async_add_entities(sensors)


class CSNetHomeSensor(CoordinatorEntity, Entity):
    """Representation of a sensor from the CSNet Home integration."""

    def __init__(
        self,
        coordinator: CSNetHomeCoordinator,
        sensor_data,
        common_data,
        key,
        device_class=None,
        unit=None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._sensor_data = sensor_data
        self._common_data = common_data
        self._key = key
        self._device_class = device_class
        self._unit = unit
        self._name = f"{sensor_data['device_name']} {sensor_data['room_name']} {key}"
        _LOGGER.debug("Configuring Sensor %s", self._name)

    @property
    def state(self):
        """Return the current temperature as the state of the sensor."""
        value = self._sensor_data.get(self._key)
        if self._key == "mode":
            if value == 0:
                return HVACMode.COOL
            if value == 1:
                return HVACMode.HEAT
            return HVACMode.OFF
        if self._key == "on_off":
            return STATE_ON if value == 1 else STATE_OFF
        return value

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for the sensor."""
        return self._unit

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self._sensor_data = next(
            (
                x
                for x in self._coordinator.get_sensors_data()
                if x.get("room_name") in self._name
            ),
            None,
        )
        if self._sensor_data:
            self.async_write_ha_state()

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

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self._sensor_data['room_name']}-{self._key}"


class CSNetHomeInstallationSensor(CoordinatorEntity, Entity):
    """Representation of an installation-level sensor from the CSNet Home integration."""

    def __init__(
        self,
        coordinator: CSNetHomeCoordinator,
        device_data,
        common_data,
        key,
        device_class=None,
        unit=None,
        friendly_name=None,
    ):
        """Initialize the installation sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._device_data = device_data
        self._common_data = common_data
        self._key = key
        self._device_class = device_class
        self._unit = unit
        self._friendly_name = friendly_name or key
        self._name = f"{device_data['device_name']} {device_data['room_name']} {self._friendly_name}"
        _LOGGER.debug("Configuring Installation Sensor %s", self._name)

    @property
    def state(self):
        """Return the current state of the sensor."""
        installation_data = self._coordinator.get_installation_devices_data()

        # Map the sensor keys to potential API response keys
        # These mappings are based on the user's description and common naming patterns
        key_mappings = {
            "water_speed": ["waterSpeed", "water_speed", "speed"],
            "water_debit": ["waterDebit", "water_debit", "debit", "flow_rate"],
            "in_water_temperature": [
                "inWaterTemperature",
                "in_water_temperature",
                "inlet_temp",
            ],
            "out_water_temperature": [
                "outWaterTemperature",
                "out_water_temperature",
                "outlet_temp",
            ],
            "set_water_temperature_ttwo": [
                "setWaterTemperatureTTWO",
                "set_water_temperature_ttwo",
                "ttwo_temp",
            ],
            "water_pressure": ["waterPressure", "water_pressure", "pressure"],
            "out_exchanger_water_temperature": [
                "outExchangerWaterTemperature",
                "out_exchanger_water_temperature",
                "exchanger_outlet_temp",
            ],
            "defrost": ["defrost", "defrost_mode", "defrosting"],
            "mix_valve_position": [
                "mixValvePosition",
                "mix_valve_position",
                "valve_position",
            ],
            "external_temperature": [
                "externalTemperature",
                "external_temperature",
                "outdoor_temp",
            ],
            "mean_external_temperature": [
                "meanExternalTemperature",
                "mean_external_temperature",
                "avg_outdoor_temp",
            ],
            "working_electric_heater": [
                "workingElectricHeater",
                "working_electric_heater",
                "electric_heater_status",
            ],
        }

        # Try to find the value using different possible key names
        possible_keys = key_mappings.get(self._key, [self._key])
        value = None

        for possible_key in possible_keys:
            if isinstance(installation_data, dict):
                value = installation_data.get(possible_key)
                if value is not None:
                    break
                # Also try nested objects
                for device in installation_data.get("devices", []):
                    if isinstance(device, dict):
                        value = device.get(possible_key)
                        if value is not None:
                            break
                    if value is not None:
                        break
            if value is not None:
                break

        # Handle special cases for different sensor types
        if self._key == "defrost":
            return STATE_ON if value else STATE_OFF
        if self._key == "working_electric_heater":
            if isinstance(value, str):
                return value
            return "Stopped" if not value else "Running"
        if self._key in ["water_speed", "mix_valve_position"]:
            # Convert percentage to decimal if needed
            if isinstance(value, (int, float)) and value > 1:
                return value / 100
            return value
        if self._key == "water_debit":
            # Convert to m3/h if needed (assuming the API might return in different units)
            if isinstance(value, (int, float)):
                return value
            return value
        if self._key in ["water_pressure"]:
            # Convert to bar if needed
            if isinstance(value, (int, float)):
                return value
            return value

        return value

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for the sensor."""
        return self._unit

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=f"{self._device_data['device_name']}-{self._device_data['room_name']}",
            manufacturer="Hitachi",
            model=f"{self._common_data.get('name', 'Unknown')} Installation",
            sw_version=self._common_data.get("firmware"),
            identifiers={
                (
                    DOMAIN,
                    f"{self._device_data['device_name']}-{self._device_data['room_name']}",
                )
            },
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-installation-{self._key}"
