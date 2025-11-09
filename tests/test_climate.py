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
    WATER_CIRCUIT_MIN_HEAT,
    WATER_CIRCUIT_MAX_HEAT,
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


# ... existing code ...
*** End Patch to File tests/test_climate.py (truncated for brevity)***