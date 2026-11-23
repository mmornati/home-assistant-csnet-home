"""The measured heat, corrected by what the unit's own heat counter teaches."""

from datetime import datetime, timedelta

import pytest

from custom_components.csnet_home.heat_calibration import MAX_FACTOR, MIN_LEARNING_RATE, MIN_WINDOW_KWH, HeatCalibration
from custom_components.csnet_home.sensor import CALCULATED_SENSOR_DESCRIPTIONS, CSNetHomeCalculatedSensor
from tests.test_sensor_decoding import DEVICE_DATA, RUNNING, _coordinator

START = datetime(2026, 11, 23, 10, 0)


def run(calibration, counter_kwh, measured_watts, use="spaceHeating", clean=True, start=START, counter=100, ratio=1.0, minutes=None):
    """Feed one minute after another while the integration measures measured_watts.

    The unit makes ``ratio`` times what is measured, so its counter rises by
    counter_kwh, in whole kWh as it reports it. Returns the time and the
    counter of the last reading.
    """
    minutes = minutes or int(round(counter_kwh * 60_000 / (measured_watts * ratio)))
    when = start
    for minute in range(minutes + 1):
        when = start + timedelta(minutes=minute)
        produced = counter_kwh * minute / minutes
        calibration.observe(when, counter + int(produced), use, measured_watts, clean)
    return when, counter + counter_kwh


def test_the_first_window_teaches_the_ratio_of_counter_to_measured_heat():
    """The counter counts 5 % more than the probes: the factor goes to about 1.05."""
    calibration = HeatCalibration()
    run(calibration, 7, 6000, ratio=1.05)
    assert calibration.windows == {"spaceHeating": 1}
    assert calibration.factor("spaceHeating") == pytest.approx(1.05, abs=0.02)


def test_a_window_too_short_teaches_nothing():
    """Fewer kWh than a window needs: no factor yet."""
    calibration = HeatCalibration()
    run(calibration, MIN_WINDOW_KWH["spaceHeating"] - 1, 4000)
    assert calibration.factors == {}


def test_hot_water_has_a_factor_of_its_own():
    """The tank is measured at another probe: it learns apart from space heating."""
    calibration = HeatCalibration()
    run(calibration, 4, 4000, use="dhw", ratio=0.9)
    assert calibration.factor("dhw") == pytest.approx(0.9, abs=0.03)
    assert calibration.factor("spaceHeating") == 1.0


def test_cooling_has_a_factor_of_its_own():
    """Cooling learns apart from space heating, though both are measured at the water outlet."""
    calibration = HeatCalibration()
    run(calibration, 7, 5000, use="spaceCooling", ratio=1.1)
    assert calibration.factor("spaceCooling") == pytest.approx(1.1, abs=0.03)
    assert calibration.factor("spaceHeating") == 1.0


def test_a_use_not_calibrated_is_left_as_measured():
    """The pool is not calibrated."""
    calibration = HeatCalibration()
    run(calibration, 8, 3000, use="swp")
    assert calibration.factors == {}
    assert calibration.factor("swp") == 1.0


@pytest.mark.parametrize("dirty_minute", [10, 60])
def test_a_window_with_a_defrost_or_another_heat_source_teaches_nothing(dirty_minute):
    """A reading measured elsewhere, or during a defrost, spoils the window it falls in."""
    calibration = HeatCalibration()
    start, counter = START, 100
    for minute in range(121):
        when = start + timedelta(minutes=minute)
        calibration.observe(when, counter + minute // 20, "spaceHeating", 3000, minute != dirty_minute)
    # the windows the spoilt reading fell in are dropped, the later ones still count
    assert calibration.windows.get("spaceHeating", 0) <= 1


def test_a_change_of_use_inside_a_window_teaches_nothing():
    """A window that turns from space heating to hot water says nothing about space heating."""
    calibration = HeatCalibration()
    for minute in range(61):
        use = "spaceHeating" if minute < 50 else "dhw"
        calibration.observe(START + timedelta(minutes=minute), 100 + minute // 9, use, 6000, True)
    assert calibration.factors == {}


def test_a_gap_in_the_readings_breaks_the_window():
    """Heat made while no reading came in is unknown: the window starts again."""
    calibration = HeatCalibration()
    when, counter = run(calibration, 3, 3000)
    run(calibration, 3, 3000, start=when + timedelta(minutes=30), counter=counter + 2)
    assert calibration.factors == {}


def test_a_counter_without_a_reading_breaks_the_window():
    """A reading without the counter drops the window under way."""
    calibration = HeatCalibration()
    when, counter = run(calibration, 3, 3000)
    calibration.observe(when + timedelta(minutes=1), None, "spaceHeating", 3000, True)
    run(calibration, 3, 3000, start=when + timedelta(minutes=2), counter=counter)
    assert calibration.factors == {}


def test_a_window_far_off_is_left_out():
    """A counter that rose four times what was measured says something else went on."""
    calibration = HeatCalibration()
    run(calibration, 8, 3000, minutes=40)
    assert calibration.factors == {}


def test_the_counter_starting_over_is_followed():
    """The counter starts over after 249: the window goes on across it."""
    calibration = HeatCalibration()
    run(calibration, 7, 6000, ratio=1.05, counter=245)
    assert calibration.factor("spaceHeating") == pytest.approx(1.05, abs=0.02)


def test_after_the_first_windows_each_one_moves_the_factor_a_little():
    """Ten windows are averaged; the eleventh moves the factor by a tenth of its distance."""
    calibration = HeatCalibration()
    calibration.factors["spaceHeating"] = 1.0
    calibration.windows["spaceHeating"] = 20
    calibration._learn("spaceHeating", 11, 10.0)  # pylint: disable=protected-access
    assert calibration.factor("spaceHeating") == pytest.approx(1.0 + MIN_LEARNING_RATE * 0.1)


def test_the_factor_stays_within_its_limits():
    """However far the windows say, the correction stays within its range."""
    calibration = HeatCalibration()
    calibration._learn("spaceHeating", 19, 10.0)  # pylint: disable=protected-access
    assert calibration.factor("spaceHeating") == MAX_FACTOR


def _heat_sensor(reading, factors):
    sensor = CSNetHomeCalculatedSensor(_coordinator(dict(reading)), DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["heating_power"])
    calibration = HeatCalibration()
    calibration.factors.update(factors)
    calibration.windows.update({use: 3 for use in factors})
    sensor.coordinator.heat_calibration = calibration
    return sensor


@pytest.mark.parametrize(
    ("reading", "factor"),
    [
        ({"operationStatus": 6}, 1.05),  # space heating, water outlet
        ({"operationStatus": 8, "waterOutletHPTemp": 45}, 0.9),  # hot water, exchanger outlet
        ({"operationStatus": 3, "waterOutletTemp": 36}, 1.2),  # cooling, water outlet
    ],
    ids=["space heating", "hot water", "cooling"],
)
def test_the_heat_power_uses_the_factor_of_its_use(reading, factor):
    """Each use is corrected by its own factor."""
    heating_status = RUNNING | reading
    sensor = _heat_sensor(heating_status, {"spaceHeating": 1.05, "dhw": 0.9, "spaceCooling": 1.2})
    plain = sensor._measure_heat(heating_status)[0]  # pylint: disable=protected-access
    assert sensor._get_thermal_power_values(heating_status)[0] == round(plain * factor, 2)  # pylint: disable=protected-access


@pytest.mark.parametrize(
    "reading",
    [
        {"operationStatus": 6, "waterOutletHPTemp": 45, "systemStatus2Flags": 1 << 8},  # backup heater on
        {"operationStatus": 6, "waterOutletTemp": -127},  # water outlet failed: the exchanger outlet stands in
    ],
    ids=["backup heater", "probe standing in"],
)
def test_the_heat_power_is_left_as_measured_elsewhere(reading):
    """Another heat source, or a probe standing in for another: no correction."""
    heating_status = RUNNING | reading
    sensor = _heat_sensor(heating_status, {"spaceHeating": 1.05, "dhw": 0.9})
    assert sensor._get_thermal_power_values(heating_status)[0] == sensor._measure_heat(heating_status)[0]  # pylint: disable=protected-access


def test_the_heat_power_shows_what_was_learnt():
    """The factors and the windows behind them are on the heat power."""
    sensor = _heat_sensor(RUNNING | {"operationStatus": 6}, {"spaceHeating": 1.0544})
    assert sensor.extra_state_attributes == {"heat_calibration": {"spaceHeating": {"factor": 1.054, "windows": 3}}}
