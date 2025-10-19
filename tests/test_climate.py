"""Test CSNet Home climate entity."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from homeassistant.components.climate import HVACAction, HVACMode

from custom_components.csnet_home.climate import CSNetHomeClimate
from custom_components.csnet_home.const import DOMAIN


def build_entity(hass, *, mode=1, on_off=1, cur=19.5, setp=20.0, ecocomfort=1):
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
    """Restore last mode when turning on (heat/cool)."""
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
