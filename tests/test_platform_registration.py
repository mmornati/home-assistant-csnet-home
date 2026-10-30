"""Add entities through a real EntityPlatform to catch HA core API changes.

Unit tests that only read entity properties do not exercise the code Home
Assistant runs when an entity is registered (capability_attributes,
state_attributes, entity registry). Issue #206 was reported from that path,
so these tests add each entity type through ``EntityPlatform`` exactly like
Home Assistant does at runtime.
"""

from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.components.water_heater import WaterHeaterEntityFeature
from pytest_homeassistant_custom_component.common import MockEntityPlatform

from custom_components.csnet_home.const import DOMAIN

from .test_climate import build_entity as build_climate_entity
from .test_water_heater import build_water_heater_entity


def _allow_listeners(entity):
    """Let a SimpleNamespace coordinator accept CoordinatorEntity listeners."""
    entity.coordinator.async_add_listener = lambda *_args, **_kwargs: lambda: None
    entity.coordinator.last_update_success = True
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
    entity = build_water_heater_entity(hass)
    assert isinstance(entity.supported_features, WaterHeaterEntityFeature)

    platform = MockEntityPlatform(hass, domain="water_heater", platform_name=DOMAIN)
    await platform.async_add_entities([entity])
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.attributes["operation_list"]
