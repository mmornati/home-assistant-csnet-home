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

    # Mock installation devices data with correct API response structure
    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "pumpSpeed": 100,
                            "waterFlow": 39,  # Will be divided by 10
                            "waterInletTemp": 20,
                            "waterOutletTemp": 20,
                            "waterTempSetting": 23,
                            "waterPressure": 224,  # Will be divided by 50
                            "gasTemp": 20,
                            "liquidTemp": 20,
                            "defrosting": 1,  # 1 = on, 0 = off
                            "mixingValveOpening": 100,
                            "outdoorAmbientTemp": 14,
                            "outdoorAmbientAverageTemp": 15,
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test pump speed sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "pump_speed",
        "water_speed",
        "m/s",
        "Pump Speed",
    )
    assert s.state == 1.0  # 100% converted to 1.0
    assert s.unit_of_measurement == "m/s"
    assert s.name == "Installation Global Pump Speed"

    # Test water flow sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_flow",
        "water_debit",
        "m³/h",
        "Water Flow",
    )
    assert s.state == 3.9  # 39 / 10 = 3.9
    assert s.unit_of_measurement == "m³/h"

    # Test water pressure sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_pressure",
        "pressure",
        "bar",
        "Water Pressure",
    )
    assert s.state == 4.48  # 224 / 50 = 4.48

    # Test defrost sensor
    s = CSNetHomeInstallationSensor(
        coordinator, device_data, common_data, "defrost", "binary", None, "Defrost"
    )
    assert s.state == STATE_ON  # defrosting = 1

    # Test gas temperature sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "gas_temperature",
        "temperature",
        "°C",
        "Gas Temperature",
    )
    assert s.state == 20

    # Test liquid temperature sensor
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "liquid_temperature",
        "temperature",
        "°C",
        "Liquid Temperature",
    )
    assert s.state == 20


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
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "pumpSpeed": 50,  # Will be converted to 0.5
                            "waterFlow": 25,  # Will be divided by 10 = 2.5
                            "waterInletTemp": 18,
                            "waterOutletTemp": 22,
                            "waterPressure": 160,  # Will be divided by 50 = 3.2
                            "defrosting": 0,  # 0 = off
                            "mixingValveOpening": 75,  # Will be converted to 0.75
                            "outdoorAmbientTemp": 12,
                            "outdoorAmbientAverageTemp": 13,
                            "gasTemp": 15,
                            "liquidTemp": 17,
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test pump speed with conversion
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "pump_speed",
        "water_speed",
        "m/s",
        "Pump Speed",
    )
    assert s.state == 0.5  # 50% converted to 0.5

    # Test water flow with division
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_flow",
        "water_debit",
        "m³/h",
        "Water Flow",
    )
    assert s.state == 2.5  # 25 / 10 = 2.5

    # Test water pressure with division
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_pressure",
        "pressure",
        "bar",
        "Water Pressure",
    )
    assert s.state == 3.2  # 160 / 50 = 3.2

    # Test defrost with 0 value (off)
    s = CSNetHomeInstallationSensor(
        coordinator, device_data, common_data, "defrost", "binary", None, "Defrost"
    )
    assert s.state == STATE_OFF

    # Test mix valve position with conversion
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
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "pumpSpeed": 80,
                            "defrosting": 1,
                            "waterFlow": 30,
                            "waterPressure": 200,
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test pump speed from nested data
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "pump_speed",
        "water_speed",
        "m/s",
        "Pump Speed",
    )
    assert s.state == 0.8  # 80% converted to 0.8

    # Test defrost from nested data
    s = CSNetHomeInstallationSensor(
        coordinator, device_data, common_data, "defrost", "binary", None, "Defrost"
    )
    assert s.state == STATE_ON  # defrosting = 1

    # Test water flow from nested data
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_flow",
        "water_debit",
        "m³/h",
        "Water Flow",
    )
    assert s.state == 3.0  # 30 / 10 = 3.0

    # Test water pressure from nested data
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "water_pressure",
        "pressure",
        "bar",
        "Water Pressure",
    )
    assert s.state == 4.0  # 200 / 50 = 4.0


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
        get_installation_devices_data=lambda: {
            "data": [
                {
                    "indoors": [
                        {
                            "heatingStatus": {
                                "pumpSpeed": 100,
                            }
                        }
                    ]
                }
            ]
        },
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "pump_speed",
        "water_speed",
        "m/s",
        "Pump Speed",
    )

    # Test device info
    device_info = s.device_info
    assert device_info["manufacturer"] == "Hitachi"
    assert device_info["model"] == "Hitachi Installation Installation"
    assert device_info["sw_version"] == "1.0.0"

    # Test unique id
    assert s.unique_id == "csnet_home-installation-pump_speed"

    # Test name
    assert s.name == "Installation Global Pump Speed"

    # Test device class and unit
    assert s.device_class == "water_speed"
    assert s.unit_of_measurement == "m/s"
