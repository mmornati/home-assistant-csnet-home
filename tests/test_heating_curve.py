"""Heating curves the user copies into the options, and the sensors computed from them."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import DOMAIN, OTC_HEATING_TYPE_FIX, OTC_HEATING_TYPE_GRADIENT, OTC_HEATING_TYPE_POINTS
from custom_components.csnet_home.heating_curve import CSNetHomeHeatingCurveSensor, HeatingCurve, curve_circuits, curve_from_options, unique_id
from custom_components.csnet_home.sensor import _heating_curve_sensors

POINTS_C1 = {
    "c1_low_ambient_temperature": -10.0,
    "c1_water_at_low_ambient": 35.0,
    "c1_high_ambient_temperature": 15.0,
    "c1_water_at_high_ambient": 25.0,
}
GRADIENT_C2 = {"c2_gradient": 1.2}


def _status(**changes):
    """Return a unit with an underfloor circuit on points and a radiator circuit on gradient."""
    status = {
        "otcTypeHeatC1": OTC_HEATING_TYPE_POINTS,
        "otcTypeHeatC2": OTC_HEATING_TYPE_GRADIENT,
        "outdoorAmbientAverageTemp": 5,
        "heatMinC1": 20,
        "heatMaxC1": 45,
    }
    status.update(changes)
    return status


def _coordinator():
    """Return a coordinator that only tracks listeners."""
    return SimpleNamespace(async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)


def _sensor(options, status, circuit=1):
    """Return the curve sensor of a circuit for a unit status."""
    return CSNetHomeHeatingCurveSensor(_coordinator(), circuit, options, None, lambda: status)


# --- the curve -----------------------------------------------------------


@pytest.mark.parametrize(
    ("outdoor", "water"),
    [(-20, 35.0), (-10, 35.0), (2.5, 30.0), (15, 25.0), (25, 25.0)],
)
def test_points_curve_is_a_line_between_the_points_and_flat_outside(outdoor, water):
    """Check that points curve is a line between the points and flat outside."""
    curve = curve_from_options(POINTS_C1, 1, OTC_HEATING_TYPE_POINTS)
    assert curve.water_temperature(outdoor) == pytest.approx(water)


@pytest.mark.parametrize(("outdoor", "water"), [(20, 20.0), (25, 20.0), (0, 44.0), (-10, 56.0)])
def test_gradient_curve_starts_at_20_20(outdoor, water):
    """1.2 °C more water for every degree below 20 °C outside."""
    curve = curve_from_options(GRADIENT_C2, 2, OTC_HEATING_TYPE_GRADIENT)
    assert curve.water_temperature(outdoor) == pytest.approx(water)


def test_vertex_offset_moves_the_whole_curve():
    """Check that vertex offset moves the whole curve."""
    curve = curve_from_options({**POINTS_C1, "c1_vertex_offset": -2.0}, 1, OTC_HEATING_TYPE_POINTS)
    assert curve.water_temperature(-15) == 33.0
    assert curve.water_temperature(20) == 23.0


@pytest.mark.parametrize(
    ("options", "curve_type"),
    [
        (POINTS_C1, OTC_HEATING_TYPE_GRADIENT),  # the unit uses another kind of curve
        (POINTS_C1, OTC_HEATING_TYPE_FIX),
        (POINTS_C1, None),
        ({k: v for k, v in POINTS_C1.items() if k != "c1_water_at_high_ambient"}, OTC_HEATING_TYPE_POINTS),
        ({**POINTS_C1, "c1_high_ambient_temperature": -10.0}, OTC_HEATING_TYPE_POINTS),
        ({**POINTS_C1, "c1_water_at_low_ambient": True}, OTC_HEATING_TYPE_POINTS),
        ({}, OTC_HEATING_TYPE_POINTS),
    ],
)
def test_no_curve_from_incomplete_or_mismatched_options(options, curve_type):
    """Check that no curve from incomplete or mismatched options."""
    assert curve_from_options(options, 1, curve_type) is None


def test_curve_is_drawn_every_5_degrees_and_at_its_bends():
    """Check that curve is drawn every 5 degrees and at its bends."""
    curve = HeatingCurve(OTC_HEATING_TYPE_POINTS, -7.0, 35.0, 18.0, 25.0)
    assert curve.draw_at() == [-20.0, -15.0, -10.0, -7.0, -5.0, 0.0, 5.0, 10.0, 15.0, 18.0, 20.0, 25.0]


@pytest.mark.parametrize(
    ("status", "zone_ids", "expected"),
    [
        (_status(), {1, 2}, {1: OTC_HEATING_TYPE_POINTS, 2: OTC_HEATING_TYPE_GRADIENT}),
        (_status(), {1}, {1: OTC_HEATING_TYPE_POINTS}),  # no second circuit
        (_status(), {5, 6}, {1: OTC_HEATING_TYPE_POINTS, 2: OTC_HEATING_TYPE_GRADIENT}),
        (_status(otcTypeHeatC1=OTC_HEATING_TYPE_FIX, otcTypeHeatC2=0), {1, 2}, {}),
        (None, {1, 2}, {}),
    ],
)
def test_only_circuits_with_a_points_or_gradient_curve_are_offered(status, zone_ids, expected):
    """Check that only circuits with a points or gradient curve are offered."""
    assert curve_circuits(status, zone_ids) == expected


# --- the sensor ----------------------------------------------------------


def test_sensor_gives_the_water_temperature_at_the_average_outdoor_temperature():
    """Check that sensor gives the water temperature at the average outdoor temperature."""
    sensor = _sensor(POINTS_C1, _status())
    assert sensor.available
    assert sensor.native_value == 29.0
    attributes = sensor.extra_state_attributes
    assert attributes["curve_type"] == "Points"
    assert attributes["outdoor_temperature"] == 5.0
    assert attributes["minimum_water_temperature"] == 20.0
    assert attributes["maximum_water_temperature"] == 45.0
    assert [-10.0, 35.0] in attributes["curve"]
    assert [15.0, 25.0] in attributes["curve"]
    assert sensor.unique_id == "csnet_home-unit-c1_heating_curve_water_temperature"


def test_sensor_keeps_within_the_water_limits_the_unit_reports():
    """Check that sensor keeps within the water limits the unit reports."""
    status = _status(outdoorAmbientAverageTemp=-15, heatMinC2=25, heatMaxC2=50)
    sensor = _sensor(GRADIENT_C2, status, circuit=2)
    assert sensor.native_value == 50.0  # 62 on the curve
    assert sensor.extra_state_attributes["curve"][0] == [-20.0, 50.0]
    status["outdoorAmbientAverageTemp"] = 22
    assert sensor.native_value == 25.0  # 20 on the curve


def test_sensor_without_reported_limits_is_not_clamped():
    """Check that sensor without reported limits is not clamped."""
    sensor = _sensor(GRADIENT_C2, _status(outdoorAmbientAverageTemp=-15), circuit=2)
    assert sensor.native_value == 62.0
    assert sensor.extra_state_attributes["maximum_water_temperature"] is None


@pytest.mark.parametrize(
    "status",
    [
        _status(otcTypeHeatC1=OTC_HEATING_TYPE_GRADIENT),  # installer changed the kind of curve
        _status(outdoorAmbientAverageTemp=-127),  # no outdoor probe
        _status(outdoorAmbientAverageTemp=None),
        None,
    ],
)
def test_sensor_is_unavailable_when_it_cannot_follow_the_unit(status):
    """Check that sensor is unavailable when it cannot follow the unit."""
    sensor = _sensor(POINTS_C1, status)
    assert not sensor.available
    assert sensor.native_value is None


# --- creation and removal ------------------------------------------------


def _coordinator_with(status, zone_ids=(1, 2)):
    """Return a coordinator holding a unit status and zones."""
    installation = {"data": [{"indoors": [{"heatingStatus": status}]}]}
    return SimpleNamespace(
        async_add_listener=lambda *a, **k: lambda: None,
        last_update_success=True,
        get_installation_devices_data=lambda: installation,
        get_sensors_data=lambda: [{"zone_id": zone} for zone in zone_ids],
        get_common_data=lambda: {},
    )


async def test_sensors_exist_only_for_described_circuits(hass: HomeAssistant):
    """Check that sensors exist only for described circuits."""
    entry = MockConfigEntry(domain=DOMAIN, options={**POINTS_C1})
    sensors = _heating_curve_sensors(hass, entry, _coordinator_with(_status()))
    assert [s.unique_id for s in sensors] == [unique_id(1)]


async def test_a_removed_curve_takes_its_sensor_away(hass: HomeAssistant):
    """Check that a removed curve takes its sensor away."""
    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", DOMAIN, unique_id(2))
    entry = MockConfigEntry(domain=DOMAIN, options={**POINTS_C1})
    _heating_curve_sensors(hass, entry, _coordinator_with(_status()))
    assert registry.async_get_entity_id("sensor", DOMAIN, unique_id(2)) is None


async def test_nothing_is_removed_while_the_unit_status_is_missing(hass: HomeAssistant):
    """A failed request at start-up must not wipe the user's sensors."""
    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", DOMAIN, unique_id(1))
    entry = MockConfigEntry(domain=DOMAIN, options={**POINTS_C1})
    coordinator = _coordinator_with(None)
    coordinator.get_installation_devices_data = lambda: None
    assert _heating_curve_sensors(hass, entry, coordinator) == []
    assert registry.async_get_entity_id("sensor", DOMAIN, unique_id(1)) is not None


# --- the options form ----------------------------------------------------


@pytest.fixture(autouse=True)
def bypass_setup_entry():
    """Skip the real setup when the options flow reloads the entry."""
    with (
        patch("custom_components.csnet_home.async_setup_entry", return_value=True),
        patch("custom_components.csnet_home.async_unload_entry", return_value=True),
    ):
        yield


async def _open_options(hass, status, options=None, loaded=True):
    """Add an entry and open its options form."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=options or {})
    entry.add_to_hass(hass)
    if loaded:
        entry.runtime_data = SimpleNamespace(coordinator=_coordinator_with(status))
    return entry, await hass.config_entries.options.async_init(entry.entry_id)


def _fields(result):
    """Return the field names of a form."""
    return [str(key) for key in result["data_schema"].schema]


async def test_form_asks_for_the_fields_of_each_circuits_curve(hass: HomeAssistant):
    """Check that form asks for the fields of each circuits curve."""
    _, result = await _open_options(hass, _status())
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert _fields(result) == [
        "c1_low_ambient_temperature",
        "c1_water_at_low_ambient",
        "c1_high_ambient_temperature",
        "c1_water_at_high_ambient",
        "c1_vertex_offset",
        "c2_gradient",
        "c2_vertex_offset",
    ]
    assert result["description_placeholders"]["circuits"] == "C1: Points, C2: Gradient"


async def test_form_stores_the_curves(hass: HomeAssistant):
    """Check that form stores the curves."""
    entry, result = await _open_options(hass, _status(), options={"c2_gradient": 0.8, "c2_vertex_offset": 1.0})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {**POINTS_C1, "c2_gradient": 1.2})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    # an emptied field is left out by the frontend: its value goes
    assert dict(entry.options) == {**POINTS_C1, "c2_gradient": 1.2}


async def test_form_keeps_curves_of_circuits_it_does_not_show(hass: HomeAssistant):
    """A circuit the unit no longer reports keeps what the user entered."""
    entry, result = await _open_options(hass, _status(otcTypeHeatC2=OTC_HEATING_TYPE_FIX), options={"c2_gradient": 0.8})
    result = await hass.config_entries.options.async_configure(result["flow_id"], POINTS_C1)
    assert dict(entry.options) == {**POINTS_C1, "c2_gradient": 0.8}


async def test_form_refuses_a_half_filled_curve(hass: HomeAssistant):
    """Check that form refuses a half filled curve."""
    _, result = await _open_options(hass, _status())
    partial = {k: v for k, v in POINTS_C1.items() if k != "c1_water_at_low_ambient"}
    result = await hass.config_entries.options.async_configure(result["flow_id"], partial)
    assert result["errors"] == {"c1_water_at_low_ambient": "incomplete_curve"}


async def test_form_refuses_points_in_the_wrong_order(hass: HomeAssistant):
    """Check that form refuses points in the wrong order."""
    _, result = await _open_options(hass, _status())
    result = await hass.config_entries.options.async_configure(result["flow_id"], {**POINTS_C1, "c1_high_ambient_temperature": -15.0})
    assert result["errors"] == {"c1_high_ambient_temperature": "high_ambient_not_above_low"}


@pytest.mark.parametrize(
    ("status", "loaded", "reason"),
    [
        (_status(otcTypeHeatC1=OTC_HEATING_TYPE_FIX, otcTypeHeatC2=0), True, "no_heating_curve"),
        (_status(), False, "not_loaded"),
    ],
)
async def test_form_explains_when_there_is_nothing_to_describe(hass: HomeAssistant, status, loaded, reason):
    """Check that form explains when there is nothing to describe."""
    _, result = await _open_options(hass, status, loaded=loaded)
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == reason


def test_every_options_field_has_a_text_in_each_language():
    """Check that every options field has a text in each language."""
    base = Path(__file__).parent.parent / "custom_components" / "csnet_home"
    reference = json.loads((base / "strings.json").read_text(encoding="utf-8"))["options"]
    fields = {
        f"c{n}_{f}"
        for n in (1, 2)
        for f in ("low_ambient_temperature", "water_at_low_ambient", "high_ambient_temperature", "water_at_high_ambient", "gradient", "vertex_offset")
    }
    assert set(reference["step"]["init"]["data"]) == fields
    assert set(reference["step"]["init"]["data_description"]) == fields
    assert set(reference["error"]) == {"incomplete_curve", "high_ambient_not_above_low"}
    assert set(reference["abort"]) == {"not_loaded", "no_heating_curve"}

    def keys(node, prefix=""):
        if isinstance(node, dict):
            return {path for key, value in node.items() for path in keys(value, f"{prefix}{key}.")}
        return {prefix}

    for language in ("en", "fr", "es"):
        translated = json.loads((base / "translations" / f"{language}.json").read_text(encoding="utf-8"))["options"]
        assert keys(translated) == keys(reference), language
