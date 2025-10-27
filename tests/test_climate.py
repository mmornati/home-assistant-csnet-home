"""Test CSNet Home climate entity."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from homeassistant.components.climate import HVACAction, HVACMode, FAN_AUTO, FAN_ON
from homeassistant.components.climate.const import ClimateEntityFeature

from custom_components.csnet_home.climate import CSNetHomeClimate
from custom_components.csnet_home.const import (
    DOMAIN,
    HEATING_MIN_TEMPERATURE,
    HEATING_MAX_TEMPERATURE,
    CONF_MAX_TEMP_OVERRIDE,
    OPST_OFF,
    OPST_COOL_D_OFF,
    OPST_COOL_T_OFF,
    OPST_COOL_T_ON,
    OPST_HEAT_D_OFF,
    OPST_HEAT_T_OFF,
    OPST_HEAT_T_ON,
    OPST_DHW_OFF,
    OPST_DHW_ON,
    OPST_SWP_OFF,
    OPST_SWP_ON,
    OPST_ALARM,
    OTC_HEATING_TYPE_NONE,
    OTC_HEATING_TYPE_POINTS,
    OTC_HEATING_TYPE_GRADIENT,
    OTC_HEATING_TYPE_FIX,
    OTC_COOLING_TYPE_NONE,
    OTC_COOLING_TYPE_POINTS,
    OTC_COOLING_TYPE_FIX,
)


def build_entity(
    hass,
    *,
    mode=1,
    on_off=1,
    cur=19.5,
    setp=20.0,
    ecocomfort=1,
    silent_mode=0,
    fan1_speed=None,
    fan2_speed=None,
    is_fan_coil=False,
    zone_id=1,
    operation_status=5
):
    """Create a CSNetHomeClimate with minimal surroundings."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
        "operation_status": operation_status,
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
        "zone_id": zone_id,
        "fan1_speed": fan1_speed,
        "fan2_speed": fan2_speed,
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry", data={})

    # Minimal hass structure for the entity
    if not hasattr(hass, "data"):
        hass.data = {}
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    # Setup installation devices data for fan coil compatibility check
    installation_devices_data = {}
    if is_fan_coil:
        installation_devices_data = {
            "heatingStatus": {
                "systemConfigBits": 0x2000,  # Fan coil compatible
                "fan1ControlledOnLCD": 3,  # Heating + Cooling
                "fan2ControlledOnLCD": 3,  # Heating + Cooling
            }
        }

    # Inject a fake API; will be overridden in tests that call it
    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        async_set_fan_speed=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: is_fan_coil,
        get_fan_control_availability=lambda circuit, mode, data: is_fan_coil,
        get_temperature_limits=lambda zone_id, mode, data: (None, None),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        get_installation_devices_data=lambda: installation_devices_data,
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
        get_common_data=lambda: {
            "device_status": {1234: {"name": "Hitachi PAC", "firmware": "1.0.0"}}
        },
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
        get_common_data=lambda: {
            "device_status": {1234: {"name": "Hitachi PAC", "firmware": "1.0.0"}}
        },
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
        get_common_data=lambda: {
            "device_status": {1234: {"name": "Hitachi PAC", "firmware": "1.0.0"}}
        },
        async_request_refresh=AsyncMock(return_value=None),
    )

    hass.data[DOMAIN][entity.entry.entry_id]["api"] = mock_api
    hass.data[DOMAIN][entity.entry.entry_id]["coordinator"] = mock_coordinator

    # Test that defaults are used
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
    entry = SimpleNamespace(entry_id="test-entry", data={})

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
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
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


def test_max_temp_override_in_config(hass):
    """Test that max_temp_override from config takes precedence."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Living Room",
        "parent_id": 1706,
        "room_id": 395,
        "operation_status": 5,
        "mode": 1,  # Heat mode
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": True,
        "c2_demand": False,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 20.0,
        "setting_temperature": 22.0,
        "zone_id": 1,  # Zone 1
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}

    # Create entry with max_temp_override set to 45
    entry = SimpleNamespace(entry_id="test-entry", data={CONF_MAX_TEMP_OVERRIDE: 45})

    # Setup hass data
    if not hasattr(hass, "data"):
        hass.data = {}
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    # Mock the API to return normal temperature limits (should be overridden)
    mock_api = SimpleNamespace(
        get_temperature_limits=lambda zone_id, mode, data: (11, 30),
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
    )
    mock_coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {
            "heatingStatus": {
                "heatAirMinC1": 11,
                "heatAirMaxC1": 30,
            }
        },
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        async_request_refresh=AsyncMock(return_value=None),
    )

    hass.data[DOMAIN][entry.entry_id]["api"] = mock_api
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = mock_coordinator

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)

    # Test that override value is used (45°C instead of API limit 30°C or default 35°C)
    assert entity.min_temp == 11  # Min is not overridden
    assert entity.max_temp == 45  # Max is overridden


def test_max_temp_no_override(hass):
    """Test that max_temp uses API/defaults when no override is configured."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Living Room",
        "parent_id": 1706,
        "room_id": 395,
        "operation_status": 5,
        "mode": 1,
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": True,
        "c2_demand": False,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 20.0,
        "setting_temperature": 22.0,
        "zone_id": 1,
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}

    # Create entry WITHOUT max_temp_override
    entry = SimpleNamespace(entry_id="test-entry", data={})  # No override

    # Setup hass data
    if not hasattr(hass, "data"):
        hass.data = {}
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    # Mock the API to return temperature limits
    mock_api = SimpleNamespace(
        get_temperature_limits=lambda zone_id, mode, data: (11, 30),
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
    )
    mock_coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: {
            "heatingStatus": {
                "heatAirMinC1": 11,
                "heatAirMaxC1": 30,
            }
        },
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        async_request_refresh=AsyncMock(return_value=None),
    )

    hass.data[DOMAIN][entry.entry_id]["api"] = mock_api
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = mock_coordinator

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)

    # Test that API value is used (30°C from API)
    assert entity.max_temp == 30


# Fan Coil System Tests
def test_fan_coil_system_detection(hass):
    """Verify fan coil system is detected correctly."""
    # Non-fan coil system
    entity = build_entity(hass, is_fan_coil=False)
    assert entity._is_fan_coil is False

    # Fan coil system
    entity = build_entity(hass, is_fan_coil=True)
    assert entity._is_fan_coil is True


def test_fan_modes_for_fan_coil_system(hass):
    """Verify fan modes for fan coil systems include speed options."""
    entity = build_entity(hass, is_fan_coil=True)
    assert entity.fan_modes is not None
    assert "off" in entity.fan_modes
    assert "low" in entity.fan_modes
    assert "medium" in entity.fan_modes
    assert "auto" in entity.fan_modes
    # Should not have silent mode options
    assert FAN_AUTO not in entity.fan_modes or entity.fan_modes != [FAN_AUTO, FAN_ON]


def test_fan_modes_for_non_fan_coil_system(hass):
    """Verify fan modes for non-fan coil systems use silent mode."""
    entity = build_entity(hass, is_fan_coil=False)
    assert entity.fan_modes is not None
    assert FAN_AUTO in entity.fan_modes
    assert FAN_ON in entity.fan_modes


def test_fan_mode_reading_for_fan_coil_c1(hass):
    """Test reading fan mode for fan coil circuit 1."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=2)
    assert entity.fan_mode == "medium"


def test_fan_mode_reading_for_fan_coil_c2(hass):
    """Test reading fan mode for fan coil circuit 2."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=2, fan2_speed=1)
    assert entity.fan_mode == "low"


def test_fan_mode_reading_auto_for_fan_coil(hass):
    """Test reading fan mode auto for fan coil."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=3)
    assert entity.fan_mode == "auto"


def test_fan_mode_reading_off_for_fan_coil(hass):
    """Test reading fan mode off for fan coil."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=0)
    assert entity.fan_mode == "off"


def test_fan_mode_reading_none_for_fan_coil(hass):
    """Test reading fan mode when None for fan coil."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=None)
    assert entity.fan_mode == "auto"


@pytest.mark.asyncio
async def test_set_fan_mode_for_fan_coil_low(hass):
    """Test setting fan mode to low for fan coil system."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=3)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode("low")

    api.async_set_fan_speed.assert_awaited()
    called_args = api.async_set_fan_speed.call_args[0]
    # args: zone_id, parent_id, fan_speed, circuit
    assert called_args[0] == 1  # zone_id
    assert called_args[1] == 1706  # parent_id
    assert called_args[2] == 1  # fan speed low
    assert called_args[3] == 1  # circuit 1
    # Check local state updated
    assert entity._sensor_data["fan1_speed"] == 1


@pytest.mark.asyncio
async def test_set_fan_mode_for_fan_coil_medium(hass):
    """Test setting fan mode to medium for fan coil system."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=0)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode("medium")

    api.async_set_fan_speed.assert_awaited()
    called_args = api.async_set_fan_speed.call_args[0]
    assert called_args[2] == 2  # fan speed medium
    assert entity._sensor_data["fan1_speed"] == 2


@pytest.mark.asyncio
async def test_set_fan_mode_for_fan_coil_auto(hass):
    """Test setting fan mode to auto for fan coil system."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=1)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode("auto")

    api.async_set_fan_speed.assert_awaited()
    called_args = api.async_set_fan_speed.call_args[0]
    assert called_args[2] == 3  # fan speed auto
    assert entity._sensor_data["fan1_speed"] == 3


@pytest.mark.asyncio
async def test_set_fan_mode_for_fan_coil_off(hass):
    """Test setting fan mode to off for fan coil system."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=2)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode("off")

    api.async_set_fan_speed.assert_awaited()
    called_args = api.async_set_fan_speed.call_args[0]
    assert called_args[2] == 0  # fan speed off
    assert entity._sensor_data["fan1_speed"] == 0


@pytest.mark.asyncio
async def test_set_fan_mode_for_fan_coil_c2(hass):
    """Test setting fan mode for fan coil circuit 2."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=2, fan2_speed=0)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode("low")

    api.async_set_fan_speed.assert_awaited()
    called_args = api.async_set_fan_speed.call_args[0]
    assert called_args[0] == 2  # zone_id 2
    assert called_args[3] == 2  # circuit 2
    assert entity._sensor_data["fan2_speed"] == 1


@pytest.mark.asyncio
async def test_set_fan_mode_invalid_for_fan_coil(hass):
    """Test setting invalid fan mode for fan coil system does nothing."""
    entity = build_entity(hass, is_fan_coil=True, zone_id=1, fan1_speed=2)
    api = hass.data[DOMAIN][entity.entry.entry_id]["api"]

    await entity.async_set_fan_mode("invalid_mode")

    # Should not call the API
    api.async_set_fan_speed.assert_not_awaited()


def test_extra_state_attributes_for_fan_coil(hass):
    """Verify fan coil attributes are included in extra state attributes."""
    entity = build_entity(hass, is_fan_coil=True, fan1_speed=2, fan2_speed=1)
    attrs = entity.extra_state_attributes
    assert "is_fan_coil_compatible" in attrs
    assert attrs["is_fan_coil_compatible"] is True
    assert "fan1_speed" in attrs
    assert attrs["fan1_speed"] == 2
    assert "fan2_speed" in attrs
    assert attrs["fan2_speed"] == 1
    assert "fan1_control_available" in attrs
    assert "fan2_control_available" in attrs


def test_extra_state_attributes_for_non_fan_coil(hass):
    """Verify fan coil attributes indicate non-compatibility."""
    entity = build_entity(hass, is_fan_coil=False)
    attrs = entity.extra_state_attributes
    assert "is_fan_coil_compatible" in attrs
    assert attrs["is_fan_coil_compatible"] is False
    # Should not have fan speed attributes
    assert "fan1_speed" not in attrs or attrs["fan1_speed"] is None
    assert "fan2_speed" not in attrs or attrs["fan2_speed"] is None


# Operation Status Decoding Tests
def test_operation_status_off(hass):
    """Test operation status decoding for OFF state."""
    entity = build_entity(hass, operation_status=OPST_OFF)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_OFF
    assert attrs["operation_status_text"] == "Off"


def test_operation_status_cool_d_off(hass):
    """Test operation status decoding for Cooling Demand Off."""
    entity = build_entity(hass, operation_status=OPST_COOL_D_OFF)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_COOL_D_OFF
    assert attrs["operation_status_text"] == "Cooling Demand Off"


def test_operation_status_cool_t_off(hass):
    """Test operation status decoding for Cooling Thermostat Off."""
    entity = build_entity(hass, operation_status=OPST_COOL_T_OFF)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_COOL_T_OFF
    assert attrs["operation_status_text"] == "Cooling Thermostat Off"


def test_operation_status_cool_t_on(hass):
    """Test operation status decoding for Cooling Thermostat On."""
    entity = build_entity(hass, operation_status=OPST_COOL_T_ON)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_COOL_T_ON
    assert attrs["operation_status_text"] == "Cooling Thermostat On"


def test_operation_status_heat_d_off(hass):
    """Test operation status decoding for Heating Demand Off."""
    entity = build_entity(hass, operation_status=OPST_HEAT_D_OFF)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_HEAT_D_OFF
    assert attrs["operation_status_text"] == "Heating Demand Off"


def test_operation_status_heat_t_off(hass):
    """Test operation status decoding for Heating Thermostat Off."""
    entity = build_entity(hass, operation_status=OPST_HEAT_T_OFF)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_HEAT_T_OFF
    assert attrs["operation_status_text"] == "Heating Thermostat Off"


def test_operation_status_heat_t_on(hass):
    """Test operation status decoding for Heating Thermostat On."""
    entity = build_entity(hass, operation_status=OPST_HEAT_T_ON)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_HEAT_T_ON
    assert attrs["operation_status_text"] == "Heating Thermostat On"


def test_operation_status_dhw_off(hass):
    """Test operation status decoding for Domestic Hot Water Off."""
    entity = build_entity(hass, operation_status=OPST_DHW_OFF)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_DHW_OFF
    assert attrs["operation_status_text"] == "Domestic Hot Water Off"


def test_operation_status_dhw_on(hass):
    """Test operation status decoding for Domestic Hot Water On."""
    entity = build_entity(hass, operation_status=OPST_DHW_ON)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_DHW_ON
    assert attrs["operation_status_text"] == "Domestic Hot Water On"


def test_operation_status_swp_off(hass):
    """Test operation status decoding for Swimming Pool Off."""
    entity = build_entity(hass, operation_status=OPST_SWP_OFF)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_SWP_OFF
    assert attrs["operation_status_text"] == "Swimming Pool Off"


def test_operation_status_swp_on(hass):
    """Test operation status decoding for Swimming Pool On."""
    entity = build_entity(hass, operation_status=OPST_SWP_ON)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_SWP_ON
    assert attrs["operation_status_text"] == "Swimming Pool On"


def test_operation_status_alarm(hass):
    """Test operation status decoding for Alarm state."""
    entity = build_entity(hass, operation_status=OPST_ALARM)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == OPST_ALARM
    assert attrs["operation_status_text"] == "Alarm"


def test_operation_status_unknown(hass):
    """Test operation status decoding for unknown status code."""
    entity = build_entity(hass, operation_status=99)
    attrs = entity.extra_state_attributes
    assert attrs["operation_status"] == 99
    assert attrs["operation_status_text"] == "Unknown (99)"


def test_operation_status_text_in_attributes(hass):
    """Verify operation_status_text is included in extra attributes."""
    entity = build_entity(hass, operation_status=OPST_HEAT_T_ON)
    attrs = entity.extra_state_attributes
    assert "operation_status" in attrs
    assert "operation_status_text" in attrs
    assert attrs["operation_status_text"] == "Heating Thermostat On"


# OTC (Outdoor Temperature Compensation) Tests - Issue #71


def test_otc_attributes_zone1_heating_fix(hass):
    """Test OTC attributes for zone 1 with heating fixed type."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
        "operation_status": 5,
        "mode": 1,
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": True,
        "c2_demand": False,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 20.0,
        "setting_temperature": 21.0,
        "zone_id": 1,
        "fan1_speed": None,
        "fan2_speed": None,
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry", data={})

    # Setup installation devices data with OTC information
    installation_devices_data = {
        "heatingStatus": {
            "otcTypeHeatC1": OTC_HEATING_TYPE_FIX,
            "otcTypeCoolC1": OTC_COOLING_TYPE_FIX,
            "otcTypeHeatC2": OTC_HEATING_TYPE_NONE,
            "otcTypeCoolC2": OTC_COOLING_TYPE_NONE,
        }
    }

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        async_set_fan_speed=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
        get_temperature_limits=lambda zone_id, mode, data: (None, None),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        get_installation_devices_data=lambda: installation_devices_data,
        async_request_refresh=AsyncMock(return_value=None),
    )

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)
    attrs = entity.extra_state_attributes

    # Verify OTC attributes are present for zone 1 (circuit 1)
    assert "otc_heating_type" in attrs
    assert "otc_heating_type_name" in attrs
    assert "otc_cooling_type" in attrs
    assert "otc_cooling_type_name" in attrs
    assert attrs["otc_heating_type"] == OTC_HEATING_TYPE_FIX
    assert attrs["otc_heating_type_name"] == "Fixed"
    assert attrs["otc_cooling_type"] == OTC_COOLING_TYPE_FIX
    assert attrs["otc_cooling_type_name"] == "Fixed"


def test_otc_attributes_zone2_heating_gradient(hass):
    """Test OTC attributes for zone 2 with heating gradient type."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Bedroom",
        "parent_id": 1706,
        "room_id": 396,
        "operation_status": 5,
        "mode": 1,
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": False,
        "c2_demand": True,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 19.0,
        "setting_temperature": 20.0,
        "zone_id": 2,
        "fan1_speed": None,
        "fan2_speed": None,
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry", data={})

    # Setup installation devices data with OTC information for circuit 2
    installation_devices_data = {
        "heatingStatus": {
            "otcTypeHeatC1": OTC_HEATING_TYPE_FIX,
            "otcTypeCoolC1": OTC_COOLING_TYPE_FIX,
            "otcTypeHeatC2": OTC_HEATING_TYPE_GRADIENT,
            "otcTypeCoolC2": OTC_COOLING_TYPE_POINTS,
        }
    }

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        async_set_fan_speed=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
        get_temperature_limits=lambda zone_id, mode, data: (None, None),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        get_installation_devices_data=lambda: installation_devices_data,
        async_request_refresh=AsyncMock(return_value=None),
    )

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)
    attrs = entity.extra_state_attributes

    # Verify OTC attributes are present for zone 2 (circuit 2)
    assert "otc_heating_type" in attrs
    assert "otc_heating_type_name" in attrs
    assert "otc_cooling_type" in attrs
    assert "otc_cooling_type_name" in attrs
    assert attrs["otc_heating_type"] == OTC_HEATING_TYPE_GRADIENT
    assert attrs["otc_heating_type_name"] == "Gradient"
    assert attrs["otc_cooling_type"] == OTC_COOLING_TYPE_POINTS
    assert attrs["otc_cooling_type_name"] == "Points"


def test_otc_attributes_zone5_water_circuit(hass):
    """Test OTC attributes for zone 5 (water circuit C1)."""
    sensor_data = {
        "device_name": "Hitachi Yutaki",
        "device_id": 1234,
        "room_name": "Water Circuit",
        "parent_id": 1706,
        "room_id": 397,
        "operation_status": 5,
        "mode": 1,
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": True,
        "c2_demand": False,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 45.0,
        "setting_temperature": 50.0,
        "zone_id": 5,  # Water circuit
        "fan1_speed": None,
        "fan2_speed": None,
    }
    common_data = {"name": "Hitachi Yutaki", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry", data={})

    # Setup installation devices data with OTC information
    installation_devices_data = {
        "heatingStatus": {
            "otcTypeHeatC1": OTC_HEATING_TYPE_POINTS,
            "otcTypeCoolC1": OTC_COOLING_TYPE_FIX,
            "otcTypeHeatC2": OTC_HEATING_TYPE_NONE,
            "otcTypeCoolC2": OTC_COOLING_TYPE_NONE,
        }
    }

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        async_set_fan_speed=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
        get_temperature_limits=lambda zone_id, mode, data: (None, None),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        get_installation_devices_data=lambda: installation_devices_data,
        async_request_refresh=AsyncMock(return_value=None),
    )

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)
    attrs = entity.extra_state_attributes

    # Verify OTC attributes are present for zone 5 (circuit 1 water)
    assert "otc_heating_type" in attrs
    assert "otc_heating_type_name" in attrs
    assert "otc_cooling_type" in attrs
    assert "otc_cooling_type_name" in attrs
    assert attrs["otc_heating_type"] == OTC_HEATING_TYPE_POINTS
    assert attrs["otc_heating_type_name"] == "Points"
    assert attrs["otc_cooling_type"] == OTC_COOLING_TYPE_FIX
    assert attrs["otc_cooling_type_name"] == "Fixed"


def test_otc_attributes_no_installation_data(hass):
    """Test OTC attributes when no installation data is available."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Living",
        "parent_id": 1706,
        "room_id": 395,
        "operation_status": 5,
        "mode": 1,
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": True,
        "c2_demand": False,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 20.0,
        "setting_temperature": 21.0,
        "zone_id": 1,
        "fan1_speed": None,
        "fan2_speed": None,
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry", data={})

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        async_set_fan_speed=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
        get_temperature_limits=lambda zone_id, mode, data: (None, None),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        get_installation_devices_data=lambda: None,  # No installation data
        async_request_refresh=AsyncMock(return_value=None),
    )

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)
    attrs = entity.extra_state_attributes

    # Verify OTC attributes are not present when no installation data
    assert "otc_heating_type" not in attrs
    assert "otc_heating_type_name" not in attrs
    assert "otc_cooling_type" not in attrs
    assert "otc_cooling_type_name" not in attrs


def test_otc_attributes_zone3_dhw_no_otc(hass):
    """Test that OTC attributes are not present for zone 3 (DHW)."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": "Water Heater",
        "parent_id": 1706,
        "room_id": 398,
        "operation_status": 8,
        "mode": 1,
        "real_mode": 1,
        "on_off": 1,
        "timer_running": False,
        "alarm_code": 0,
        "c1_demand": False,
        "c2_demand": False,
        "ecocomfort": 1,
        "silent_mode": 0,
        "current_temperature": 50.0,
        "setting_temperature": 55.0,
        "zone_id": 3,  # DHW - should not have OTC
        "fan1_speed": None,
        "fan2_speed": None,
    }
    common_data = {"name": "Hitachi PAC", "firmware": "1.0.0"}
    entry = SimpleNamespace(entry_id="test-entry", data={})

    # Setup installation devices data with OTC information
    installation_devices_data = {
        "heatingStatus": {
            "otcTypeHeatC1": OTC_HEATING_TYPE_FIX,
            "otcTypeCoolC1": OTC_COOLING_TYPE_FIX,
            "otcTypeHeatC2": OTC_HEATING_TYPE_NONE,
            "otcTypeCoolC2": OTC_COOLING_TYPE_NONE,
        }
    }

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_hvac_mode=AsyncMock(return_value=True),
        async_set_temperature=AsyncMock(return_value=True),
        set_preset_modes=AsyncMock(return_value=True),
        async_set_silent_mode=AsyncMock(return_value=True),
        async_set_fan_speed=AsyncMock(return_value=True),
        is_fan_coil_compatible=lambda data: False,
        get_fan_control_availability=lambda circuit, mode, data: False,
        get_temperature_limits=lambda zone_id, mode, data: (None, None),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        get_installation_devices_data=lambda: installation_devices_data,
        async_request_refresh=AsyncMock(return_value=None),
    )

    entity = CSNetHomeClimate(hass, entry, sensor_data, common_data)
    attrs = entity.extra_state_attributes

    # Verify OTC attributes are NOT present for zone 3 (DHW has no circuits)
    assert "otc_heating_type" not in attrs
    assert "otc_heating_type_name" not in attrs
    assert "otc_cooling_type" not in attrs
    assert "otc_cooling_type_name" not in attrs
