"""Add entities through a real EntityPlatform to catch HA core API changes.

Unit tests that only read entity properties do not exercise the code Home
Assistant runs when an entity is registered (capability_attributes,
state_attributes, entity registry). Issue #206 was reported from that path,
so these tests add each entity type through ``EntityPlatform`` exactly like
Home Assistant does at runtime.
"""

from homeassistant.components.climate import ClimateEntityFeature, HVACMode
from homeassistant.components.water_heater import WaterHeaterEntityFeature
from pytest_homeassistant_custom_component.common import MockEntityPlatform

from custom_components.csnet_home.const import DOMAIN

from .test_climate import build_entity as build_climate_entity
from .test_water_heater import build_water_heater_entity


def _allow_listeners(entity):
    """Let a SimpleNamespace coordinator accept CoordinatorEntity listeners."""
    entity.coordinator.async_add_listener = lambda *_args, **_kwargs: lambda: None
    entity.coordinator.last_update_success = True
    # the builders replace the state write with a mock: use the real one here
    entity.__dict__.pop("async_write_ha_state", None)
    return entity


async def test_climate_entity_added_to_platform(hass):
    """Climate entity registers and exposes capability attributes (#206)."""
    entity = _allow_listeners(build_climate_entity(hass))
    assert isinstance(entity.supported_features, ClimateEntityFeature)

    platform = MockEntityPlatform(hass, domain="climate", platform_name=DOMAIN)
    await platform.async_add_entities([entity])
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.attributes["hvac_modes"]
    assert state.attributes["preset_modes"] == ["comfort", "eco"]
    assert "fan_modes" in state.attributes


async def test_water_heater_entity_added_to_platform(hass):
    """Water heater entity registers and exposes capability attributes."""
    entity = _allow_listeners(build_water_heater_entity(hass))
    assert isinstance(entity.supported_features, WaterHeaterEntityFeature)

    platform = MockEntityPlatform(hass, domain="water_heater", platform_name=DOMAIN)
    await platform.async_add_entities([entity])
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.attributes["operation_list"]


async def test_accepted_orders_reach_the_state_machine_at_once(hass):
    """After an order CSNet accepted, Home Assistant shows the new value before any poll."""
    entity = _allow_listeners(build_climate_entity(hass, mode=1, on_off=1, setp=19.0, ecocomfort=1))
    platform = MockEntityPlatform(hass, domain="climate", platform_name=DOMAIN)
    await platform.async_add_entities([entity])
    await hass.async_block_till_done()
    assert hass.states.get(entity.entity_id).state == HVACMode.HEAT

    await entity.async_set_temperature(temperature=21.5)
    assert hass.states.get(entity.entity_id).attributes["temperature"] == 21.5

    await entity.async_set_preset_mode("eco")
    assert hass.states.get(entity.entity_id).attributes["preset_mode"] == "eco"

    await entity.async_set_hvac_mode(HVACMode.OFF)
    assert hass.states.get(entity.entity_id).state == HVACMode.OFF


async def test_water_heater_orders_reach_the_state_machine_at_once(hass):
    """The same for the hot water tank."""
    entity = _allow_listeners(build_water_heater_entity(hass, zone_id=3, setp=45))
    platform = MockEntityPlatform(hass, domain="water_heater", platform_name=DOMAIN)
    await platform.async_add_entities([entity])
    await hass.async_block_till_done()

    await entity.async_set_temperature(temperature=50)
    assert hass.states.get(entity.entity_id).attributes["temperature"] == 50


async def test_water_heater_operation_mode_reaches_the_state_machine_at_once(hass):
    """The state shown is derived from the data: it must be derived again before it is written."""
    entity = _allow_listeners(build_water_heater_entity(hass, zone_id=3, on_off=1))
    platform = MockEntityPlatform(hass, domain="water_heater", platform_name=DOMAIN)
    await platform.async_add_entities([entity])
    await hass.async_block_till_done()
    assert hass.states.get(entity.entity_id).state == "eco"

    await entity.async_set_operation_mode("performance")
    assert hass.states.get(entity.entity_id).state == "performance"

    await entity.async_set_operation_mode("off")
    assert hass.states.get(entity.entity_id).state == "off"


async def test_fan_mode_reaches_the_state_machine_at_once(hass):
    """Silent mode and fan speed orders are shown without waiting for a poll."""
    entity = _allow_listeners(build_climate_entity(hass, silent_mode=0))
    platform = MockEntityPlatform(hass, domain="climate", platform_name=DOMAIN)
    await platform.async_add_entities([entity])
    await hass.async_block_till_done()
    assert hass.states.get(entity.entity_id).attributes["fan_mode"] == "auto"

    await entity.async_set_fan_mode("on")
    assert hass.states.get(entity.entity_id).attributes["fan_mode"] == "on"

    fan_coil = _allow_listeners(build_climate_entity(hass, is_fan_coil=True, fan2_speed=3, zone_id=2))
    await platform.async_add_entities([fan_coil])
    await hass.async_block_till_done()
    await fan_coil.async_set_fan_mode("low")
    assert hass.states.get(fan_coil.entity_id).attributes["fan_mode"] == "low"
