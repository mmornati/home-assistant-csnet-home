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
            "device_name": "System",
            "device_id": "global",
            "room_name": "Controller",
            "parent_id": "global",
            "room_id": "global",
        }

        # Water-related sensors
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "pump_speed",
                "water_speed",
                UnitOfSpeed.METERS_PER_SECOND,
                "Pump Speed",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "water_flow",
                "water_debit",
                UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                "Water Flow",
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
                "set_water_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Set Water Temperature",
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
                "gas_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Gas Temperature",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "liquid_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Liquid Temperature",
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

        # Central Control Configuration sensors
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "central_config",
                "enum",
                None,
                "Central Config",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "lcd_software_version",
                None,
                None,
                "LCD Software Version",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "unit_model",
                "enum",
                None,
                "Unit Model",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "central_control_enabled",
                "binary",
                None,
                "Central Control Enabled",
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

        # Map the sensor keys to actual API response keys from indoors/heatingStatus
        key_mappings = {
            "pump_speed": ["pumpSpeed"],
            "water_flow": ["waterFlow"],
            "in_water_temperature": ["waterInletTemp"],
            "out_water_temperature": ["waterOutletTemp"],
            "set_water_temperature": ["waterTempSetting"],
            "water_pressure": ["waterPressure"],
            "defrost": ["defrosting"],
            "mix_valve_position": ["mixingValveOpening"],
            "external_temperature": ["outdoorAmbientTemp"],
            "mean_external_temperature": ["outdoorAmbientAverageTemp"],
            "gas_temperature": ["gasTemp"],
            "liquid_temperature": ["liquidTemp"],
            # Central control configuration
            "central_config": ["centralConfig"],
            "lcd_software_version": ["lcdSoft"],
            "unit_model": ["unitModel"],
        }

        # Try to find the value using different possible key names
        possible_keys = key_mappings.get(self._key, [self._key])
        value = None

        # Look in the correct API response structure: data[0].indoors[0].heatingStatus
        if isinstance(installation_data, dict):
            # First try direct access
            for possible_key in possible_keys:
                value = installation_data.get(possible_key)
                if value is not None:
                    break

            # If not found, try in data[0].indoors[0].heatingStatus structure
            if value is None:
                data_array = installation_data.get("data", [])
                if isinstance(data_array, list) and len(data_array) > 0:
                    first_device = data_array[0]
                    if isinstance(first_device, dict):
                        indoors_array = first_device.get("indoors", [])
                        if isinstance(indoors_array, list) and len(indoors_array) > 0:
                            first_indoors = indoors_array[0]
                            if isinstance(first_indoors, dict):
                                heating_status = first_indoors.get("heatingStatus", {})
                                if isinstance(heating_status, dict):
                                    for possible_key in possible_keys:
                                        value = heating_status.get(possible_key)
                                        if value is not None:
                                            break

        # Handle special cases for different sensor types
        if self._key == "defrost":
            # defrosting: 0 = off, 1 = on
            return STATE_ON if value == 1 else STATE_OFF
        if self._key == "water_flow":
            # waterFlow value must be divided by 10 to have the right measurement unit
            if isinstance(value, (int, float)):
                return value / 10
            return value
        if self._key == "water_pressure":
            # waterPressure: app shows 4.48bar, value is 224, so divide by 50
            if isinstance(value, (int, float)):
                return value / 50
            return value
        if self._key in ["pump_speed", "mix_valve_position"]:
            # Convert percentage to decimal if needed
            if isinstance(value, (int, float)) and value > 1:
                return value / 100
            return value
        
        # Central control configuration sensors
        if self._key == "unit_model":
            # Decode unit model codes
            unit_models = {
                0: "Yutaki S",
                1: "Yutaki SC",
                2: "Yutaki S80",
                3: "Yutaki M",
                4: "Yutaki SC Lite",
                5: "Yutampo",
            }
            return unit_models.get(value, f"Unknown ({value})")
        
        if self._key == "lcd_software_version":
            # Format as hex version (e.g., 0x0222 = v2.34)
            if isinstance(value, int) and value > 0:
                return f"0x{value:04X}"
            return value
        
        if self._key == "central_config":
            # Decode central config values
            config_names = {
                0: "Unit Only",
                1: "RT Only",
                2: "Unit & RT",
                3: "Total Control",
                4: "Total Control+",
            }
            decoded = config_names.get(value, f"Unknown ({value})")
            if value is not None and value < 3:
                decoded += " ⚠️"  # Warning for insufficient control
            return decoded
        
        if self._key == "central_control_enabled":
            # Calculate if central control is properly configured
            # Based on JavaScript function isCentralWellConfigured()
            if not isinstance(installation_data, dict):
                return STATE_OFF
            
            heating_status = None
            data_array = installation_data.get("data", [])
            if isinstance(data_array, list) and len(data_array) > 0:
                first_device = data_array[0]
                if isinstance(first_device, dict):
                    indoors_array = first_device.get("indoors", [])
                    if isinstance(indoors_array, list) and len(indoors_array) > 0:
                        first_indoors = indoors_array[0]
                        if isinstance(first_indoors, dict):
                            heating_status = first_indoors.get("heatingStatus", {})
            
            if not heating_status:
                return STATE_OFF
            
            central_config = heating_status.get("centralConfig", 0)
            
            # Central config >= 3 means "Total" control is enabled
            if central_config >= 3:
                return STATE_ON
            
            # For non-S80 models, check LCD software version
            unit_model = heating_status.get("unitModel", 0)
            CODE_YUTAKI_S80 = 2
            
            if unit_model != CODE_YUTAKI_S80:
                lcd_soft = heating_status.get("lcdSoft", 0)
                
                # lcdSoft == 0 means not configured yet (during wizard)
                if lcd_soft == 0:
                    return STATE_ON
                
                # Version >= 0x0222 (546 decimal) allows control
                if lcd_soft >= 0x0222:
                    return STATE_ON
            
            return STATE_OFF

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
