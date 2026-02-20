"""Test CSNet Home water heater entity."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.components.water_heater import WaterHeaterEntityFeature
from homeassistant.const import PRECISION_WHOLE, UnitOfTemperature

from custom_components.csnet_home.const import (DOMAIN,
                                                SWIMMING_POOL_MAX_TEMPERATURE,
                                                SWIMMING_POOL_MIN_TEMPERATURE,
                                                WATER_HEATER_MIN_TEMPERATURE)
from custom_components.csnet_home.water_heater import CSNetHomeWaterHeater


def build_water_heater_entity(
    hass,
    *,
    zone_id=3,
    on_off=1,
    cur=43.0,
    setp=45,
    doing_boost=False,
    room_name="Water Heater",
):
    """Create a CSNetHomeWaterHeater with minimal surroundings."""
    sensor_data = {
        "device_name": "Hitachi PAC",
        "device_id": 1234,
        "room_name": room_name,
        "parent_id": 1706,
        "room_id": 396,
        "operation_status": 8 if zone_id == 3 else 10,
        "mode": 1,
        "real_mode": 1,
        "on_off": on_off,
        "timer_running": False,
        "alarm_code": 0,
        "doingBoost": doing_boost,
        "current_temperature": cur,
        "setting_temperature": setp,
        "zone_id": zone_id,
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

    # Setup installation devices data
    installation_devices_data = {
        "heatingStatus": {
            "dhwMax": 55,
        }
    }

    # Inject a fake API
    hass.data[DOMAIN][entry.entry_id]["api"] = SimpleNamespace(
        async_set_temperature=AsyncMock(return_value=True),
        set_water_heater_mode=AsyncMock(return_value=True),
        get_temperature_limits=lambda zone_id, mode, data: (
            None,
            55 if zone_id == 3 else 33,
        ),
    )
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = SimpleNamespace(
        get_sensors_data=lambda: [sensor_data],
        get_common_data=lambda: {"device_status": {1234: common_data}},
        get_installation_devices_data=lambda: installation_devices_data,
    )

    entity = CSNetHomeWaterHeater(hass, entry, sensor_data, common_data)
    return entity


def test_water_heater_initialization(hass):
    """Test water heater initialization."""
    entity = build_water_heater_entity(hass, zone_id=3, room_name="DHW")
    assert entity._attr_name == "DHW"
    assert not entity._is_swimming_pool
    assert entity._attr_temperature_unit == UnitOfTemperature.CELSIUS
    assert entity._attr_supported_features == (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    assert entity._attr_operation_list == ["off", "eco", "performance"]


def test_swimming_pool_initialization(hass):
    """Test swimming pool initialization."""
    entity = build_water_heater_entity(hass, zone_id=4, room_name="Pool")
    assert entity._attr_name == "Pool"
    assert entity._is_swimming_pool
    assert entity._attr_temperature_unit == UnitOfTemperature.CELSIUS
    assert entity._attr_supported_features == (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    assert entity._attr_operation_list == ["off", "on"]


def test_water_heater_operation_mode_eco(hass):
    """Test water heater in eco mode."""
    entity = build_water_heater_entity(hass, zone_id=3, on_off=1, doing_boost=False)
    assert entity._attr_operation_mode == "eco"
    assert entity.current_operation == "eco"


def test_water_heater_operation_mode_performance(hass):
    """Test water heater in performance mode."""
    entity = build_water_heater_entity(hass, zone_id=3, on_off=1, doing_boost=True)
    assert entity._attr_operation_mode == "performance"
    assert entity.current_operation == "performance"


def test_water_heater_operation_mode_off(hass):
    """Test water heater in off mode."""
    entity = build_water_heater_entity(hass, zone_id=3, on_off=0, doing_boost=False)
    assert entity._attr_operation_mode == "off"
    assert entity.current_operation == "off"


def test_swimming_pool_operation_mode_on(hass):
    """Test swimming pool in on mode."""
    entity = build_water_heater_entity(hass, zone_id=4, on_off=1)
    assert entity._attr_operation_mode == "on"
    assert entity.current_operation == "on"


def test_swimming_pool_operation_mode_off(hass):
    """Test swimming pool in off mode."""
    entity = build_water_heater_entity(hass, zone_id=4, on_off=0)
    assert entity._attr_operation_mode == "off"
    assert entity.current_operation == "off"


def test_water_heater_temperature_limits(hass):
    """Test water heater temperature limits."""
    entity = build_water_heater_entity(hass, zone_id=3)
    assert entity.min_temp == WATER_HEATER_MIN_TEMPERATURE
    assert entity.max_temp == 55  # From API


def test_swimming_pool_temperature_limits(hass):
    """Test swimming pool temperature limits."""
    entity = build_water_heater_entity(hass, zone_id=4)
    assert entity.min_temp == SWIMMING_POOL_MIN_TEMPERATURE
    assert entity.max_temp == SWIMMING_POOL_MAX_TEMPERATURE


def test_water_heater_precision(hass):
    """Test water heater precision."""
    entity = build_water_heater_entity(hass, zone_id=3)
    assert entity.precision == PRECISION_WHOLE


def test_water_heater_current_temperature(hass):
    """Test water heater current temperature reading."""
    entity = build_water_heater_entity(hass, zone_id=3, cur=43.0, setp=45)
    assert entity._attr_current_temperature == 43.0
    assert entity._attr_target_temperature == 45


def test_swimming_pool_current_temperature(hass):
    """Test swimming pool current temperature reading."""
    entity = build_water_heater_entity(hass, zone_id=4, cur=27.0, setp=28)
    assert entity._attr_current_temperature == 27.0
    assert entity._attr_target_temperature == 28


def test_water_heater_unique_id(hass):
    """Test water heater unique ID."""
    entity = build_water_heater_entity(hass, zone_id=3, room_name="DHW")
    assert entity.unique_id == f"{DOMAIN}-water-heater-DHW"


def test_swimming_pool_unique_id(hass):
    """Test swimming pool unique ID."""
    entity = build_water_heater_entity(hass, zone_id=4, room_name="Pool")
    assert entity.unique_id == f"{DOMAIN}-swimming-pool-Pool"


@pytest.mark.asyncio
async def test_water_heater_set_temperature(hass):
    """Test setting water heater temperature."""
    entity = build_water_heater_entity(hass, zone_id=3, setp=45)
    await entity.async_set_temperature(temperature=50)

    api = hass.data[DOMAIN]["test-entry"]["api"]
    api.async_set_temperature.assert_called_once()
    assert entity._sensor_data["setting_temperature"] == 50
    assert entity._attr_target_temperature == 50


@pytest.mark.asyncio
async def test_swimming_pool_set_temperature(hass):
    """Test setting swimming pool temperature."""
    entity = build_water_heater_entity(hass, zone_id=4, setp=28)
    await entity.async_set_temperature(temperature=30)

    api = hass.data[DOMAIN]["test-entry"]["api"]
    api.async_set_temperature.assert_called_once()
    assert entity._sensor_data["setting_temperature"] == 30
    assert entity._attr_target_temperature == 30


@pytest.mark.asyncio
async def test_water_heater_set_operation_mode_eco(hass):
    """Test setting water heater to eco mode."""
    entity = build_water_heater_entity(hass, zone_id=3, doing_boost=True)
    await entity.async_set_operation_mode("eco")

    api = hass.data[DOMAIN]["test-entry"]["api"]
    api.set_water_heater_mode.assert_called_once_with(3, 1706, "eco")
    assert entity._sensor_data["on_off"] == 1
    assert not entity._sensor_data["doingBoost"]
    assert entity._attr_operation_mode == "eco"


@pytest.mark.asyncio
async def test_water_heater_set_operation_mode_performance(hass):
    """Test setting water heater to performance mode."""
    entity = build_water_heater_entity(hass, zone_id=3, doing_boost=False)
    await entity.async_set_operation_mode("performance")

    api = hass.data[DOMAIN]["test-entry"]["api"]
    api.set_water_heater_mode.assert_called_once_with(3, 1706, "performance")
    assert entity._sensor_data["on_off"] == 1
    assert entity._sensor_data["doingBoost"]
    assert entity._attr_operation_mode == "performance"


@pytest.mark.asyncio
async def test_water_heater_set_operation_mode_off(hass):
    """Test turning off water heater."""
    entity = build_water_heater_entity(hass, zone_id=3, on_off=1)
    await entity.async_set_operation_mode("off")

    api = hass.data[DOMAIN]["test-entry"]["api"]
    api.set_water_heater_mode.assert_called_once_with(3, 1706, "off")
    assert entity._sensor_data["on_off"] == 0
    assert entity._attr_operation_mode == "off"


@pytest.mark.asyncio
async def test_swimming_pool_set_operation_mode_on(hass):
    """Test turning on swimming pool."""
    entity = build_water_heater_entity(hass, zone_id=4, on_off=0)
    await entity.async_set_operation_mode("on")

    api = hass.data[DOMAIN]["test-entry"]["api"]
    api.set_water_heater_mode.assert_called_once_with(4, 1706, "on")
    assert entity._sensor_data["on_off"] == 1
    assert entity._attr_operation_mode == "on"
    # Swimming pool should not have doingBoost attribute set
    assert "doingBoost" not in entity._sensor_data or not entity._sensor_data.get(
        "doingBoost"
    )


@pytest.mark.asyncio
async def test_swimming_pool_set_operation_mode_off(hass):
    """Test turning off swimming pool."""
    entity = build_water_heater_entity(hass, zone_id=4, on_off=1)
    await entity.async_set_operation_mode("off")

    api = hass.data[DOMAIN]["test-entry"]["api"]
    api.set_water_heater_mode.assert_called_once_with(4, 1706, "off")
    assert entity._sensor_data["on_off"] == 0
    assert entity._attr_operation_mode == "off"


@pytest.mark.asyncio
async def test_water_heater_update(hass):
    """Test water heater data update."""
    entity = build_water_heater_entity(hass, zone_id=3, room_name="DHW")

    # Update sensor data
    coordinator = hass.data[DOMAIN]["test-entry"]["coordinator"]
    updated_sensor = {
        "zone_id": 3,
        "room_name": "DHW",
        "on_off": 1,
        "doingBoost": True,
        "current_temperature": 50.0,
        "setting_temperature": 52,
    }
    coordinator.get_sensors_data = lambda: [updated_sensor]

    await entity.async_update()

    assert entity._sensor_data["current_temperature"] == 50.0
    assert entity._sensor_data["setting_temperature"] == 52


@pytest.mark.asyncio
async def test_swimming_pool_update(hass):
    """Test swimming pool data update."""
    entity = build_water_heater_entity(hass, zone_id=4, room_name="Pool")

    # Update sensor data
    coordinator = hass.data[DOMAIN]["test-entry"]["coordinator"]
    updated_sensor = {
        "zone_id": 4,
        "room_name": "Pool",
        "on_off": 1,
        "current_temperature": 29.0,
        "setting_temperature": 30,
    }
    coordinator.get_sensors_data = lambda: [updated_sensor]

    await entity.async_update()

    assert entity._sensor_data["current_temperature"] == 29.0
    assert entity._sensor_data["setting_temperature"] == 30


def test_water_heater_device_info(hass):
    """Test water heater device info."""
    entity = build_water_heater_entity(hass, zone_id=3, room_name="DHW")
    device_info = entity.device_info

    assert device_info["name"] == "Hitachi PAC-DHW"
    assert device_info["manufacturer"] == "Hitachi"
    assert "Remote Controller" in device_info["model"]
    assert device_info["sw_version"] == "1.0.0"


def test_swimming_pool_device_info(hass):
    """Test swimming pool device info."""
    entity = build_water_heater_entity(hass, zone_id=4, room_name="Pool")
    device_info = entity.device_info

    assert device_info["name"] == "Hitachi PAC-Pool"
    assert device_info["manufacturer"] == "Hitachi"
    assert "Remote Controller" in device_info["model"]
    assert device_info["sw_version"] == "1.0.0"
