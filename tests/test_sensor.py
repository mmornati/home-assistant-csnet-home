"""Test CSNet Home sensors."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import STATE_OFF, STATE_ON, UnitOfTemperature

from custom_components.csnet_home.sensor import CSNetHomeSensor


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
