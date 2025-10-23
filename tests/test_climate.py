"""Test CSNet Home climate entity."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from homeassistant.components.climate import HVACAction, HVACMode, FAN_AUTO, FAN_ON
from homeassistant.components.climate.const import ClimateEntityFeature

from custom_components.csnet_home.climate import CSNetHomeClimate
from custom_components.csnet_home.const import DOMAIN


def build_entity(
    hass, *, mode=1, on_off=1, cur=19.5, setp=20.0, ecocomfort=1, silent_mode=0
):
    """Create a CSNetHomeClimate with minimal surroundings."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
        "operation_status": 5,
        "mode": mode,
        "real_mode": mode,
        "on_off": on_off,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": True,
        "c2_demand": False,
        "ecocomfort": ecocomfort,
        "silent_mode": silent_mode,
        "current_temperature": cur,
        "setting_temperature": setp,
        "zone_id": 1,
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry")

    # Minimal hass structure for the entity
    if not hasattr(hass, "data"):
        hass.data = {}
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}
    # Inject a fake API; will be overridden in tests that call it
    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        async_request_refresh=AsyncMock(return_value=None),
    )

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)
    return entity


def test_hvac_mode_mapping_off(hass):
    """Return OFF when on_off is 0."""
    entity = build_entity(hass, mode=1, on_off=0)
    assert entity.hvac_mode == HVACMode.OFF


def test_hvac_mode_mapping_heat(hass):
    """Return HEAT when on and mode=1."""
    entity = build_entity(hass, mode=1, on_off=1)
    assert entity.hvac_mode == HVACMode.HEAT


def test_hvac_mode_mapping_cool(hass):
    """Return COOL when on and mode=0."""
    entity = build_entity(hass, mode=0, on_off=1)
    assert entity.hvac_mode == HVACMode.COOL


def test_hvac_mode_mapping_auto(hass):
    """Return HEAT_COOL when on and mode=2."""
    entity = build_entity(hass, mode=2, on_off=1)
    assert entity.hvac_mode == HVACMode.HEAT_COOL


def test_preset_mode(hass):
    """Map ecocomfort 0->eco and 1->comfort."""
    assert build_entity(hass, ecocomfort=0).preset_mode == "eco"
    assert build_entity(hass, ecocomfort=1).preset_mode == "comfort"
    # default path for unknown values
    assert build_entity(hass, ecocomfort=-1).preset_mode == "comfort"


def test_hvac_action_heat_and_cool(hass):
    """Report HEATING/COOLING/IDLE based on temperatures and mode."""
    # Heating when setpoint > current in heat mode
    entity = build_entity(hass, mode=1, on_off=1, cur=19.0, setp=20.0)
    assert entity.hvac_action == HVACAction.HEATING
    # Cooling when setpoint < current in cool mode
    entity = build_entity(hass, mode=0, on_off=1, cur=23.0, setp=21.0)
    assert entity.hvac_action == HVACAction.COOLING
    # Idle otherwise
    entity = build_entity(hass, mode=1, on_off=1, cur=20.0, setp=20.0)
    assert entity.hvac_action == HVACAction.IDLE


def test_extra_state_attributes(hass):
    """Expose extra attributes from elements payload."""
    entity = build_entity(hass)
    attrs = entity.extra_state_attributes
    assert attrs["real_mode"] == 1
    assert attrs["operation_status"] == 5
    assert attrs["c1_demand"] is True
    assert attrs["c2_demand"] is False


@pytest.mark.asyncio
async def test_turn_off_calls_api(hass):
    """Call API with hvac_mode OFF when turning off."""
    entity = build_entity(hass, mode=1, on_off=1)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]
    await entity.async_turn_off()
    api.async_set_hvac_mode.assert_awaited()
    called_args = api.async_set_hvac_mode.call_args[0]
    # args: zone_id, parent_id, hvac_mode
    assert called_args[2] == HVACMode.OFF


@pytest.mark.asyncio
async def test_turn_on_preserves_mode(hass):
    """Restore last mode when turning on (heat/cool/auto)."""
    # When last mode is heat
    entity = build_entity(hass, mode=1, on_off=0)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]
    await entity.async_turn_on()
    called_args = api.async_set_hvac_mode.call_args[0]
    assert called_args[2] == HVACMode.HEAT

    # When last mode is cool
    entity = build_entity(hass, mode=0, on_off=0)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]
    await entity.async_turn_on()
    called_args = api.async_set_hvac_mode.call_args[0]
    assert called_args[2] == HVACMode.COOL

    # When last mode is auto
    entity = build_entity(hass, mode=2, on_off=0)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]
    await entity.async_turn_on()
    called_args = api.async_set_hvac_mode.call_args[0]
    assert called_args[2] == HVACMode.HEAT_COOL


@pytest.mark.asyncio
async def test_set_temperature_updates_state_on_success(hass):
    """Update target temperature locally on success."""
    entity = build_entity(hass, mode=1, on_off=1, setp=19.0)
    await entity.async_set_temperature(temperature=21.0)
    assert entity.target_temperature == 21.0


def test_unique_id_contains_device_id(hass):
    """Include device_id in unique_id for stability."""
    entity = build_entity(hass)
    uid = entity.unique_id
    assert "1234" in uid


@pytest.mark.asyncio
async def test_async_update_handles_missing_sensor_data(hass):
    """Test that async_update handles when sensor data becomes None gracefully."""
    entity = build_entity(hass, mode=1, on_off=1, cur=19.5, setp=20.0)

    # Modify coordinator to return empty list (simulating room not found)
    coordinator = hass.data[DOMAIN][entity.entry.entry_id]["coordinator"]
    coordinator.get_sensors_data = lambda: []

    # This should not raise TypeError even though sensor_data becomes None
    await entity.async_update()

    # Verify entity handles None sensor_data gracefully
    assert entity.current_temperature is None
    assert entity.target_temperature is None
    assert entity.hvac_mode == HVACMode.OFF
    assert entity.preset_mode == "comfort"
    assert not entity.extra_state_attributes
    assert entity.hvac_action == HVACAction.IDLE
    assert entity.is_heating() is False
    assert entity.is_cooling() is False


@pytest.mark.asyncio
async def test_async_update_preserves_sensor_data_when_found(hass):
    """Test that async_update works correctly when sensor data is found."""
    entity = build_entity(hass, mode=1, on_off=1, cur=19.5, setp=20.0)

    # Update should preserve the sensor data
    await entity.async_update()

    # Verify entity still has valid data
    assert entity.current_temperature == 19.5
    assert entity.target_temperature == 20.0
    assert entity.hvac_mode == HVACMode.HEAT


def test_fan_mode_mapping_silent_off(hass):
    """Return FAN_AUTO when silent_mode is 0."""
    entity = build_entity(hass, silent_mode=0)
    assert entity.fan_mode == FAN_AUTO


def test_fan_mode_mapping_silent_on(hass):
    """Return FAN_ON when silent_mode is 1."""
    entity = build_entity(hass, silent_mode=1)
    assert entity.fan_mode == FAN_ON


def test_fan_mode_mapping_silent_none(hass):
    """Return FAN_AUTO when silent_mode is None."""
    entity = build_entity(hass)
    # Remove silent_mode to test None case
    entity._sensor_data["silent_mode"] = None
    assert entity.fan_mode == FAN_AUTO


@pytest.mark.asyncio
async def test_set_fan_mode_to_silent(hass):
    """Test setting fan mode to silent (FAN_ON)."""
    entity = build_entity(hass, silent_mode=0)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode(FAN_ON)

    api.async_set_silent_mode.assert_awaited()
    called_args = api.async_set_silent_mode.call_args[0]
    # args: zone_id, parent_id, silent_mode
    assert called_args[0] == 1  # zone_id
    assert called_args[1] == 1706  # parent_id
    assert called_args[2] is True  # silent_mode enabled
    # Check local state updated
    assert entity._sensor_data["silent_mode"] == 1


@pytest.mark.asyncio
async def test_set_fan_mode_to_normal(hass):
    """Test setting fan mode to normal (FAN_AUTO)."""
    entity = build_entity(hass, silent_mode=1)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode(FAN_AUTO)

    api.async_set_silent_mode.assert_awaited()
    called_args = api.async_set_silent_mode.call_args[0]
    assert called_args[0] == 1  # zone_id
    assert called_args[1] == 1706  # parent_id
    assert called_args[2] is False  # silent_mode disabled
    # Check local state updated
    assert entity._sensor_data["silent_mode"] == 0


def test_extra_state_attributes_includes_silent_mode(hass):
    """Verify silent_mode is included in extra attributes."""
    entity = build_entity(hass, silent_mode=1)
    attrs = entity.extra_state_attributes
    assert "silent_mode" in attrs
    assert attrs["silent_mode"] == 1


def test_fan_modes_available(hass):
    """Verify fan modes are available."""
    entity = build_entity(hass)
    assert entity.fan_modes is not None
    assert FAN_AUTO in entity.fan_modes
    assert FAN_ON in entity.fan_modes


def test_supported_features_includes_fan_mode(hass):
    """Verify FAN_MODE is in supported features."""
    entity = build_entity(hass)
    assert entity.supported_features & ClimateEntityFeature.FAN_MODE


def test_dynamic_temperature_limits_heating_mode(hass):
    """Test that min/max temp are dynamically set based on heating mode."""
    entity = build_entity(hass, mode=1)  # Heating mode

    # Mock the API and coordinator to return temperature limits
    mock_api = SimpleNamespace(
        get_temperature_limits=lambda zone_id, mode, data: (11, 30),
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
    )
    mock_coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {
            "heatingStatus": {
                "heatAirMinC1": 11,
                "heatAirMaxC1": 30,
            }
        },
        get_sensors_data=lambda: [entity._sensor_data],
        get_common_data=lambda: {"device_status": {1234: {"name": "Hitachi PAC", "firmware": "1.0.0"}}},
        async_request_refresh=AsyncMock(return_value=None),
    )

    hass.data[DOMAIN][entity.entry.entry_id]["api"] = mock_api
    hass.data[DOMAIN][entity.entry.entry_id]["coordinator"] = mock_coordinator

    # Test min and max temperature
    assert entity.min_temp == 11
    assert entity.max_temp == 30


def test_dynamic_temperature_limits_cooling_mode(hass):
    """Test that min/max temp are dynamically set based on cooling mode."""
    entity = build_entity(hass, mode=0)  # Cooling mode

    # Mock the API and coordinator to return temperature limits for cooling
    mock_api = SimpleNamespace(
        get_temperature_limits=lambda zone_id, mode, data: (16, 30),
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
    )
    mock_coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {
            "heatingStatus": {
                "coolAirMinC1": 16,
                "coolAirMaxC1": 30,
            }
        },
        get_sensors_data=lambda: [entity._sensor_data],
        get_common_data=lambda: {"device_status": {1234: {"name": "Hitachi PAC", "firmware": "1.0.0"}}},
        async_request_refresh=AsyncMock(return_value=None),
    )

    hass.data[DOMAIN][entity.entry.entry_id]["api"] = mock_api
    hass.data[DOMAIN][entity.entry.entry_id]["coordinator"] = mock_coordinator

    # Test min and max temperature for cooling mode
    assert entity.min_temp == 16
    assert entity.max_temp == 30


def test_dynamic_temperature_limits_fallback_to_defaults(hass):
    """Test that min/max temp fall back to defaults when API data is missing."""
    entity = build_entity(hass, mode=1)

    # Mock the API to return None (no data available)
    mock_api = SimpleNamespace(
        get_temperature_limits=lambda zone_id, mode, data: (None, None),
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
    )
    mock_coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {},
        get_sensors_data=lambda: [entity._sensor_data],
        get_common_data=lambda: {"device_status": {1234: {"name": "Hitachi PAC", "firmware": "1.0.0"}}},
        async_request_refresh=AsyncMock(return_value=None),
    )

    hass.data[DOMAIN][entity.entry.entry_id]["api"] = mock_api
    hass.data[DOMAIN][entity.entry.entry_id]["coordinator"] = mock_coordinator

    # Test that defaults are used
    from custom_components.csnet_home.const import (
        HEATING_MIN_TEMPERATURE,
        HEATING_MAX_TEMPERATURE,
    )
    assert entity.min_temp == HEATING_MIN_TEMPERATURE
    assert entity.max_temp == HEATING_MAX_TEMPERATURE


def test_dynamic_temperature_limits_zone2(hass):
    """Test temperature limits for zone 2 (C2 circuit)."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Bedroom",
        "parent_id": 1706,
        "room_id": 396,
        "operation_status": 5,
        "mode": 1,  # Heat mode
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": False,
        "c2_demand": True,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 18.0,
        "setting_temperature": 20.0,
        "zone_id": 2,  # Zone 2
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry")

    # Setup hass data
    if not hasattr(hass, "data"):
        hass.data = {}
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    # Mock the API to return zone 2 temperature limits
    mock_api = SimpleNamespace(
        get_temperature_limits=lambda zone_id, mode, data: (12, 28),
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
    )
    mock_coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {
            "heatingStatus": {
                "heatAirMinC2": 12,
                "heatAirMaxC2": 28,
            }
        },
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        async_request_refresh=AsyncMock(return_value=None),
    )

    hass.data[DOMAIN][entry.entry_id]["api"] = mock_api
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = mock_coordinator

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)

    # Test min and max temperature for zone 2
    assert entity.min_temp == 12
    assert entity.max_temp == 28
