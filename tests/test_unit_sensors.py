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
    # reported by the maintainer's unit although it has no tank, fan coils, R290 circuit or cascade
    "controlTypeDHW": 0,
    "antiLegionellaStatusDHW": 0,
    "antiLegionellaSettingDHW": 55,
    "realFan1Speed": 0,
    "realFan2Speed": 0,
    "primaryFlowR290": -1,
    "systemConfigBits": 4035,
}


def _unit(status, cascade=None):
    """Wrap a unit status (and cascade info) as the indoor unit CSNet sends."""
    if not isinstance(status, dict):
        return status
    return {"heatingStatus": status, "cascadeInfo": cascade or {"cascadeEnabledUnits": 0, "cascadeWorkingUnits": 0, "cascadeRequiredUnits": 0}}


def _values(status, zone_ids, cascade=None):
    """Return {key: value} of the sensors created for a unit."""
    unit = _unit(status, cascade)
    coordinator = SimpleNamespace(async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    return {d.key: CSNetHomeUnitSensor(coordinator, d, None, lambda: unit).native_value for d in unit_sensor_descriptions(unit, zone_ids)}


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
    description = next(d for d in unit_sensor_descriptions(_unit(status), {1}) if d.key == "c1_eco_offset_heating")
    entity = CSNetHomeUnitSensor(coordinator, description, None, lambda: _unit(status))
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


def test_unit_without_the_equipment_gets_none_of_its_sensors():
    """Values a unit reports for equipment it does not have create nothing."""
    keys = set(_values(LIVE, {1, 2}))
    assert not {k for k in keys if k.startswith(("dhw_", "cascade_", "primary_")) or "fan_speed" in k}


@pytest.mark.parametrize(("code", "mode"), [(0, "economic"), (1, "standard"), (2, "high_demand"), (7, "economic")])
def test_hot_water_tank_sensors(code, mode):
    """A unit with a tank shows how it is heated and the anti-legionella temperature."""
    values = _values(LIVE | {"controlTypeDHW": code}, {1, 3})
    assert values["dhw_mode"] == mode
    assert values["dhw_anti_legionella_temperature"] == 55.0
    # and nothing for a tank without a zone
    assert "dhw_mode" not in _values(LIVE | {"controlTypeDHW": code}, {1})


def test_fan_coil_sensors_need_the_fan_coil_bit_and_the_circuit():
    """The speed a fan really runs at, per circuit, only on units set up for fan coils."""
    fan_coil = LIVE | {"systemConfigBits": 4035 | 0x2000, "realFan1Speed": 3, "realFan2Speed": 1}
    assert _values(fan_coil, {1})["c1_fan_speed_actual"] == "high"
    assert "c2_fan_speed_actual" not in _values(fan_coil, {1})
    assert _values(fan_coil, {5, 6})["c2_fan_speed_actual"] == "low"
    # a speed outside the four the web app knows is not shown as one of them
    assert "c1_fan_speed_actual" not in _values(fan_coil | {"realFan1Speed": 9}, {1})
    # without the bit, the zeros every unit reports mean nothing
    assert "c1_fan_speed_actual" not in _values(LIVE | {"realFan1Speed": 3}, {1})


@pytest.mark.parametrize(("raw", "expected"), [(152, 1.52), (5, 0.05), (0, None), (-1, None), (None, None)])
def test_primary_water_flow_is_in_hundredths(raw, expected):
    """R290 units report the primary circuit's flow in hundredths of m3/h; other units report -1."""
    assert _values(LIVE | {"primaryFlowR290": raw}, {1}).get("primary_water_flow") == expected


def test_cascade_sensors_only_on_a_cascade():
    """Units enabled, working and required, when the unit is part of a cascade."""
    cascade = {"cascadeEnabledUnits": 3, "cascadeWorkingUnits": 2, "cascadeRequiredUnits": 2}
    values = _values(LIVE, {1}, cascade)
    assert (values["cascade_units_enabled"], values["cascade_units_working"], values["cascade_units_required"]) == (3, 2, 2)
    assert not [k for k in _values(LIVE, {1}) if k.startswith("cascade_")]
    assert not [k for k in _values(LIVE, {1}, {"cascadeEnabledUnits": 0, "cascadeWorkingUnits": 1}) if k.startswith("cascade_")]


def test_enum_sensors_declare_their_options():
    """Home Assistant refuses an enum state that is not among the declared options."""
    from custom_components.csnet_home.unit_sensors import DHW_MODES, FAN_SPEEDS, UNIT_SENSOR_DESCRIPTIONS

    by_key = {d.key: d for d in UNIT_SENSOR_DESCRIPTIONS}
    assert by_key["dhw_mode"].options == list(DHW_MODES.values())
    assert by_key["c1_fan_speed_actual"].options == list(FAN_SPEEDS.values())
    assert len(by_key) == len(UNIT_SENSOR_DESCRIPTIONS)
