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
        "alarm_message": None,
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


def test_alarm_code_and_active():
    """Expose alarm_code value and compute alarm_active binary state."""
    coordinator, sensor_data, common = build_context()
    sensor_data["alarm_code"] = 0

    alarm_code = CSNetHomeSensor(coordinator, sensor_data, common, "alarm_code", "enum")
    alarm_active = CSNetHomeSensor(
        coordinator, sensor_data, common, "alarm_active", "binary"
    )

    # no alarm
    assert alarm_code.state == 0
    assert alarm_active.state == STATE_OFF

    # set an alarm
    sensor_data["alarm_code"] = 42
    assert alarm_code.state == 42
    assert alarm_active.state == STATE_ON


def test_installation_sensor():
    """Test installation sensor functionality."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
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
    assert s.name == "System Controller Pump Speed"

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
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
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
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
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
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
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
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
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
    assert device_info["model"] == "HVAC System"
    assert device_info["sw_version"] == "1.0.0"

    # Test unique id
    assert s.unique_id == "csnet_home-installation-pump_speed"

    # Test name
    assert s.name == "System Controller Pump Speed"

    # Test device class and unit
    assert s.device_class == "water_speed"
    assert s.unit_of_measurement == "m/s"


def test_central_config_sensor():
    """Test central config sensor with different values."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with centralConfig = 0 (Unit Only)
    installation_data = {
        "data": [{"indoors": [{"heatingStatus": {"centralConfig": 0}}]}]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "central_config",
        "enum",
        None,
        "Central Config",
    )
    assert s.state == "Unit Only ⚠️"

    # Test with centralConfig = 1 (RT Only)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 1
    assert s.state == "RT Only ⚠️"

    # Test with centralConfig = 2 (Unit & RT)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 2
    assert s.state == "Unit & RT ⚠️"

    # Test with centralConfig = 3 (Total Control) - no warning
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 3
    assert s.state == "Total Control"
    assert "⚠️" not in s.state

    # Test with centralConfig = 4 (Total Control+)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 4
    assert s.state == "Total Control+"
    assert "⚠️" not in s.state

    # Test with unknown value
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 99
    assert "Unknown" in s.state


def test_lcd_software_version_sensor():
    """Test LCD software version sensor."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with version 0x0222 (546 decimal)
    installation_data = {"data": [{"indoors": [{"heatingStatus": {"lcdSoft": 546}}]}]}

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "lcd_software_version",
        None,
        None,
        "LCD Software Version",
    )
    assert s.state == "0x0222"

    # Test with version 0x0300 (768 decimal)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["lcdSoft"] = 768
    assert s.state == "0x0300"

    # Test with version 0
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["lcdSoft"] = 0
    assert s.state == 0

    # Test with None
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["lcdSoft"] = None
    assert s.state is None


def test_unit_model_sensor():
    """Test unit model sensor with different model codes."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    installation_data = {"data": [{"indoors": [{"heatingStatus": {"unitModel": 0}}]}]}

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "unit_model",
        "enum",
        None,
        "Unit Model",
    )

    # Test all known unit models
    assert s.state == "Yutaki S"

    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 1
    assert s.state == "Yutaki SC"

    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 2
    assert s.state == "Yutaki S80"

    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 3
    assert s.state == "Yutaki M"

    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 4
    assert s.state == "Yutaki SC Lite"

    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 5
    assert s.state == "Yutampo"

    # Test unknown model
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 99
    assert "Unknown" in s.state


def test_central_control_enabled_sensor():
    """Test central control enabled binary sensor."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with centralConfig >= 3 (should be ON)
    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "centralConfig": 3,
                            "unitModel": 0,
                            "lcdSoft": 546,
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "central_control_enabled",
        "binary",
        None,
        "Central Control Enabled",
    )
    assert s.state == STATE_ON

    # Test with centralConfig < 3 but non-S80 model and recent firmware (should be ON)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 2
    installation_data["data"][0]["indoors"][0]["heatingStatus"][
        "unitModel"
    ] = 0  # Yutaki S
    installation_data["data"][0]["indoors"][0]["heatingStatus"][
        "lcdSoft"
    ] = 546  # >= 0x0222
    assert s.state == STATE_ON

    # Test with centralConfig < 3, non-S80, and lcdSoft = 0 (should be ON - not configured yet)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 2
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 0
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["lcdSoft"] = 0
    assert s.state == STATE_ON

    # Test with centralConfig < 3, non-S80, old firmware (should be OFF)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 2
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 0
    installation_data["data"][0]["indoors"][0]["heatingStatus"][
        "lcdSoft"
    ] = 500  # < 0x0222
    assert s.state == STATE_OFF

    # Test with centralConfig < 3 and S80 model (should be OFF)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 2
    installation_data["data"][0]["indoors"][0]["heatingStatus"][
        "unitModel"
    ] = 2  # Yutaki S80
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["lcdSoft"] = 546
    assert s.state == STATE_OFF

    # Test with centralConfig = 4 (should be ON)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["centralConfig"] = 4
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["unitModel"] = 2
    assert s.state == STATE_ON


def test_central_control_enabled_no_data():
    """Test central control enabled sensor with missing data."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
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
        "central_control_enabled",
        "binary",
        None,
        "Central Control Enabled",
    )
    assert s.state == STATE_OFF

    # Test with None data
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: None,
    )
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "central_control_enabled",
        "binary",
        None,
        "Central Control Enabled",
    )
    assert s.state == STATE_OFF

    # Test with missing heatingStatus
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {"data": [{"indoors": [{}]}]},
    )
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "central_control_enabled",
        "binary",
        None,
        "Central Control Enabled",
    )
    assert s.state == STATE_OFF


def test_central_control_sensors_metadata():
    """Test metadata for new central control sensors."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "centralConfig": 3,
                            "unitModel": 0,
                            "lcdSoft": 546,
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test central config sensor metadata
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "central_config",
        "enum",
        None,
        "Central Config",
    )
    assert s.name == "System Controller Central Config"
    assert s.unique_id == "csnet_home-installation-central_config"
    assert s.device_class == "enum"

    # Test LCD software version sensor metadata
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "lcd_software_version",
        None,
        None,
        "LCD Software Version",
    )
    assert s.name == "System Controller LCD Software Version"
    assert s.unique_id == "csnet_home-installation-lcd_software_version"

    # Test unit model sensor metadata
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "unit_model",
        "enum",
        None,
        "Unit Model",
    )
    assert s.name == "System Controller Unit Model"
    assert s.unique_id == "csnet_home-installation-unit_model"
    assert s.device_class == "enum"

    # Test central control enabled sensor metadata
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "central_control_enabled",
        "binary",
        None,
        "Central Control Enabled",
    )
    assert s.name == "System Controller Central Control Enabled"
    assert s.unique_id == "csnet_home-installation-central_control_enabled"
    assert s.device_class == "binary"
