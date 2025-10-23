"""Support for CSNet Home sensors."""

import logging
from datetime import datetime, timezone
from collections import Counter

from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfVolumeFlowRate,
    UnitOfSpeed,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.sensor import SensorDeviceClass
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

            system_config_bits = heating_status.get("systemConfigBits", 0)

            # Decode the specific bit based on the sensor key
            if self._key == "cascade_slave_mode":
                # Bit 0x1000 (4096) indicates cascade slave mode
                return STATE_ON if (system_config_bits & 0x1000) > 0 else STATE_OFF
            if self._key == "fan_coil_compatible":
                # Bit 0x2000 (8192) indicates fan coil compatibility
                return STATE_ON if (system_config_bits & 0x2000) > 0 else STATE_OFF
            if self._key == "c1_thermostat_present":
                # Bit 0x40 (64) indicates C1 thermostat present
                return STATE_ON if (system_config_bits & 0x40) > 0 else STATE_OFF
            if self._key == "c2_thermostat_present":
                # Bit 0x80 (128) indicates C2 thermostat present
                return STATE_ON if (system_config_bits & 0x80) > 0 else STATE_OFF

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
