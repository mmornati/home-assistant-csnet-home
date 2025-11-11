"""Support for CSNet Home sensors."""

import logging
from datetime import datetime, timezone
from collections import Counter

from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfVolumeFlowRate,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import STATE_ON, STATE_OFF

from .const import (
    DOMAIN,
    OTC_HEATING_TYPE_NAMES,
    OTC_COOLING_TYPE_NAMES,
    OPERATION_STATUS_MAP,
)
from .coordinator import CSNetHomeCoordinator
from .helpers import (
    detect_fan_coil_support,
    extract_heating_status,
    extract_second_cycle,
)

_LOGGER = logging.getLogger(__name__)


def _convert_unsigned_to_signed_byte(value):
    """Convert an unsigned byte (0-255) to a signed byte (-128 to 127).

    This is necessary because temperature values transmitted from the device
    may be sent as unsigned bytes (0-255), but should be interpreted as signed
    when they represent negative temperatures.

    For example:
    - 246 (unsigned) should be interpreted as -10°C (signed)
    - 250 (unsigned) should be interpreted as -6°C (signed)

    Args:
        value: The value to convert (int or None)

    Returns:
        Converted signed value or None if input is None
    """
    if value is None or not isinstance(value, int):
        return value

    # If the value is in the range 128-255, it should be converted to negative
    if value > 127:
        return value - 256

    return value


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
        # expose alarm information
        sensors.append(
            CSNetHomeSensor(coordinator, sensor_data, common_data, "alarm_code", "enum")
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "alarm_active", "binary"
            )
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "alarm_message", "enum"
            )
        )
        # Enhanced alarm information
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "alarm_code_formatted", "enum"
            )
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "alarm_origin", "enum"
            )
        )
        sensors.append(
            CSNetHomeSensor(coordinator, sensor_data, common_data, "unit_type", "enum")
        )

        # Add WiFi signal strength sensor
        sensors.append(
            CSNetHomeDeviceSensor(
                coordinator,
                sensor_data,
                common_data,
                "wifi_signal",
                SensorDeviceClass.SIGNAL_STRENGTH,
                SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                "WiFi Signal",
            )
        )

        # Add connectivity binary sensor
        sensors.append(
            CSNetHomeDeviceSensor(
                coordinator,
                sensor_data,
                common_data,
                "connectivity",
                "binary",
                None,
                "Connectivity",
            )
        )

        # Add last communication timestamp sensor
        sensors.append(
            CSNetHomeDeviceSensor(
                coordinator,
                sensor_data,
                common_data,
                "last_communication",
                SensorDeviceClass.TIMESTAMP,
                None,
                "Last Communication",
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
                "percentage",
                "%",
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
                "Outdoor Temperature",
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
                "Outdoor Average Temperature",
            )
        )

        # Weather sensor from cloud service (Issue #79)
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "weather_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Weather Temperature",
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

        # System Configuration Diagnostic sensors (Issue #78)
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "cascade_slave_mode",
                "binary",
                None,
                "Cascade Slave Mode",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "fan_coil_compatible",
                "binary",
                None,
                "Fan Coil Compatible",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "c1_thermostat_present",
                "binary",
                None,
                "C1 Thermostat Present",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "c2_thermostat_present",
                "binary",
                None,
                "C2 Thermostat Present",
            )
        )

        # OTC (Outdoor Temperature Compensation) sensors (Issue #71)
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "otc_heating_type_c1",
                "enum",
                None,
                "OTC Heating Type C1",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "otc_cooling_type_c1",
                "enum",
                None,
                "OTC Cooling Type C1",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "otc_heating_type_c2",
                "enum",
                None,
                "OTC Heating Type C2",
            )
        )
        sensors.append(
            CSNetHomeInstallationSensor(
                coordinator,
                global_device_data,
                common_data,
                "otc_cooling_type_c2",
                "enum",
                None,
                "OTC Cooling Type C2",
            )
        )

    # Add alarm history sensor (shows recent alarms from installation alarms API)
    sensors.append(CSNetHomeAlarmHistorySensor(coordinator, common_data))

    # Add alarm statistics sensors (total count, by origin, by device)
    sensors.append(
        CSNetHomeAlarmStatisticsSensor(
            coordinator, common_data, "total_alarm_count", "Total Alarms"
        )
    )
    sensors.append(
        CSNetHomeAlarmStatisticsSensor(
            coordinator, common_data, "active_alarm_count", "Active Alarms"
        )
    )
    sensors.append(
        CSNetHomeAlarmStatisticsSensor(
            coordinator, common_data, "alarm_by_origin", "Alarms by Origin"
        )
    )

    # Add compressor/outdoor unit sensors
    if installation_devices_data:
        compressor_device_data = {
            "device_name": "Compressor",
            "device_id": "compressor",
            "room_name": "Outdoor Unit",
            "parent_id": "compressor",
            "room_id": "compressor",
        }

        # Primary Compressor Sensors
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "compressor_frequency",
                "frequency",
                "Hz",
                "Compressor Frequency",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "compressor_current",
                "current",
                "A",
                "Compressor Current",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "compressor_capacity",
                None,
                None,
                "Compressor Capacity",
            )
        )

        # Compressor Temperatures
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "discharge_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Discharge Temperature",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "evaporator_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Evaporator Temperature",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "outdoor_ambient_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Outdoor Ambient Temperature",
            )
        )

        # Compressor Pressures
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "discharge_pressure",
                "pressure",
                UnitOfPressure.BAR,
                "Discharge Pressure",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "suction_pressure",
                "pressure",
                UnitOfPressure.BAR,
                "Suction Pressure",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "suction_pressure_correction",
                None,
                None,
                "Suction Pressure Correction",
            )
        )

        # Expansion Valve and Control
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "expansion_valve_opening",
                "percentage",
                "%",
                "Expansion Valve Opening (EVI)",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "outdoor_fan_rpm",
                None,
                "RPM",
                "Outdoor Fan RPM",
            )
        )

        # Outdoor Unit Information
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "operation_status",
                "enum",
                None,
                "Operation Status",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "system_status_flags",
                None,
                None,
                "System Status Flags",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "ou_code",
                "enum",
                None,
                "Outdoor Unit Code",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "ou_capacity_code",
                None,
                None,
                "Outdoor Unit Capacity Code",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "ou_pcb_software",
                None,
                None,
                "Outdoor Unit PCB Software",
            )
        )

        # Secondary Cycle Sensors (for dual-cycle systems)
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_discharge_temp",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Secondary Discharge Temperature",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_suction_temp",
                "temperature",
                UnitOfTemperature.CELSIUS,
                "Secondary Suction Temperature",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_discharge_pressure",
                "pressure",
                UnitOfPressure.BAR,
                "Secondary Discharge Pressure",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_suction_pressure",
                "pressure",
                UnitOfPressure.BAR,
                "Secondary Suction Pressure",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_compressor_frequency",
                "frequency",
                "Hz",
                "Secondary Compressor Frequency",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_expansion_valve",
                None,
                None,
                "Secondary Expansion Valve",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_compressor_current",
                "current",
                "A",
                "Secondary Compressor Current",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_current",
                "current",
                "A",
                "Secondary Current",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_superheat",
                None,
                None,
                "Secondary Superheat",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_stop_code",
                "enum",
                None,
                "Secondary Stop Code",
            )
        )
        sensors.append(
            CSNetHomeCompressorSensor(
                coordinator,
                compressor_device_data,
                common_data,
                "secondary_retry_code",
                "enum",
                None,
                "Secondary Retry Code",
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
        if self._key == "alarm_active":
            # computed from alarm_code
            alarm_code = self._sensor_data.get("alarm_code")
            return STATE_ON if alarm_code not in (None, 0) else STATE_OFF
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
            model=f"{self._common_data['name']} Remote Controller",
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
        # Special handling for weather_temperature from cloud service (Issue #79)
        if self._key == "weather_temperature":
            common_data = self._coordinator.get_common_data()
            return common_data.get("weather_temperature")

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
            # These values are already in percentage (0-100) from the API
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
            code_yutaki_s80 = 2

            if unit_model != code_yutaki_s80:
                lcd_soft = heating_status.get("lcdSoft", 0)

                # lcdSoft == 0 means not configured yet (during wizard)
                if lcd_soft == 0:
                    return STATE_ON

                # Version >= 0x0222 (546 decimal) allows control
                if lcd_soft >= 0x0222:
                    return STATE_ON

            return STATE_OFF

        # System Configuration Diagnostic sensors (Issue #78)
        # Extract systemConfigBits from heatingStatus
        if self._key in [
            "cascade_slave_mode",
            "fan_coil_compatible",
            "c1_thermostat_present",
            "c2_thermostat_present",
        ]:
            heating_status = extract_heating_status(installation_data) or {}

            if self._key == "fan_coil_compatible":
                return (
                    STATE_ON
                    if detect_fan_coil_support(installation_data)
                    else STATE_OFF
                )

            if not heating_status:
                return STATE_OFF

            system_config_bits = heating_status.get("systemConfigBits", 0)

            # Decode the specific bit based on the sensor key
            if self._key == "cascade_slave_mode":
                # Bit 0x1000 (4096) indicates cascade slave mode
                return STATE_ON if (system_config_bits & 0x1000) > 0 else STATE_OFF
            if self._key == "c1_thermostat_present":
                # Bit 0x40 (64) indicates C1 thermostat present
                return STATE_ON if (system_config_bits & 0x40) > 0 else STATE_OFF
            if self._key == "c2_thermostat_present":
                # Bit 0x80 (128) indicates C2 thermostat present
                return STATE_ON if (system_config_bits & 0x80) > 0 else STATE_OFF

        # OTC (Outdoor Temperature Compensation) sensors (Issue #71)
        if self._key in [
            "otc_heating_type_c1",
            "otc_cooling_type_c1",
            "otc_heating_type_c2",
            "otc_cooling_type_c2",
        ]:
            if not installation_data:
                return "Unknown"

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
                return "Unknown"

            # Map sensor key to API key
            otc_key_map = {
                "otc_heating_type_c1": "otcTypeHeatC1",
                "otc_cooling_type_c1": "otcTypeCoolC1",
                "otc_heating_type_c2": "otcTypeHeatC2",
                "otc_cooling_type_c2": "otcTypeCoolC2",
            }

            api_key = otc_key_map.get(self._key)
            if api_key:
                otc_value = heating_status.get(api_key)
                if otc_value is not None:
                    # Return the descriptive name for the OTC type
                    if "heating" in self._key:
                        return OTC_HEATING_TYPE_NAMES.get(
                            otc_value, f"Unknown ({otc_value})"
                        )
                    return OTC_COOLING_TYPE_NAMES.get(
                        otc_value, f"Unknown ({otc_value})"
                    )

            return "Unknown"

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
            model="HVAC System",
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


class CSNetHomeDeviceSensor(CoordinatorEntity, Entity):
    """Representation of a device-level sensor (WiFi, connectivity) from CSNet Home."""

    def __init__(
        self,
        coordinator: CSNetHomeCoordinator,
        sensor_data,
        common_data,
        key,
        device_class=None,
        unit=None,
        friendly_name=None,
    ):
        """Initialize the device sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._sensor_data = sensor_data
        self._common_data = common_data
        self._key = key
        self._device_class = device_class
        self._unit = unit
        self._friendly_name = friendly_name or key
        self._device_id = sensor_data.get("device_id")
        self._name = f"{sensor_data['device_name']} {self._friendly_name}"
        _LOGGER.debug("Configuring Device Sensor %s", self._name)

    @property
    def state(self):
        """Return the current state of the sensor."""
        # Get the device status from common_data
        device_status = self._common_data.get("device_status", {}).get(self._device_id)

        if not device_status:
            return None

        if self._key == "wifi_signal":
            # Return RSSI value (WiFi signal strength in dBm)
            return device_status.get("rssi")

        if self._key == "connectivity":
            # Calculate connectivity status based on lastComm timestamp
            # Device is considered offline if last communication was > 10 minutes ago
            last_comm = device_status.get("lastComm")
            current_time = device_status.get("currentTimeMillis")

            if last_comm is None or current_time is None:
                return STATE_OFF  # Unknown status = offline

            # Calculate time difference in milliseconds
            time_diff_ms = current_time - last_comm
            # Convert to minutes
            time_diff_minutes = time_diff_ms / 1000 / 60

            # Online if last communication was within 10 minutes
            return STATE_ON if time_diff_minutes <= 10 else STATE_OFF

        if self._key == "last_communication":
            # Return last communication timestamp as ISO 8601 datetime
            last_comm = device_status.get("lastComm")
            if last_comm is None:
                return None

            # Convert from milliseconds to seconds and create datetime
            timestamp_seconds = last_comm / 1000
            return datetime.fromtimestamp(
                timestamp_seconds, tz=timezone.utc
            ).isoformat()

        return None

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
        # Update sensor_data reference
        self._sensor_data = next(
            (
                x
                for x in self._coordinator.get_sensors_data()
                if x.get("device_id") == self._device_id
            ),
            None,
        )

        # Update common_data reference
        self._common_data = self._coordinator.get_common_data()

        if self._sensor_data:
            self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=f"{self._sensor_data['device_name']}-{self._sensor_data.get('room_name', 'Unknown')}",
            manufacturer="Hitachi",
            model=f"{self._common_data.get('device_status', {}).get(self._device_id, {}).get('name', 'Unknown')} Remote Controller",
            sw_version=self._common_data.get("device_status", {})
            .get(self._device_id, {})
            .get("firmware"),
            identifiers={
                (
                    DOMAIN,
                    f"{self._sensor_data['device_name']}-{self._sensor_data.get('room_name', 'Unknown')}",
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
        return f"{DOMAIN}-{self._sensor_data.get('room_name', 'unknown')}-{self._key}"


class CSNetHomeAlarmHistorySensor(CoordinatorEntity, Entity):
    """Sensor showing alarm history from installation alarms API."""

    def __init__(self, coordinator: CSNetHomeCoordinator, common_data):
        """Initialize the alarm history sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._common_data = common_data
        self._name = "Alarm History"

    @property
    def state(self):
        """Return the number of alarms in history."""
        alarms_data = self._coordinator.get_installation_alarms_data()
        if not alarms_data:
            return 0

        # Count alarms in the data
        alarms = alarms_data.get("alarms", [])
        return len(alarms)

    @property
    def extra_state_attributes(self):
        """Return alarm history details as attributes."""
        alarms_data = self._coordinator.get_installation_alarms_data()
        if not alarms_data:
            return {}

        alarms = alarms_data.get("alarms", [])

        # Limit to most recent 10 alarms
        recent_alarms = alarms[:10] if len(alarms) > 10 else alarms

        # Format alarm history for display
        alarm_list = []
        for alarm in recent_alarms:
            alarm_entry = {
                "code": alarm.get("code"),
                "description": alarm.get("description"),
                "timestamp": alarm.get("timestamp"),
                "device": alarm.get("device"),
            }
            alarm_list.append(alarm_entry)

        return {
            "recent_alarms": alarm_list,
            "total_alarms": len(alarms),
            "last_updated": alarms_data.get("last_updated"),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self._common_data = self._coordinator.get_common_data()
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name="Installation Alarms",
            manufacturer="Hitachi",
            model="CSNet Home Installation",
            identifiers={(DOMAIN, "installation_alarms")},
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-installation-alarm-history"


class CSNetHomeAlarmStatisticsSensor(CoordinatorEntity, Entity):
    """Sensor showing alarm statistics."""

    def __init__(
        self,
        coordinator: CSNetHomeCoordinator,
        common_data,
        statistic_type: str,
        friendly_name: str,
    ):
        """Initialize the alarm statistics sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._common_data = common_data
        self._statistic_type = statistic_type
        self._name = friendly_name

    @property
    def state(self):
        """Return the statistic value."""
        sensors = self._coordinator.get_sensors_data()

        if self._statistic_type == "total_alarm_count":
            # Count all sensors that have ever had an alarm (alarm_code != 0)
            # This is the current active alarm count
            return sum(
                1
                for sensor in sensors
                if sensor.get("alarm_code") and sensor.get("alarm_code") != 0
            )

        if self._statistic_type == "active_alarm_count":
            # Count currently active alarms
            return sum(
                1
                for sensor in sensors
                if sensor.get("alarm_code") and sensor.get("alarm_code") != 0
            )

        if self._statistic_type == "alarm_by_origin":
            # Count alarms by origin
            origins = [
                sensor.get("alarm_origin")
                for sensor in sensors
                if sensor.get("alarm_code")
                and sensor.get("alarm_code") != 0
                and sensor.get("alarm_origin")
            ]
            if not origins:
                return 0
            # Return count of most common origin
            origin_counts = Counter(origins)
            return origin_counts.most_common(1)[0][1] if origin_counts else 0

        return 0

    @property
    def extra_state_attributes(self):
        """Return detailed statistics as attributes."""
        sensors = self._coordinator.get_sensors_data()
        active_alarms = [
            sensor
            for sensor in sensors
            if sensor.get("alarm_code") and sensor.get("alarm_code") != 0
        ]

        if self._statistic_type == "total_alarm_count":
            return {
                "active_devices": [
                    {
                        "device": sensor.get("device_name"),
                        "room": sensor.get("room_name"),
                        "code": sensor.get("alarm_code"),
                        "formatted_code": sensor.get("alarm_code_formatted"),
                    }
                    for sensor in active_alarms
                ]
            }

        if self._statistic_type == "active_alarm_count":
            return {
                "devices_with_alarms": [
                    f"{sensor.get('device_name')} - {sensor.get('room_name')}"
                    for sensor in active_alarms
                ]
            }

        if self._statistic_type == "alarm_by_origin":
            origins = [
                sensor.get("alarm_origin")
                for sensor in active_alarms
                if sensor.get("alarm_origin")
            ]
            origin_counts = Counter(origins)
            return {
                "origin_distribution": dict(origin_counts),
                "most_common_origin": (
                    origin_counts.most_common(1)[0][0] if origin_counts else None
                ),
            }

        return {}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self._common_data = self._coordinator.get_common_data()
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name="Alarm Statistics",
            manufacturer="Hitachi",
            model="CSNet Home Statistics",
            identifiers={(DOMAIN, "alarm_statistics")},
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-{self._statistic_type}"


class CSNetHomeCompressorSensor(CoordinatorEntity, Entity):
    """Representation of a compressor/outdoor unit sensor from CSNet Home."""

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
        """Initialize the compressor sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._device_data = device_data
        self._common_data = common_data
        self._key = key
        self._device_class = device_class
        self._unit = unit
        self._friendly_name = friendly_name or key
        self._name = f"{device_data['device_name']} {device_data['room_name']} {self._friendly_name}"
        _LOGGER.debug("Configuring Compressor Sensor %s", self._name)

    def _get_heating_status(self):
        """Get heatingStatus from installation devices data."""
        installation_data = self._coordinator.get_installation_devices_data()
        return extract_heating_status(installation_data)

    def _get_second_cycle(self):
        """Get secondCycle from installation devices data."""
        installation_data = self._coordinator.get_installation_devices_data()
        return extract_second_cycle(installation_data)

    @property
    def state(self):
        """Return the current state of the sensor."""
        heating_status = self._get_heating_status()
        if not heating_status:
            return None

        # Primary compressor metrics
        if self._key == "compressor_frequency":
            return heating_status.get("ouHz")

        if self._key == "compressor_current":
            return heating_status.get("ouCurrent")

        if self._key == "compressor_capacity":
            return heating_status.get("unitCapacity")

        # Temperatures
        if self._key == "discharge_temperature":
            return _convert_unsigned_to_signed_byte(
                heating_status.get("ouDischargeTemperature")
            )

        if self._key == "evaporator_temperature":
            return _convert_unsigned_to_signed_byte(
                heating_status.get("ouEvapTemperature")
            )

        if self._key == "outdoor_ambient_temperature":
            return _convert_unsigned_to_signed_byte(
                heating_status.get("ouAmbientTemperature")
            )

        # Pressures
        if self._key == "discharge_pressure":
            value = heating_status.get("ouDischargePress")
            # Pressure conversion if needed (assuming value is already in bar)
            return value

        if self._key == "suction_pressure":
            value = heating_status.get("ouSuctionPress")
            # Pressure conversion if needed (assuming value is already in bar)
            return value

        if self._key == "suction_pressure_correction":
            return heating_status.get("ouSuctionPressCorrection")

        # Expansion valve and control
        if self._key == "expansion_valve_opening":
            # evi is the expansion valve opening (0-100%)
            return heating_status.get("evi")

        if self._key == "outdoor_fan_rpm":
            value = heating_status.get("fanRPM")
            # -1 indicates no data or unavailable
            return value if value != -1 else None

        # Outdoor unit information
        if self._key == "operation_status":
            value = heating_status.get("operationStatus")
            if value is None:
                return None
            return OPERATION_STATUS_MAP.get(value, f"Unknown ({value})")

        if self._key == "system_status_flags":
            # Return as hex string for easier interpretation
            value = heating_status.get("systemStatus2Flags")
            return f"0x{value:04X}" if value is not None else None

        if self._key == "ou_code":
            value = heating_status.get("ouCode")
            # Outdoor unit codes
            ou_code_map = {
                0: "Unknown",
                1: "RAS-1",
                2: "RAS-2",
                3: "Yutaki",
                4: "RAD",
            }
            return ou_code_map.get(value, f"Code {value}")

        if self._key == "ou_capacity_code":
            return heating_status.get("ouCapacityCode")

        if self._key == "ou_pcb_software":
            value = heating_status.get("ouPcbSoft")
            # -1 indicates no data
            return value if value != -1 else None

        # Secondary cycle sensors
        second_cycle = self._get_second_cycle()
        if not second_cycle:
            # If no secondary cycle data, return None
            if self._key.startswith("secondary_"):
                return None
        else:
            if self._key == "secondary_discharge_temp":
                # 0°C is a valid temperature reading, don't filter it out
                return _convert_unsigned_to_signed_byte(
                    second_cycle.get("dischargeTemp")
                )

            if self._key == "secondary_suction_temp":
                return _convert_unsigned_to_signed_byte(second_cycle.get("suctionTemp"))

            if self._key == "secondary_discharge_pressure":
                value = second_cycle.get("dischargePressure")
                # 127 seems to be a default/invalid value
                return value if value != 127 else None

            if self._key == "secondary_suction_pressure":
                value = second_cycle.get("suctionPressure")
                # 127 seems to be a default/invalid value
                return value if value != 127 else None

            if self._key == "secondary_compressor_frequency":
                return second_cycle.get("compressorFreq")

            if self._key == "secondary_expansion_valve":
                value = second_cycle.get("expansionValve")
                # 255 seems to be a default/invalid value
                return value if value != 255 else None

            if self._key == "secondary_compressor_current":
                return second_cycle.get("compressorCurrent")

            if self._key == "secondary_current":
                return second_cycle.get("secondaryCurrent")

            if self._key == "secondary_superheat":
                return second_cycle.get("teSH")

            if self._key == "secondary_stop_code":
                value = second_cycle.get("stopCode")
                return value if value != 0 else "Running"

            if self._key == "secondary_retry_code":
                value = second_cycle.get("retryCode")
                return value if value != 0 else "Normal"

        return None

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for the sensor."""
        return self._unit

    @property
    def extra_state_attributes(self):
        """Return additional attributes for certain sensors."""
        if self._key == "system_status_flags":
            heating_status = self._get_heating_status()
            if heating_status:
                flags = heating_status.get("systemStatus2Flags", 0)
                # Decode individual bits
                return {
                    "raw_value": flags,
                    "hex_value": f"0x{flags:04X}",
                    "cascade_slave": bool(flags & 0x1000),
                    "fan_coil_mode": bool(flags & 0x2000),
                    "c1_thermostat": bool(flags & 0x40),
                    "c2_thermostat": bool(flags & 0x80),
                }

        if self._key == "operation_status":
            heating_status = self._get_heating_status()
            if heating_status:
                raw_value = heating_status.get("operationStatus")
                return {
                    "raw_value": raw_value,
                    "status_text": OPERATION_STATUS_MAP.get(
                        raw_value, f"Unknown ({raw_value})"
                    ),
                    "defrosting": bool(heating_status.get("defrosting", 0)),
                }

        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        heating_status = self._get_heating_status()
        ou_model = "Unknown"
        ou_software = "Unknown"

        if heating_status:
            ou_code = heating_status.get("ouCode", 0)
            ou_code_map = {
                0: "Unknown",
                1: "RAS-1",
                2: "RAS-2",
                3: "Yutaki",
                4: "RAD",
            }
            ou_model = ou_code_map.get(ou_code, f"Code {ou_code}")

            ou_pcb = heating_status.get("ouPcbSoft", -1)
            if ou_pcb != -1:
                ou_software = f"0x{ou_pcb:04X}"

        return DeviceInfo(
            name=f"{self._device_data['device_name']} {self._device_data['room_name']}",
            manufacturer="Hitachi",
            model=f"{ou_model} Outdoor Unit",
            sw_version=ou_software,
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
        return f"{DOMAIN}-compressor-{self._key}"
