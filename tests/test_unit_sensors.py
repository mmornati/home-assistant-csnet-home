"""Extra unit sensors, hot water boost and fixed water temperature limits."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from custom_components.csnet_home.unit_sensors import CSNetHomeUnitSensor, unit_sensor_descriptions

from .test_water_heater import build_water_heater_entity

# What the maintainer's unit reports
LIVE = {
    "ambientTempRoomThermostatZ1": 200,
    "ambientTempRoomWirelessZ1": 205,
    "ambientTempRoomThermostatZ2": 195,
    "ambientTempRoomWirelessZ2": 0,
    "ecoOffsetTempHeatC1": 3,
    "ecoOffsetTempHeatC2": 3,
    "pcbSoft": 534,
}


def _values(status, zone_ids):
    """Return {key: value} of the sensors created for a unit."""
    coordinator = SimpleNamespace(async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    return {d.key: CSNetHomeUnitSensor(coordinator, d, None, lambda: status).native_value for d in unit_sensor_descriptions(status, zone_ids)}


def test_two_circuit_unit_gets_what_it_reports():
    """Whole degrees and a hex software number; the ambiguous thermostat readings are not exposed."""
    assert _values(LIVE, {1, 2}) == {
        "c1_eco_offset_heating": 3.0,
        "c2_eco_offset_heating": 3.0,
        "indoor_board_software": "0x0216",
    }


def test_circuit_sensors_follow_the_zones():
    """A unit with one circuit gets no circuit 2 sensors, whatever the status contains."""
    assert not [key for key in _values(LIVE, {1}) if key.startswith("c2_")]
    assert not [key for key in _values(LIVE, {3}) if key.startswith(("c1_", "c2_"))]
    assert "c2_eco_offset_heating" in _values(LIVE, {6})


@pytest.mark.parametrize("status", [None, {}, "text", {"pcbSoft": -1, "ecoOffsetTempHeatC1": None, "ecoOffsetTempHeatC2": -1}])
def test_nothing_is_created_for_missing_values(status):
    """Markers, missing keys and missing status give no entity."""
    assert _values(status, {1, 2}) == {}


def test_a_value_that_disappears_becomes_unknown():
    """Created while reported; unknown, not wrong, when the unit stops reporting it."""
    status = dict(LIVE)
    coordinator = SimpleNamespace(async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    description = next(d for d in unit_sensor_descriptions(status, {1}) if d.key == "c1_eco_offset_heating")
    entity = CSNetHomeUnitSensor(coordinator, description, None, lambda: status)
    assert entity.native_value == 3.0
    status["ecoOffsetTempHeatC1"] = -1
    assert entity.native_value is None


@pytest.mark.parametrize(
    ("has_boost", "doing_boost", "expected"),
    [
        (None, False, ["off", "eco", "performance"]),
        (True, False, ["off", "eco", "performance"]),
        (False, False, ["off", "eco"]),
        (False, True, ["off", "eco", "performance"]),
    ],
)
def test_hot_water_boost_is_offered_only_where_the_unit_has_it(hass, has_boost, doing_boost, expected):
    """Only an explicit "no" removes boost, and never while a boost is running."""
    entity = build_water_heater_entity(hass, zone_id=3, doing_boost=doing_boost)
    entity._sensor_data["has_boost"] = has_boost
    entity._update_attributes()
    assert entity.operation_list == expected


def test_pool_modes_are_unchanged(hass):
    """A pool is on or off."""
    assert build_water_heater_entity(hass, zone_id=4).operation_list == ["off", "on"]


@pytest.mark.parametrize(
    ("limits", "expected"),
    [((25, 55), (25.0, 55.0)), ((250, 550), (25.0, 55.0)), ((0, 0), None), ((None, None), None), ((60, 20), None), (("a", 55), None), ((20, 150), None)],
)
def test_fixed_water_temperature_limits_come_from_the_unit(limits, expected):
    """The unit's limits when it reports sensible ones (also in tenths, like the climate entity), the usual ones otherwise."""
    from custom_components.csnet_home.number import CSNetHomeFixedWaterTemperatureNumber

    coordinator = MagicMock()
    coordinator.get_installation_devices_data.return_value = {"data": []}
    entry = SimpleNamespace(runtime_data=SimpleNamespace(api=SimpleNamespace(get_temperature_limits=lambda zone_id, mode, data, indoor_id=None: limits)))
    sensor_data = {"zone_id": 5, "device_id": 1, "room_name": "Floor", "parent_id": 100, "device_name": "PAC"}
    entity = CSNetHomeFixedWaterTemperatureNumber(coordinator, sensor_data, {}, circuit=1, mode=1, entry=entry)
    default = entity._default_limits
    assert (entity.native_min_value, entity.native_max_value) == (expected or default)
