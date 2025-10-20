"""Test CSNet Home sensors."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import STATE_OFF, STATE_ON, UnitOfTemperature

from custom_components.csnet_home.sensor import (
    CSNetHomeSensor,
    CSNetHomeInstallationSensor,
)


def build_context():
    """Build minimal coordinator/sensor_data/common_data for tests."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
        "mode": 1,
        "on_off": 1,
        "doingBoost": False,
        "current_temperature": 19.5,
        "setting_temperature": 20.0,
    }
    common = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
    )
    return coordinator, sensor_data, common


def test_state_mode_and_on_off_mapping():
    """Map mode to HA HVACMode and on_off to HA binary states."""
    coordinator, sensor_data, common = build_context()

    # mode sensor
    s = CSNetHomeSensor(coordinator, sensor_data, common, "mode", "enum")
    assert s.state == HVACMode.HEAT
    sensor_data["mode"] = 0
    assert s.state == HVACMode.COOL
    sensor_data["mode"] = 2
    assert s.state == HVACMode.OFF

    # on_off sensor
    s2 = CSNetHomeSensor(coordinator, sensor_data, common, "on_off", "enum")
    sensor_data["on_off"] = 1
    assert s2.state == STATE_ON
    sensor_data["on_off"] = 0
    assert s2.state == STATE_OFF


def test_metadata_and_identity():
    """Expose device_class/unit, device_info and unique_id/name."""
    coordinator, sensor_data, common = build_context()
    s = CSNetHomeSensor(
        coordinator,
        sensor_data,
        common,
        "current_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
    )
    assert s.device_class == "temperature"
    assert s.unit_of_measurement == UnitOfTemperature.CELSIUS
    assert sensor_data["room_name"] in s.unique_id
    assert s.name.endswith("current_temperature")

    info = s.device_info
    assert info["manufacturer"] == "Hitachi"
    assert common["firmware"] in info["sw_version"]


def test_handle_coordinator_update():
    """Refresh internal sensor_data on coordinator update."""
    coordinator, sensor_data, common = build_context()
    s = CSNetHomeSensor(coordinator, sensor_data, common, "setting_temperature")
    # avoid HA write call (Entity hass is not set in unit tests here)
    s.async_write_ha_state = MagicMock()
    # simulate change in coordinator data
    sensor_data["setting_temperature"] = 21.0
    s._handle_coordinator_update()
    assert s.state == 21.0


def test_installation_sensor():
    """Test installation sensor functionality."""
    device_data = {
        "device_name": "Installation",
        "device_id": "global",
        "room_name": "Global",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Mock installation devices data
    installation_data = {
        "waterSpeed": 100,
        "waterDebit": 3.9,
        "inWaterTemperature": 20,
        "outWaterTemperature": 20,
        "setWaterTemperatureTTWO": 23,
        "waterPressure": 4.48,
        "outExchangerWaterTemperature": 20,
        "defrost": True,
        "mixValvePosition": 100,
        "externalTemperature": 14,
        "meanExternalTemperature": 15,
        "workingElectricHeater": "Stopped",
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test water speed sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_speed",
        "water_speed",
        "m/s",
        "Water Speed",
    )
    assert s.state == 1.0  # 100% converted to 1.0
    assert s.unit_of_measurement == "m/s"
    assert s.name == "Installation Global Water Speed"

    # Test water debit sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_debit",
        "water_debit",
        "m³/h",
        "Water Debit",
    )
    assert s.state == 3.9
    assert s.unit_of_measurement == "m³/h"

    # Test defrost sensor
    s = CSNetHomeInstallationSensor(
        coordinator, device_data, common_data, "defrost", "binary", None, "Defrost"
    )
    assert s.state == STATE_ON

    # Test working electric heater sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "working_electric_heater",
        "enum",
        None,
        "Working Electric Heater",
    )
    assert s.state == "Stopped"


def test_installation_sensor_edge_cases():
    """Test installation sensor edge cases and data conversion."""
    device_data = {
        "device_name": "Installation",
        "device_id": "global",
        "room_name": "Global",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with different data formats
    installation_data = {
        "water_speed": 50,  # Different key name
        "water_debit": 2.5,
        "inlet_temp": 18,  # Different key name
        "outlet_temp": 22,  # Different key name
        "pressure": 3.2,  # Different key name
        "defrost": False,
        "valve_position": 75,  # Different key name
        "outdoor_temp": 12,  # Different key name
        "avg_outdoor_temp": 13,  # Different key name
        "electric_heater_status": "Running",  # Different key name
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test water speed with different key name
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_speed",
        "water_speed",
        "m/s",
        "Water Speed",
    )
    assert s.state == 0.5  # 50% converted to 0.5

    # Test defrost with False value
    s = CSNetHomeInstallationSensor(
        coordinator, device_data, common_data, "defrost", "binary", None, "Defrost"
    )
    assert s.state == STATE_OFF

    # Test working electric heater with string value
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "working_electric_heater",
        "enum",
        None,
        "Working Electric Heater",
    )
    assert s.state == "Running"

    # Test mix valve position with different key name
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "mix_valve_position",
        "percentage",
        "%",
        "Mix Valve Position",
    )
    assert s.state == 0.75  # 75% converted to 0.75


def test_installation_sensor_no_data():
    """Test installation sensor when no data is available."""
    device_data = {
        "device_name": "Installation",
        "device_id": "global",
        "room_name": "Global",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with empty data
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {},
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_speed",
        "water_speed",
        "m/s",
        "Water Speed",
    )
    assert s.state is None

    # Test with None data
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: None,
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_speed",
        "water_speed",
        "m/s",
        "Water Speed",
    )
    assert s.state is None


def test_installation_sensor_nested_data():
    """Test installation sensor with nested device data."""
    device_data = {
        "device_name": "Installation",
        "device_id": "global",
        "room_name": "Global",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with nested devices structure
    installation_data = {
        "devices": [
            {
                "waterSpeed": 80,
                "defrost": True,
                "workingElectricHeater": "Running",
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test water speed from nested data
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_speed",
        "water_speed",
        "m/s",
        "Water Speed",
    )
    assert s.state == 0.8  # 80% converted to 0.8

    # Test defrost from nested data
    s = CSNetHomeInstallationSensor(
        coordinator, device_data, common_data, "defrost", "binary", None, "Defrost"
    )
    assert s.state == STATE_ON

    # Test working electric heater from nested data
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "working_electric_heater",
        "enum",
        None,
        "Working Electric Heater",
    )
    assert s.state == "Running"


def test_installation_sensor_metadata():
    """Test installation sensor metadata and properties."""
    device_data = {
        "device_name": "Installation",
        "device_id": "global",
        "room_name": "Global",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {"waterSpeed": 100},
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_speed",
        "water_speed",
        "m/s",
        "Water Speed",
    )

    # Test device info
    device_info = s.device_info
    assert device_info["manufacturer"] == "Hitachi"
    assert device_info["model"] == "Hitachi Installation Installation"
    assert device_info["sw_version"] == "1.0.0"

    # Test unique id
    assert s.unique_id == "csnet_home-installation-water_speed"

    # Test name
    assert s.name == "Installation Global Water Speed"

    # Test device class and unit
    assert s.device_class == "water_speed"
    assert s.unit_of_measurement == "m/s"
