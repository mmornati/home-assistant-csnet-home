"""Test CSNet Home sensors."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import STATE_OFF, STATE_ON, UnitOfTemperature

from custom_components.csnet_home.sensor import (
    CSNetHomeSensor,
    CSNetHomeInstallationSensor,
    CSNetHomeDeviceSensor,
    CSNetHomeAlarmHistorySensor,
    CSNetHomeAlarmStatisticsSensor,
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


def test_wifi_signal_sensor():
    """Test WiFi signal strength sensor."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "rssi": -70,
                "lastComm": 1736193442000,
                "currentTimeMillis": 1736193448768,
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "wifi_signal",
        "signal_strength",
        "dBm",
        "WiFi Signal",
    )

    # Test WiFi signal strength
    assert s.state == -70
    assert s.unit_of_measurement == "dBm"
    assert s.device_class == "signal_strength"
    assert s.name == "Hitachi PAC WiFi Signal"
    assert "wifi_signal" in s.unique_id


def test_wifi_signal_sensor_no_data():
    """Test WiFi signal sensor when RSSI data is missing."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                # rssi is missing
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "wifi_signal",
        "signal_strength",
        "dBm",
        "WiFi Signal",
    )

    # Should return None when rssi is missing
    assert s.state is None


def test_connectivity_sensor_online():
    """Test connectivity sensor when device is online."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    # Device last communicated 5 minutes ago (5 * 60 * 1000 ms = 300000 ms)
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "lastComm": 1736193148768,  # 5 minutes ago
                "currentTimeMillis": 1736193448768,
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "connectivity",
        "binary",
        None,
        "Connectivity",
    )

    # Should be ON (online) when last communication was < 10 minutes ago
    assert s.state == STATE_ON
    assert s.device_class == "binary"
    assert s.name == "Hitachi PAC Connectivity"


def test_connectivity_sensor_offline():
    """Test connectivity sensor when device is offline."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    # Device last communicated 15 minutes ago (15 * 60 * 1000 ms = 900000 ms)
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "lastComm": 1736192548768,  # 15 minutes ago
                "currentTimeMillis": 1736193448768,
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "connectivity",
        "binary",
        None,
        "Connectivity",
    )

    # Should be OFF (offline) when last communication was > 10 minutes ago
    assert s.state == STATE_OFF


def test_connectivity_sensor_exactly_10_minutes():
    """Test connectivity sensor at exactly 10 minutes boundary."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    # Device last communicated exactly 10 minutes ago (10 * 60 * 1000 ms = 600000 ms)
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "lastComm": 1736192848768,  # exactly 10 minutes ago
                "currentTimeMillis": 1736193448768,
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "connectivity",
        "binary",
        None,
        "Connectivity",
    )

    # Should be ON (online) when last communication was exactly 10 minutes ago (<=10)
    assert s.state == STATE_ON


def test_connectivity_sensor_no_data():
    """Test connectivity sensor when timestamp data is missing."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                # lastComm and currentTimeMillis are missing
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "connectivity",
        "binary",
        None,
        "Connectivity",
    )

    # Should be OFF (offline) when data is missing
    assert s.state == STATE_OFF


def test_last_communication_sensor():
    """Test last communication timestamp sensor."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "lastComm": 1736193442000,
                "currentTimeMillis": 1736193448768,
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "last_communication",
        "timestamp",
        None,
        "Last Communication",
    )

    # Test timestamp conversion
    assert s.state is not None
    assert "2025-01-06" in s.state  # Verify it's a valid ISO timestamp
    assert "T" in s.state  # ISO format should have T separator
    assert s.device_class == "timestamp"
    assert s.name == "Hitachi PAC Last Communication"


def test_last_communication_sensor_no_data():
    """Test last communication sensor when timestamp is missing."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                # lastComm is missing
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "last_communication",
        "timestamp",
        None,
        "Last Communication",
    )

    # Should return None when lastComm is missing
    assert s.state is None


def test_device_sensor_coordinator_update():
    """Test device sensor updates when coordinator refreshes."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "rssi": -70,
                "lastComm": 1736193442000,
                "currentTimeMillis": 1736193448768,
            }
        },
    }

    updated_sensor_data = sensor_data.copy()
    updated_common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "rssi": -65,  # Updated signal strength
                "lastComm": 1736193500000,  # Updated timestamp
                "currentTimeMillis": 1736193500000,
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [updated_sensor_data],
        get_common_data=lambda: updated_common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "wifi_signal",
        "signal_strength",
        "dBm",
        "WiFi Signal",
    )

    # Mock the async_write_ha_state method
    s.async_write_ha_state = MagicMock()

    # Initial state
    assert s.state == -70

    # Update common_data reference
    s._common_data = updated_common_data

    # Trigger coordinator update
    s._handle_coordinator_update()

    # Verify state updated
    assert s.state == -65
    s.async_write_ha_state.assert_called_once()


def test_device_sensor_metadata():
    """Test device sensor metadata and properties."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "status": 1,
                "firmware": "1234",
                "rssi": -70,
                "lastComm": 1736193442000,
                "currentTimeMillis": 1736193448768,
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "wifi_signal",
        "signal_strength",
        "dBm",
        "WiFi Signal",
    )

    # Test device info
    device_info = s.device_info
    assert device_info["manufacturer"] == "Hitachi"
    assert "Remote Controller" in device_info["model"]
    assert device_info["sw_version"] == "1234"

    # Test unique id
    assert "csnet_home" in s.unique_id
    assert "Living" in s.unique_id
    assert "wifi_signal" in s.unique_id

    # Test name
    assert s.name == "Hitachi PAC WiFi Signal"

    # Test device class and unit
    assert s.device_class == "signal_strength"
    assert s.unit_of_measurement == "dBm"


def test_device_sensor_no_device_status():
    """Test device sensor when device_status is missing entirely."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {},  # Empty device_status
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "wifi_signal",
        "signal_strength",
        "dBm",
        "WiFi Signal",
    )

    # Should return None when device_status is missing
    assert s.state is None


def test_wifi_signal_different_values():
    """Test WiFi signal sensor with different RSSI values."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1709,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
    }

    # Test with strong signal
    common_data = {
        "name": "Hitachi PAC",
        "firmware": "1.0.0",
        "device_status": {
            1709: {
                "name": "Hitachi PAC",
                "rssi": -50,  # Strong signal
            }
        },
    }

    coordinator = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: common_data,
    )

    s = CSNetHomeDeviceSensor(
        coordinator,
        sensor_data,
        common_data,
        "wifi_signal",
        "signal_strength",
        "dBm",
        "WiFi Signal",
    )
    assert s.state == -50

    # Test with weak signal
    common_data["device_status"][1709]["rssi"] = -90
    assert s.state == -90

    # Test with medium signal
    common_data["device_status"][1709]["rssi"] = -70
    assert s.state == -70


def test_enhanced_alarm_sensors():
    """Test enhanced alarm sensors (alarm_code_formatted, alarm_origin, unit_type)."""
    coordinator, sensor_data, common = build_context()

    # Add enhanced alarm fields to sensor_data
    sensor_data["alarm_code"] = 62
    sensor_data["alarm_code_formatted"] = "62"
    sensor_data["alarm_origin"] = "Indoor Unit"
    sensor_data["unit_type"] = "yutaki"

    # Test alarm_code_formatted sensor
    s_formatted = CSNetHomeSensor(
        coordinator, sensor_data, common, "alarm_code_formatted", "enum"
    )
    assert s_formatted.state == "62"

    # Test alarm_origin sensor
    s_origin = CSNetHomeSensor(coordinator, sensor_data, common, "alarm_origin", "enum")
    assert s_origin.state == "Indoor Unit"

    # Test unit_type sensor
    s_type = CSNetHomeSensor(coordinator, sensor_data, common, "unit_type", "enum")
    assert s_type.state == "yutaki"

    # Test with BCD alarm code
    sensor_data["alarm_code"] = 0x0162
    sensor_data["alarm_code_formatted"] = "62"
    s_formatted = CSNetHomeSensor(
        coordinator, sensor_data, common, "alarm_code_formatted", "enum"
    )
    assert s_formatted.state == "62"


def test_alarm_history_sensor():
    """Test alarm history sensor."""
    common_data = {
        "name": "Test Installation",
        "firmware": "1.0.0",
    }

    # Mock coordinator with alarm history
    coordinator = SimpleNamespace(
        get_common_data=lambda: common_data,
        get_installation_alarms_data=lambda: {
            "alarms": [
                {
                    "code": "62",
                    "description": "Test Alarm 1",
                    "timestamp": "2024-01-01T12:00:00",
                    "device": "Device1",
                },
                {
                    "code": "100",
                    "description": "Test Alarm 2",
                    "timestamp": "2024-01-01T13:00:00",
                    "device": "Device2",
                },
            ],
            "last_updated": "2024-01-01T14:00:00",
        },
    )

    s = CSNetHomeAlarmHistorySensor(coordinator, common_data)

    # Test state (number of alarms)
    assert s.state == 2

    # Test attributes
    attrs = s.extra_state_attributes
    assert "recent_alarms" in attrs
    assert len(attrs["recent_alarms"]) == 2
    assert attrs["total_alarms"] == 2
    assert attrs["last_updated"] == "2024-01-01T14:00:00"
    assert attrs["recent_alarms"][0]["code"] == "62"
    assert attrs["recent_alarms"][1]["code"] == "100"


def test_alarm_history_sensor_empty():
    """Test alarm history sensor with no alarms."""
    common_data = {
        "name": "Test Installation",
        "firmware": "1.0.0",
    }

    # Mock coordinator with no alarm history
    coordinator = SimpleNamespace(
        get_common_data=lambda: common_data,
        get_installation_alarms_data=lambda: None,
    )

    s = CSNetHomeAlarmHistorySensor(coordinator, common_data)

    # Test state (no alarms)
    assert s.state == 0

    # Test attributes
    attrs = s.extra_state_attributes
    assert not attrs


def test_alarm_statistics_sensor_total_count():
    """Test alarm statistics sensor for total alarm count."""
    common_data = {
        "name": "Test Installation",
        "firmware": "1.0.0",
    }

    sensors_data = [
        {
            "device_name": "Device1",
            "room_name": "Room1",
            "alarm_code": 62,
            "alarm_code_formatted": "62",
        },
        {
            "device_name": "Device2",
            "room_name": "Room2",
            "alarm_code": 100,
            "alarm_code_formatted": "100",
        },
        {
            "device_name": "Device3",
            "room_name": "Room3",
            "alarm_code": 0,  # No alarm
            "alarm_code_formatted": "0",
        },
    ]

    # Mock coordinator
    coordinator = SimpleNamespace(
        get_common_data=lambda: common_data,
        get_sensors_data=lambda: sensors_data,
    )

    s = CSNetHomeAlarmStatisticsSensor(
        coordinator, common_data, "total_alarm_count", "Total Alarms"
    )

    # Test state (count of active alarms)
    assert s.state == 2

    # Test attributes
    attrs = s.extra_state_attributes
    assert "active_devices" in attrs
    assert len(attrs["active_devices"]) == 2
    assert attrs["active_devices"][0]["device"] == "Device1"
    assert attrs["active_devices"][0]["code"] == 62


def test_alarm_statistics_sensor_by_origin():
    """Test alarm statistics sensor for alarms by origin."""
    common_data = {
        "name": "Test Installation",
        "firmware": "1.0.0",
    }

    sensors_data = [
        {
            "device_name": "Device1",
            "room_name": "Room1",
            "alarm_code": 62,
            "alarm_origin": "Indoor Unit",
        },
        {
            "device_name": "Device2",
            "room_name": "Room2",
            "alarm_code": 100,
            "alarm_origin": "Indoor Unit",
        },
        {
            "device_name": "Device3",
            "room_name": "Room3",
            "alarm_code": 101,
            "alarm_origin": "2nd Cycle",
        },
    ]

    # Mock coordinator
    coordinator = SimpleNamespace(
        get_common_data=lambda: common_data,
        get_sensors_data=lambda: sensors_data,
    )

    s = CSNetHomeAlarmStatisticsSensor(
        coordinator, common_data, "alarm_by_origin", "Alarms by Origin"
    )

    # Test state (count of most common origin)
    assert s.state == 2  # "Indoor Unit" appears twice

    # Test attributes
    attrs = s.extra_state_attributes
    assert "origin_distribution" in attrs
    assert attrs["origin_distribution"]["Indoor Unit"] == 2
    assert attrs["origin_distribution"]["2nd Cycle"] == 1
    assert attrs["most_common_origin"] == "Indoor Unit"


def test_alarm_statistics_sensor_no_alarms():
    """Test alarm statistics sensor with no active alarms."""
    common_data = {
        "name": "Test Installation",
        "firmware": "1.0.0",
    }

    sensors_data = [
        {
            "device_name": "Device1",
            "room_name": "Room1",
            "alarm_code": 0,
        },
        {
            "device_name": "Device2",
            "room_name": "Room2",
            "alarm_code": 0,
        },
    ]

    # Mock coordinator
    coordinator = SimpleNamespace(
        get_common_data=lambda: common_data,
        get_sensors_data=lambda: sensors_data,
    )

    s_total = CSNetHomeAlarmStatisticsSensor(
        coordinator, common_data, "total_alarm_count", "Total Alarms"
    )
    assert s_total.state == 0

    s_origin = CSNetHomeAlarmStatisticsSensor(
        coordinator, common_data, "alarm_by_origin", "Alarms by Origin"
    )
    assert s_origin.state == 0


def test_system_config_sensors():
    """Test system configuration diagnostic sensors (Issue #78)."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Mock installation devices data with systemConfigBits
    # Test all bits: 0x1000 (cascade), 0x2000 (fan coil), 0x40 (C1), 0x80 (C2)
    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "systemConfigBits": 0x3000 | 0x40 | 0x80,  # All bits set
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test cascade slave mode sensor (bit 0x1000)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "cascade_slave_mode",
        "binary",
        None,
        "Cascade Slave Mode",
    )
    assert s.state == STATE_ON
    assert s.name == "System Controller Cascade Slave Mode"

    # Test fan coil compatible sensor (bit 0x2000)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "fan_coil_compatible",
        "binary",
        None,
        "Fan Coil Compatible",
    )
    assert s.state == STATE_ON

    # Test C1 thermostat present sensor (bit 0x40)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "c1_thermostat_present",
        "binary",
        None,
        "C1 Thermostat Present",
    )
    assert s.state == STATE_ON

    # Test C2 thermostat present sensor (bit 0x80)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "c2_thermostat_present",
        "binary",
        None,
        "C2 Thermostat Present",
    )
    assert s.state == STATE_ON


def test_system_config_sensors_no_bits_set():
    """Test system configuration sensors when no bits are set."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Mock installation devices data with systemConfigBits = 0
    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "systemConfigBits": 0,  # No bits set
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test cascade slave mode sensor (bit 0x1000)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "cascade_slave_mode",
        "binary",
        None,
        "Cascade Slave Mode",
    )
    assert s.state == STATE_OFF

    # Test fan coil compatible sensor (bit 0x2000)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "fan_coil_compatible",
        "binary",
        None,
        "Fan Coil Compatible",
    )
    assert s.state == STATE_OFF

    # Test C1 thermostat present sensor (bit 0x40)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "c1_thermostat_present",
        "binary",
        None,
        "C1 Thermostat Present",
    )
    assert s.state == STATE_OFF

    # Test C2 thermostat present sensor (bit 0x80)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "c2_thermostat_present",
        "binary",
        None,
        "C2 Thermostat Present",
    )
    assert s.state == STATE_OFF


def test_system_config_sensors_partial_bits():
    """Test system configuration sensors with only some bits set."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Mock installation devices data with only fan coil and C1 bits set
    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "systemConfigBits": 0x2000 | 0x40,  # Fan coil + C1 only
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    # Test cascade slave mode sensor - should be OFF
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "cascade_slave_mode",
        "binary",
        None,
        "Cascade Slave Mode",
    )
    assert s.state == STATE_OFF

    # Test fan coil compatible sensor - should be ON
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "fan_coil_compatible",
        "binary",
        None,
        "Fan Coil Compatible",
    )
    assert s.state == STATE_ON

    # Test C1 thermostat present sensor - should be ON
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "c1_thermostat_present",
        "binary",
        None,
        "C1 Thermostat Present",
    )
    assert s.state == STATE_ON

    # Test C2 thermostat present sensor - should be OFF
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "c2_thermostat_present",
        "binary",
        None,
        "C2 Thermostat Present",
    )
    assert s.state == STATE_OFF


def test_system_config_sensors_no_data():
    """Test system configuration sensors when no installation data available."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Mock with empty/no data
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {},
    )

    # All sensors should return STATE_OFF when no data is available
    for key, name in [
        ("cascade_slave_mode", "Cascade Slave Mode"),
        ("fan_coil_compatible", "Fan Coil Compatible"),
        ("c1_thermostat_present", "C1 Thermostat Present"),
        ("c2_thermostat_present", "C2 Thermostat Present"),
    ]:
        s = CSNetHomeInstallationSensor(
            coordinator,
            device_data,
            common_data,
            key,
            "binary",
            None,
            name,
        )
        assert s.state == STATE_OFF


def test_outdoor_temperature_sensors():
    """Test outdoor temperature sensors (Issue: Add Outdoor Temperature Sensor)."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Mock installation devices data with outdoor temperature values
    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
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

    # Test outdoor temperature sensor (current outdoor temperature)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "external_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
        "Outdoor Temperature",
    )
    assert s.state == 14
    assert s.unit_of_measurement == UnitOfTemperature.CELSIUS
    assert s.device_class == "temperature"
    assert s.name == "System Controller Outdoor Temperature"
    assert s.unique_id == "csnet_home-installation-external_temperature"

    # Test outdoor average temperature sensor (mean external temperature)
    s = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "mean_external_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
        "Outdoor Average Temperature",
    )
    assert s.state == 15
    assert s.unit_of_measurement == UnitOfTemperature.CELSIUS
    assert s.device_class == "temperature"
    assert s.name == "System Controller Outdoor Average Temperature"
    assert s.unique_id == "csnet_home-installation-mean_external_temperature"


def test_outdoor_temperature_sensors_various_values():
    """Test outdoor temperature sensors with various temperature values."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with negative temperature (winter conditions)
    installation_data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "outdoorAmbientTemp": -5,
                            "outdoorAmbientAverageTemp": -3,
                        }
                    }
                ]
            }
        ]
    }

    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation_data,
    )

    s_outdoor = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "external_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
        "Outdoor Temperature",
    )
    assert s_outdoor.state == -5

    s_avg = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "mean_external_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
        "Outdoor Average Temperature",
    )
    assert s_avg.state == -3

    # Test with high temperature (summer conditions)
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["outdoorAmbientTemp"] = 35
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["outdoorAmbientAverageTemp"] = 32
    assert s_outdoor.state == 35
    assert s_avg.state == 32

    # Test with zero temperature
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["outdoorAmbientTemp"] = 0
    installation_data["data"][0]["indoors"][0]["heatingStatus"]["outdoorAmbientAverageTemp"] = 0
    assert s_outdoor.state == 0
    assert s_avg.state == 0


def test_outdoor_temperature_sensors_no_data():
    """Test outdoor temperature sensors when data is missing."""
    device_data = {
        "device_name": "System",
        "device_id": "global",
        "room_name": "Controller",
        "parent_id": "global",
        "room_id": "global",
    }
    common_data = {"name": "Hitachi Installation", "firmware": "1.0.0"}

    # Test with empty installation data
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {},
    )

    s_outdoor = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "external_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
        "Outdoor Temperature",
    )
    assert s_outdoor.state is None

    s_avg = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "mean_external_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
        "Outdoor Average Temperature",
    )
    assert s_avg.state is None

    # Test with None data
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: None,
    )

    s_outdoor = CSNetHomeInstallationSensor(
        coordinator,
        device_data,
        common_data,
        "external_temperature",
        "temperature",
        UnitOfTemperature.CELSIUS,
        "Outdoor Temperature",
    )
    assert s_outdoor.state is None
