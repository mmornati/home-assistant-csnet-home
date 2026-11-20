"""Tests for how raw CSNet values are decoded into sensor states."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

from custom_components.csnet_home.const import POWER_SUPPLY_THREE_PHASE
from custom_components.csnet_home.coordinator import CSNetHomeCoordinator
from custom_components.csnet_home.helpers import extract_heating_status
from custom_components.csnet_home.power_calibration import MAX_FACTOR, PowerCalibration
from custom_components.csnet_home.sensor import (
    CALCULATED_SENSOR_DESCRIPTIONS,
    COMPRESSOR_SENSOR_DESCRIPTIONS,
    CRANKCASE_HEATER_POWER_W,
    DAILY_SENSOR_DESCRIPTIONS,
    FAN_DEFAULT_POWER_W,
    FAN_MAX_POWER_W,
    INSTALLATION_SENSOR_DESCRIPTIONS,
    INSTANT_COP_WINDOW,
    MAX_ENERGY_INTEGRATION_HOURS,
    OUTDOOR_ELECTRONICS_POWER_W,
    PUMP_MAX_POWER_W,
    PUMP_MIN_POWER_W,
    STANDBY_POWER_W,
    SUCTION_PRESSURE_MISSING,
    WATTS_PER_AMP_SINGLE_PHASE,
    WATTS_PER_AMP_THREE_PHASE,
    CSNetHomeCalculatedSensor,
    CSNetHomeCompressorSensor,
    CSNetHomeDailySensor,
    CSNetHomeInstallationSensor,
    _heat_use,
    _heat_uses,
    _named_for_its_electricity,
    _power_reading_follower,
)

DEVICE_DATA = {"device_name": "System", "device_id": "global", "room_name": "Controller", "parent_id": "global", "room_id": "global"}


@pytest.fixture(autouse=True)
def mock_integration_frame():
    """Let the coordinator be created outside a config entry setup."""
    with patch("homeassistant.helpers.frame.report_usage"):
        yield


def _coordinator(heating_status, last_update_success=True):
    data = {"data": [{"indoors": [{"heatingStatus": heating_status}]}]}
    return SimpleNamespace(get_installation_devices_data=lambda: data, get_common_data=lambda: {}, last_update_success=last_update_success)


def _description(descriptions, key):
    if isinstance(descriptions, dict):
        return descriptions[key]
    return next(d for d in descriptions if d.key == key)


def _installation_sensor(key, heating_status):
    return CSNetHomeInstallationSensor(_coordinator(heating_status), DEVICE_DATA, {}, _description(INSTALLATION_SENSOR_DESCRIPTIONS, key))


# --------------------------------------------------------------------------
# "No sensor" markers
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "raw_key"),
    [
        ("out_water_temperature_3", "waterOutlet3Temp"),
        ("c2_water_temperature", "waterOutlet2Temp"),
        ("in_water_temperature", "waterInletTemp"),
        ("out_water_temperature", "waterOutletTemp"),
        ("heat_exchanger_water_outlet_temperature", "waterOutletHPTemp"),
        ("set_water_temperature", "waterTempSetting"),
        ("gas_temperature", "gasTemp"),
        ("liquid_temperature", "liquidTemp"),
        ("external_temperature", "outdoorAmbientTemp"),
        ("mean_external_temperature", "outdoorAmbientAverageTemp"),
    ],
)
@pytest.mark.parametrize("marker", [-127, -67])
def test_missing_probe_marker_is_not_shown_as_a_temperature(key, raw_key, marker):
    """-127 and -67 mean the probe is not fitted."""
    assert _installation_sensor(key, {raw_key: marker}).native_value is None


@pytest.mark.parametrize("value", [-20, 0, 43])
def test_real_water_temperatures_are_kept(value):
    """Real readings, including below zero, pass through unchanged."""
    assert _installation_sensor("out_water_temperature_3", {"waterOutlet3Temp": value}).native_value == value


def test_cold_outdoor_temperature_is_kept():
    """A real winter reading is far above the marker."""
    assert _installation_sensor("external_temperature", {"outdoorAmbientTemp": -25}).native_value == -25


def _compressor_sensor(key, heating_status=None, second_cycle=None):
    data = {"data": [{"indoors": [{"heatingStatus": heating_status or {"ouHz": 30}, "secondCycle": second_cycle or {}}]}]}
    coordinator = SimpleNamespace(get_installation_devices_data=lambda: data, get_common_data=lambda: {})
    return CSNetHomeCompressorSensor(coordinator, DEVICE_DATA, {}, _description(COMPRESSOR_SENSOR_DESCRIPTIONS, key))


@pytest.mark.parametrize(
    ("key", "raw_key"),
    [
        ("discharge_temperature", "ouDischargeTemperature"),
        ("evaporator_temperature", "ouEvapTemperature"),
        ("outdoor_ambient_temperature", "ouAmbientTemperature"),
    ],
)
@pytest.mark.parametrize("raw", [129, 189, 128])
def test_outdoor_unit_marker_bytes_are_not_shown(key, raw_key, raw):
    """129, 189 and 128 are -127, -67 and -128 as signed bytes: no probe."""
    assert _compressor_sensor(key, {raw_key: raw}).native_value is None


def test_outdoor_unit_negative_temperature_is_kept():
    """252 is -4 °C, a normal evaporator temperature."""
    assert _compressor_sensor("evaporator_temperature", {"ouEvapTemperature": 252}).native_value == -4


def test_second_cycle_marker_is_not_shown():
    """The second refrigerant cycle reports the same markers."""
    assert _compressor_sensor("secondary_suction_temp", second_cycle={"suctionTemp": 129}).native_value is None


# --------------------------------------------------------------------------
# System status flags
# --------------------------------------------------------------------------


def _flags_sensor(heating_status):
    return CSNetHomeCompressorSensor(_coordinator(heating_status), DEVICE_DATA, {}, _description(COMPRESSOR_SENSOR_DESCRIPTIONS, "system_status_flags"))


def test_status_flags_are_decoded_as_running_components():
    """0x603C: pumps 1-3 and compressor on, both circuits calling for heat."""
    attrs = _flags_sensor({"systemStatus2Flags": 0x603C, "systemConfigBits": 0x0FC3}).extra_state_attributes

    assert attrs["raw_value"] == 0x603C
    assert attrs["hex_value"] == "0x603C"
    assert attrs["water_pump_1"] is True
    assert attrs["water_pump_2"] is True
    assert attrs["water_pump_3"] is True
    assert attrs["compressor_on"] is True
    assert attrs["c1_demand"] is True
    assert attrs["c2_demand"] is True
    assert attrs["boiler_on"] is False
    assert attrs["dhw_heater_on"] is False
    assert attrs["space_heater_on"] is False
    assert attrs["smart_function_input"] is False
    assert attrs["forced_off"] is False
    assert attrs["dhw_recirculation"] is False


@pytest.mark.parametrize(
    ("flags", "name"),
    [
        (0x40, "boiler_on"),
        (0x80, "dhw_heater_on"),
        (0x100, "space_heater_on"),
        (0x200, "smart_function_input"),
        (0x400, "forced_off"),
        (0x800, "dhw_recirculation"),
    ],
)
def test_each_status_flag_bit(flags, name):
    """Each bit lights exactly its own attribute."""
    attrs = _flags_sensor({"systemStatus2Flags": flags, "systemConfigBits": 0}).extra_state_attributes

    lit = [key for key, value in attrs.items() if value is True]
    assert lit == [name]


def test_configuration_attributes_come_from_the_config_bits():
    """Demand bits in the status flags are no longer reported as fan coil mode."""
    # status says both circuits call for heat (0x2000 | 0x4000); config has no fan coil, no cascade
    attrs = _flags_sensor({"systemStatus2Flags": 0x6000, "systemConfigBits": 0x00C0}).extra_state_attributes
    assert attrs["fan_coil_mode"] is False
    assert attrs["cascade_slave"] is False
    assert attrs["c1_thermostat"] is True
    assert attrs["c2_thermostat"] is True

    attrs = _flags_sensor({"systemStatus2Flags": 0, "systemConfigBits": 0x3000}).extra_state_attributes
    assert attrs["fan_coil_mode"] is True
    assert attrs["cascade_slave"] is True
    assert attrs["c1_thermostat"] is False


def test_status_flags_with_missing_fields():
    """Units that do not send the fields report everything off."""
    attrs = _flags_sensor({"systemStatus2Flags": None}).extra_state_attributes

    assert attrs["raw_value"] == 0
    assert attrs["compressor_on"] is False
    assert attrs["fan_coil_mode"] is False


# --------------------------------------------------------------------------
# Heat output
# --------------------------------------------------------------------------


def _thermal_power(heating_status):
    sensor = CSNetHomeCalculatedSensor(_coordinator(heating_status), DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["heating_power"])
    return sensor._get_thermal_power_values(heating_status)[0]


# The exchanger outlet differs on purpose: it is not used in space heating
RUNNING = {"waterFlow": 25, "waterInletTemp": 40, "waterOutletTemp": 43, "waterOutletHPTemp": 50, "ouHz": 31, "defrosting": 0}
EXPECTED_W = 2.5 * 1160 * 3


def test_heat_is_counted_while_the_compressor_runs_in_thermostat_off():
    """Status 5 with the compressor at 31 Hz delivers heat like status 6."""
    assert _thermal_power(RUNNING | {"operationStatus": 5}) == EXPECTED_W
    assert _thermal_power(RUNNING | {"operationStatus": 6}) == EXPECTED_W


@pytest.mark.parametrize("status", [0, 4, 5, 7, 9])
def test_no_heat_when_the_compressor_is_stopped(status):
    """Warm water still circulating after the compressor stops is not production."""
    assert _thermal_power(RUNNING | {"operationStatus": status, "ouHz": 0}) == 0


@pytest.mark.parametrize("status", [5, 6, 8])
def test_no_heat_while_defrosting(status):
    """Defrosting takes heat from the water, in every status."""
    assert _thermal_power(RUNNING | {"operationStatus": status, "defrosting": 1, "waterOutletHPTemp": 45}) == 0


def test_cooling_status_sent_as_text_is_not_counted_as_heating():
    """Some units send the status as text."""
    assert _thermal_power(RUNNING | {"operationStatus": "Cooling Thermostat Off"}) == 0


@pytest.mark.parametrize("probe", ["waterInletTemp", "waterOutletTemp"])
def test_no_heat_from_a_missing_probe(probe):
    """A -127 marker must not turn into hundreds of kilowatts."""
    assert _thermal_power(RUNNING | {"operationStatus": 5, "waterOutletHPTemp": -127, probe: -127}) == 0
    assert _thermal_power(RUNNING | {"operationStatus": 5, "waterInletTemp": -127}) == 0


@pytest.mark.parametrize("status", [5, 6])
def test_space_heating_is_measured_at_the_water_outlet(status):
    """Space heating is measured at the unit's water outlet, as its own heat figures are."""
    assert _thermal_power(RUNNING | {"operationStatus": status}) == EXPECTED_W


def test_cooling_is_measured_at_the_water_outlet():
    """In cooling the water outlet is the cold side: 40 in, 36 out."""
    assert _thermal_power(RUNNING | {"operationStatus": 3, "waterOutletTemp": 36}) == 2.5 * 1160 * 4


def test_hot_water_is_measured_at_the_exchanger_outlet():
    """While the tank is heated the water outlet is not in the flow: the exchanger outlet is used."""
    assert _thermal_power(RUNNING | {"operationStatus": 8, "waterOutletHPTemp": 45}) == 2.5 * 1160 * 5


@pytest.mark.parametrize("bit", [6, 8], ids=["boiler", "backup heater"])
def test_another_heat_source_is_left_out(bit):
    """While a boiler or a backup heater runs, the heat is taken at the exchanger outlet, before them."""
    reading = RUNNING | {"operationStatus": 6, "waterOutletHPTemp": 45, "systemStatus2Flags": (1 << bit) | (1 << 5)}
    assert _thermal_power(reading) == 2.5 * 1160 * 5


def test_other_flags_keep_the_water_outlet():
    """The pumps, the compressor or a circuit's demand do not change the probe."""
    reading = RUNNING | {"operationStatus": 6, "systemStatus2Flags": (1 << 2) | (1 << 5) | (1 << 13) | (1 << 14)}
    assert _thermal_power(reading) == EXPECTED_W


@pytest.mark.parametrize(
    "reading, expected_k",
    [
        ({"operationStatus": 6, "waterOutletTemp": -127}, 10),  # water outlet failed: exchanger outlet
        ({"operationStatus": 6, "waterOutletTemp": None}, 10),  # not sent at all
        ({"operationStatus": 8, "waterOutletHPTemp": -127}, 3),  # tank, no exchanger outlet: water outlet
        ({"operationStatus": 8, "waterOutletHPTemp": None}, 3),
    ],
)
def test_a_missing_outlet_probe_gives_way_to_the_other(reading, expected_k):
    """A probe the unit does not send, or reports failed, gives way to the other outlet."""
    heating_status = {key: value for key, value in (RUNNING | reading).items() if value is not None}
    assert _thermal_power(heating_status) == 2.5 * 1160 * expected_k


# --------------------------------------------------------------------------
# Estimated electricity: auxiliary consumption
# --------------------------------------------------------------------------

STOPPED = {"ouHz": 0, "ouCurrent": 0, "ouDischargePress": 0, "ouSuctionPress": 0, "waterFlow": 0}
# 6 A single phase: the outdoor unit is held between 1320 and 1538 W
SIX_AMPS = {"ouHz": 80, "ouCurrent": 6, "ouDischargePress": 25, "ouSuctionPress": 8, "ouDischargeTemperature": 70, "waterFlow": 20}


def _electric_power(heating_status):
    sensor = CSNetHomeCalculatedSensor(_coordinator(heating_status), DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"])
    return sensor._calculate_complex_power(heating_status)


IDLE_W = STANDBY_POWER_W + CRANKCASE_HEATER_POWER_W


def test_stopped_unit_draws_its_standby():
    """With the compressor and the pump stopped the controllers and the crankcase heater are left."""
    assert _electric_power(STOPPED) == IDLE_W


def _observed(sensor, reading):
    """Feed a new reading, as the coordinator brings it: the model learns once, then the power is asked for."""
    sensor.observe_power_reading(reading)
    return sensor._calculate_complex_power(reading)


def _stopped_readings(sensor, *temperatures):
    """Feed the sensor one reading per discharge temperature and return the last power."""
    power = None
    for temperature in temperatures:
        power = _observed(sensor, STOPPED | {"ouDischargeTemperature": temperature})
    return power


def test_crankcase_heater_counts_while_the_discharge_temperature_climbs():
    """A stopped compressor getting warmer is being heated; getting cooler, it is not."""
    sensor, _ = _calibrated_sensor()
    assert _stopped_readings(sensor, 31, 32) == IDLE_W
    assert _stopped_readings(sensor, 33, 32) == STANDBY_POWER_W


def test_crankcase_heater_state_holds_between_whole_degrees():
    """The temperature moves a degree every few minutes: the state holds meanwhile."""
    sensor, _ = _calibrated_sensor()
    assert _stopped_readings(sensor, 35, 34, 34, 34) == STANDBY_POWER_W
    assert _stopped_readings(sensor, 35, 35, 35) == IDLE_W


def test_crankcase_heater_is_not_counted_right_after_a_run():
    """A compressor that has just stopped is hot and cooling: no heating until it warms again."""
    sensor, _ = _calibrated_sensor()
    _observed(sensor, dict(LOW_MODEL))
    assert _stopped_readings(sensor, 70, 68, 60) == STANDBY_POWER_W
    assert _stopped_readings(sensor, 61) == IDLE_W


def test_crankcase_heater_keeps_its_state_without_a_temperature():
    """A reading with no discharge temperature changes nothing."""
    sensor, _ = _calibrated_sensor()
    assert _stopped_readings(sensor, 33, 32, None) == STANDBY_POWER_W


def test_asking_for_the_power_changes_nothing():
    """Several sensors ask for the power of a reading: only the coordinator's update moves the state."""
    sensor, coordinator = _calibrated_sensor()
    _stopped_readings(sensor, 33, 32)
    for temperature in (40, 50, 60):
        assert sensor._calculate_complex_power(STOPPED | {"ouDischargeTemperature": temperature}) == STANDBY_POWER_W
    assert coordinator.crankcase_heater.heating is False
    for _ in range(3):
        sensor._calculate_complex_power(dict(LOW_MODEL))
    assert coordinator.power_calibration.factors == {}


MINIMUM_SPEED = {"ouHz": 31, "ouCurrent": 2, "ouDischargePress": 18, "ouSuctionPress": 9, "waterFlow": 20, "pumpSpeed": 76, "fanRPM": -1}


def test_reported_current_is_no_floor_at_low_speed():
    """A single-phase unit at its minimum speed reports 2 A for under 400 W: with the pressure model the current only caps."""
    auxiliary = STANDBY_POWER_W + PUMP_MAX_POWER_W * 0.76**2
    assert _electric_power(MINIMUM_SPEED) == round(OUTDOOR_ELECTRONICS_POWER_W + FAN_DEFAULT_POWER_W + 31 * 9 + auxiliary)
    assert _electric_power(MINIMUM_SPEED | {"ouHz": 41}) >= 2 * WATTS_PER_AMP_SINGLE_PHASE


def _three_phase_power(heating_status):
    sensor = CSNetHomeCalculatedSensor(_coordinator(heating_status), DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"])
    sensor.power_supply = POWER_SUPPLY_THREE_PHASE
    return sensor._calculate_complex_power(heating_status)


def test_three_phase_unit_without_a_suction_sensor_keeps_the_current_floor():
    """A three-phase unit with no suction sensor (128) at 32 Hz and 2 A: the current is all there is."""
    reading = MINIMUM_SPEED | {"ouHz": 32, "ouSuctionPress": SUCTION_PRESSURE_MISSING, "ouDischargePress": 30}
    assert _three_phase_power(reading) >= 2 * WATTS_PER_AMP_THREE_PHASE


def test_three_phase_unit_keeps_the_current_floor_at_low_speed():
    """A three-phase unit can under-read its current: it stays a floor below 40 Hz too."""
    assert _three_phase_power(dict(MINIMUM_SPEED)) >= 2 * WATTS_PER_AMP_THREE_PHASE


@pytest.mark.parametrize(
    "reading",
    [
        MINIMUM_SPEED | {"ouSuctionPress": SUCTION_PRESSURE_MISSING},  # no suction sensor
        MINIMUM_SPEED | {"ouSuctionPress": 20},  # crossed pressures
        MINIMUM_SPEED | {"defrosting": 1},  # a defrost
    ],
    ids=["no suction sensor", "crossed pressures", "defrost"],
)
def test_without_the_pressure_model_the_current_is_a_floor_at_low_speed(reading):
    """Without the pressure model a single-phase unit keeps the current's floor below 40 Hz."""
    assert _electric_power(reading) >= 2 * WATTS_PER_AMP_SINGLE_PHASE


def test_no_suction_sensor_teaches_nothing():
    """Without the pressure model there is no model to correct."""
    sensor, coordinator = _calibrated_sensor()
    sensor.observe_power_reading(LOW_MODEL | {"ouSuctionPress": SUCTION_PRESSURE_MISSING})
    assert sensor._power_calibration().factors == {}


def test_the_power_model_learns_once_per_update_of_the_coordinator():
    """The listener learns from every update, even when the coordinator updates its data in place."""
    reading = dict(LOW_MODEL)
    coordinator = _coordinator(reading)
    observer = CSNetHomeCalculatedSensor(coordinator, DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"])
    follow = _power_reading_follower(coordinator, observer)
    follow()
    first = coordinator.power_calibration.factor(41)
    observer._get_heating_status()["ouCurrent"] = 7  # the same dict, changed in place
    follow()
    assert 1.0 < first < coordinator.power_calibration.factor(41)


def test_the_estimated_electricity_moves_at_each_update_without_any_cop_sensor():
    """The listener brings the estimate up to date itself, with the power of the new reading."""
    coordinator = _coordinator(dict(SIX_AMPS))
    coordinator.estimated_energy = MagicMock()
    observer = CSNetHomeCalculatedSensor(coordinator, DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"])
    follow = _power_reading_follower(coordinator, observer)
    follow()
    follow()
    assert coordinator.estimated_energy.async_update.call_count == 2
    _now, watts = coordinator.estimated_energy.async_update.call_args.args
    assert watts == observer._calculate_complex_power(observer._get_heating_status())


def test_the_calculated_heat_moves_at_each_update_with_its_use():
    """The listener counts the heat of each new reading to its use, without the heat sensors."""
    coordinator = _coordinator(COP_RUN | {"operationStatus": 8, "waterOutletHPTemp": 45})
    coordinator.produced_energy = MagicMock()
    observer = CSNetHomeCalculatedSensor(coordinator, DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"])
    _power_reading_follower(coordinator, observer)()
    _now, watts, use = coordinator.produced_energy.async_update.call_args.args
    assert (watts, use) == (2.5 * 1160 * 5, "dhw")


def test_the_power_model_learns_nothing_from_a_failed_update():
    """A failed poll leaves the last reading in place: nothing new to learn from."""
    coordinator = _coordinator(dict(LOW_MODEL))
    coordinator.last_update_success = False
    observer = CSNetHomeCalculatedSensor(coordinator, DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"])
    _power_reading_follower(coordinator, observer)()
    assert observer._power_calibration().factors == {}


def test_crankcase_heater_is_off_while_the_compressor_runs():
    """During a defrost with no fan: electronics, compressor, pump and controllers, no heater."""
    running = {"ouHz": 60, "ouCurrent": 4, "ouDischargePress": 5, "ouSuctionPress": 8, "waterFlow": 20, "pumpSpeed": 100, "fanRPM": 0}
    assert _electric_power(running) == round(OUTDOOR_ELECTRONICS_POWER_W + 60 * 15 + STANDBY_POWER_W + PUMP_MAX_POWER_W)


def test_pump_running_without_the_compressor_is_counted():
    """Water flowing means the pump runs: 10 W plus 65 W by the square of its speed."""
    assert _electric_power(STOPPED | {"waterFlow": 12, "pumpSpeed": 100}) == IDLE_W + PUMP_MAX_POWER_W
    assert _electric_power(STOPPED | {"waterFlow": 12, "pumpSpeed": 50}) == round(IDLE_W + PUMP_MIN_POWER_W + (PUMP_MAX_POWER_W - PUMP_MIN_POWER_W) * 0.25)


def test_pump_speed_alone_does_not_mean_the_pump_runs():
    """The unit keeps reporting the last speed after the pump stops: no flow, no pump power."""
    assert _electric_power(STOPPED | {"pumpSpeed": 75}) == IDLE_W


def test_pump_at_zero_speed_draws_nothing():
    """A pump the unit reports at 0 % is not counted."""
    assert _electric_power(STOPPED | {"waterFlow": 12, "pumpSpeed": 0}) == IDLE_W


def test_pump_and_controllers_are_added_to_the_current_range():
    """The reported current is the outdoor unit's: the pump and the controllers come on top."""
    auxiliary = STANDBY_POWER_W + PUMP_MAX_POWER_W
    power = _electric_power(SIX_AMPS | {"pumpSpeed": 100})
    assert 6 * WATTS_PER_AMP_SINGLE_PHASE + auxiliary <= power <= 6.99 * WATTS_PER_AMP_SINGLE_PHASE + auxiliary + 1


def test_outdoor_fan_follows_its_speed():
    """A faster fan draws more, inside the range of the reported current."""
    free = SIX_AMPS | {"pumpSpeed": 100}  # the model lands inside the 6 A range
    slow = _electric_power(free | {"fanRPM": 300})
    fast = _electric_power(free | {"fanRPM": 900})
    assert fast - slow == round(FAN_MAX_POWER_W * (1 - (300 / 900) ** 3))


def test_fan_without_a_speed_reading_stops_during_a_defrost():
    """No fanRPM: a default while the compressor runs, nothing during a defrost."""
    defrost = {"ouHz": 60, "ouCurrent": 0, "ouDischargePress": 5, "ouSuctionPress": 8, "waterFlow": 20, "pumpSpeed": 100, "fanRPM": -1}
    auxiliary = STANDBY_POWER_W + PUMP_MAX_POWER_W
    assert _electric_power(defrost | {"ouCurrent": 4, "defrosting": 1}) == round(OUTDOOR_ELECTRONICS_POWER_W + 60 * 15 + auxiliary)
    assert _electric_power(defrost | {"ouCurrent": 4, "defrosting": 0}) == round(OUTDOOR_ELECTRONICS_POWER_W + FAN_DEFAULT_POWER_W + 60 * 15 + auxiliary)


def test_defrost_is_taken_from_the_unit_flag():
    """With the flag set the defrost estimate is used, whatever the pressures say."""
    normal = {"ouHz": 60, "ouCurrent": 4, "ouDischargePress": 25, "ouSuctionPress": 8, "waterFlow": 20, "pumpSpeed": 100, "fanRPM": 0}
    auxiliary = STANDBY_POWER_W + PUMP_MAX_POWER_W
    assert _electric_power(normal | {"defrosting": 1}) == round(OUTDOOR_ELECTRONICS_POWER_W + 60 * 15 + auxiliary)
    assert _electric_power(normal | {"defrosting": 0}) != _electric_power(normal | {"defrosting": 1})


# --------------------------------------------------------------------------
# Estimated electricity: self-calibration from the reported current
# --------------------------------------------------------------------------

# 41 Hz and 17 bar apart: the model says 697 W for the compressor, well under the 1320 W of 6 A
LOW_MODEL = {"ouHz": 41, "ouCurrent": 6, "ouDischargePress": 25, "ouSuctionPress": 8, "waterFlow": 20, "pumpSpeed": 100, "fanRPM": 0}


def _calibrated_sensor():
    coordinator = _coordinator({})
    return CSNetHomeCalculatedSensor(coordinator, DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"]), coordinator


def test_model_below_the_current_range_raises_its_factor():
    """Each new reading under the range moves the factor of that frequency band up."""
    sensor, coordinator = _calibrated_sensor()
    sensor.observe_power_reading(dict(LOW_MODEL))
    first = coordinator.power_calibration.factor(41)
    sensor.observe_power_reading(dict(LOW_MODEL))
    assert 1.0 < first < coordinator.power_calibration.factor(41)
    assert coordinator.power_calibration.factor(80) == 1.0  # another band is left alone


def test_model_above_the_current_range_lowers_its_factor():
    """A model over the range of 1 A is brought down."""
    sensor, coordinator = _calibrated_sensor()
    sensor.observe_power_reading(LOW_MODEL | {"ouCurrent": 1})
    assert coordinator.power_calibration.factor(41) < 1.0


def test_model_inside_the_current_range_keeps_its_factor():
    """Nothing to learn while the model agrees with the current."""
    sensor, coordinator = _calibrated_sensor()
    sensor.observe_power_reading(SIX_AMPS | {"pumpSpeed": 100, "fanRPM": 0})
    assert coordinator.power_calibration.factors == {}


def test_calibrated_model_reaches_the_current_range():
    """After enough readings the model lands on the range instead of being cut to it."""
    sensor, coordinator = _calibrated_sensor()
    reading = LOW_MODEL | {"ouCurrent": 3}  # 660 to 878 W: the model's 732 W of outdoor power is inside
    assert sensor._calculate_complex_power(dict(reading)) == round(35 + 41 * 17 + STANDBY_POWER_W + PUMP_MAX_POWER_W)
    reading = LOW_MODEL | {"ouCurrent": 4}  # 880 to 1098 W: the model is under it
    for _ in range(200):
        sensor.observe_power_reading(dict(reading))
    factor = coordinator.power_calibration.factor(41)
    assert 35 + 41 * 17 * factor == pytest.approx(4 * WATTS_PER_AMP_SINGLE_PHASE, abs=1)


def test_factor_stays_within_its_limits():
    """A model far from the range is not stretched without limit."""
    sensor, coordinator = _calibrated_sensor()
    for _ in range(500):
        sensor.observe_power_reading(LOW_MODEL | {"ouCurrent": 12})
    assert coordinator.power_calibration.factor(41) == MAX_FACTOR


def test_defrost_teaches_nothing():
    """The defrost estimate is not the model: the current says nothing about the model then."""
    sensor, coordinator = _calibrated_sensor()
    sensor.observe_power_reading(LOW_MODEL | {"defrosting": 1})
    assert sensor._power_calibration().factors == {}


def test_consumption_sensor_shows_the_learnt_factors():
    """The factors are visible, by frequency band, on the consumption sensor only."""
    sensor, coordinator = _calibrated_sensor()
    sensor.observe_power_reading(dict(LOW_MODEL))
    attributes = sensor.extra_state_attributes["power_calibration"]
    assert list(attributes) == ["40-59 Hz"]
    assert attributes["40-59 Hz"] == round(coordinator.power_calibration.factor(41), 3)
    cop = CSNetHomeCalculatedSensor(coordinator, DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_cop"])
    assert cop.extra_state_attributes is None


async def test_learnt_factors_survive_a_restart():
    """Stored factors are loaded; anything unusable in storage is dropped."""
    calibration = PowerCalibration(MagicMock(), "entry")
    calibration._store = MagicMock()
    calibration._store.async_load = AsyncMock(return_value={"factors": {"1": 1.2, "3": 9.0, "x": 1.1, "9": 1.1}})
    await calibration.async_load()
    assert calibration.factors == {1: 1.2}
    assert calibration.factor(31) == 1.2


def test_learnt_factor_is_saved_once_it_has_moved_enough():
    """Small steps do not write to storage at every poll."""
    hass = MagicMock()
    calibration = PowerCalibration(hass, "entry")
    calibration._async_save = MagicMock()
    calibration.learn(31, 669, 669 * 1.1, 2000)  # 5 % of the way to 1.1: 1.005
    assert hass.async_create_task.call_count == 0
    for _ in range(5):
        calibration.learn(31, 669, 669 * 1.5, 2000)
    assert hass.async_create_task.call_count >= 1


# --------------------------------------------------------------------------
# Instant COP, averaged
# --------------------------------------------------------------------------

COP_RUN = SIX_AMPS | RUNNING | {"operationStatus": 6, "pumpSpeed": 100}


def _cop_sensor(heating_status):
    sensor = CSNetHomeCalculatedSensor(_coordinator(dict(heating_status)), DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_cop"])
    sensor.hass = SimpleNamespace()
    sensor.async_write_ha_state = lambda: None
    return sensor


def _poll(sensor, when, **changes):
    sensor._get_heating_status().update(changes)
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=when):
        sensor._handle_coordinator_update()
        return sensor.native_value


def test_instant_cop_before_any_poll_is_the_single_reading():
    """Nothing to average yet: heat over electricity of the reading at hand."""
    sensor = _cop_sensor(COP_RUN)
    heat = sensor._get_thermal_power_values(COP_RUN)[0]
    assert sensor.native_value == round(heat / sensor._calculate_complex_power(COP_RUN), 2)


def test_instant_cop_is_averaged_over_the_window():
    """Two readings 3 K and 5 K apart give the COP of 4 K, not of the last one."""
    sensor = _cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    low = _poll(sensor, start, waterOutletTemp=43)
    averaged = _poll(sensor, start + timedelta(minutes=1), waterOutletTemp=45)
    electricity = sensor._calculate_complex_power(sensor._get_heating_status())
    assert low == round(2.5 * 1160 * 3 / electricity, 2)
    assert averaged == round(2.5 * 1160 * 4 / electricity, 2)


def test_instant_cop_weighs_each_reading_by_its_time():
    """An extra refresh a few seconds after a poll weighs those seconds, not a whole poll."""
    sensor = _cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _poll(sensor, start, waterOutletTemp=43)
    _poll(sensor, start + timedelta(minutes=1), waterOutletTemp=43)
    averaged = _poll(sensor, start + timedelta(minutes=1, seconds=6), waterOutletTemp=53)
    electricity = sensor._calculate_complex_power(sensor._get_heating_status())
    # 3 K for two minutes, 13 K for six seconds
    assert averaged == round(2.5 * 1160 * (3 * 120 + 13 * 6) / 126 / electricity, 2)


def test_instant_cop_forgets_readings_older_than_the_window():
    """A reading from before the window no longer weighs."""
    sensor = _cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _poll(sensor, start, waterOutletTemp=43)
    later = _poll(sensor, start + INSTANT_COP_WINDOW + timedelta(minutes=1), waterOutletTemp=45)
    electricity = sensor._calculate_complex_power(sensor._get_heating_status())
    assert later == round(2.5 * 1160 * 5 / electricity, 2)


def test_instant_cop_is_zero_while_the_compressor_is_stopped_and_starts_anew():
    """A stop empties the average: the next run does not inherit the last one."""
    sensor = _cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _poll(sensor, start, waterOutletTemp=43)
    assert _poll(sensor, start + timedelta(minutes=1), ouHz=0) == 0.0
    restarted = _poll(sensor, start + timedelta(minutes=2), ouHz=31, waterOutletTemp=45)
    electricity = sensor._calculate_complex_power(sensor._get_heating_status())
    assert restarted == round(2.5 * 1160 * 5 / electricity, 2)


def test_instant_cop_skips_the_poll_a_compressor_starts_up():
    """A few Hz and 0 A, with the water still warm from the last run: no ratio from that poll."""
    sensor = _cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _poll(sensor, start, ouHz=0)
    assert _poll(sensor, start + timedelta(minutes=1), ouHz=1, ouCurrent=0, waterOutletTemp=41) == 0.0
    assert not sensor._cop_samples
    running = _poll(sensor, start + timedelta(minutes=2), ouHz=41, ouCurrent=6, waterOutletTemp=45)
    electricity = sensor._calculate_complex_power(sensor._get_heating_status())
    assert running == round(2.5 * 1160 * 5 / electricity, 2)


def test_instant_cop_keeps_its_average_through_a_poll_without_current():
    """A poll at 0 A in the middle of a run neither counts nor restarts the average."""
    sensor = _cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    first = _poll(sensor, start, waterOutletTemp=43)
    assert _poll(sensor, start + timedelta(minutes=1), ouCurrent=0) == first
    assert len(sensor._cop_samples) == 1


def test_instant_cop_ignores_a_failed_poll():
    """A failed poll brings no new reading into the average."""
    sensor = _cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _poll(sensor, start, waterOutletTemp=43)
    sensor.coordinator.last_update_success = False
    _poll(sensor, start + timedelta(minutes=1), waterOutletTemp=45)
    assert len(sensor._cop_samples) == 1


def _metered_cop_sensor(heating_status):
    """Build an instant COP sensor with a meter whose reading the test sets."""
    sensor = _cop_sensor(heating_status)
    meter = {"state": "10.0"}
    sensor.energy_meter = "sensor.heat_pump_energy"
    sensor.hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda entity_id: SimpleNamespace(state=meter["state"], attributes={"unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR}))
    )
    return sensor, meter


def _metered_poll(sensor, meter, when, reading, **changes):
    meter["state"] = reading
    return _poll(sensor, when, **changes)


def test_instant_cop_uses_the_meter_when_one_is_configured():
    """Heat over what the meter counted between the first and the last reading of the window."""
    sensor, meter = _metered_cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _metered_poll(sensor, meter, start, "10.0", waterOutletTemp=45)
    cop = _metered_poll(sensor, meter, start + timedelta(minutes=5), "10.1", waterOutletTemp=45)
    heat_kwh = 2.5 * 1160 * 5 * (5 / 60) / 1000  # 5 K for 5 minutes
    assert cop == round(heat_kwh / 0.1, 2)


def test_instant_cop_uses_the_estimate_until_the_meter_has_counted_enough():
    """Under 20 Wh in the window the meter's steps would make the COP jump."""
    sensor, meter = _metered_cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _metered_poll(sensor, meter, start, "10.0", waterOutletTemp=45)
    cop = _metered_poll(sensor, meter, start + timedelta(minutes=1), "10.01", waterOutletTemp=45)
    electricity = sensor._calculate_complex_power(sensor._get_heating_status())
    assert cop == round(2.5 * 1160 * 5 / electricity, 2)


@pytest.mark.parametrize("reading", ["unavailable", "9.0"])
def test_instant_cop_uses_the_estimate_when_the_meter_cannot_tell(reading):
    """A meter with no reading, or one that was reset, says nothing about the window."""
    sensor, meter = _metered_cop_sensor(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    _metered_poll(sensor, meter, start, "10.0", waterOutletTemp=45)
    cop = _metered_poll(sensor, meter, start + timedelta(minutes=5), reading, waterOutletTemp=45)
    electricity = sensor._calculate_complex_power(sensor._get_heating_status())
    assert cop == round(2.5 * 1160 * 5 / electricity, 2)


def _meter_hass(states):
    """Build a hass whose states the test sets: entity id -> (state, unit)."""
    return SimpleNamespace(
        states=SimpleNamespace(
            get=lambda entity_id: (
                SimpleNamespace(state=states[entity_id][0], attributes={"unit_of_measurement": states[entity_id][1]}) if entity_id in states else None
            )
        )
    )


def _consumption_sensor(states, power_entity=None):
    sensor = CSNetHomeCalculatedSensor(_coordinator(dict(COP_RUN)), DEVICE_DATA, {}, CALCULATED_SENSOR_DESCRIPTIONS["instant_consumption"])
    sensor.energy_meter = "sensor.heat_pump_energy"
    sensor.energy_meter_power = power_entity
    sensor.hass = _meter_hass(states)
    sensor.async_write_ha_state = lambda: None
    return sensor


@pytest.mark.parametrize(("state", "unit", "expected"), [("812.43", "W", 812.43), ("0.81243", "kW", 812.43)])
def test_instant_consumption_is_the_meter_power_sensor(state, unit, expected):
    """With a power sensor beside the meter, the consumption is what it measures, decimals included."""
    sensor = _consumption_sensor({"sensor.heat_pump_power": (state, unit)}, "sensor.heat_pump_power")
    assert sensor.native_value == expected
    assert sensor.extra_state_attributes["electricity_source"] == "meter"


def test_instant_consumption_takes_the_power_sensor_at_each_update():
    """The meter's power is read when the integration updates, once a poll, with its decimals."""
    states = {"sensor.heat_pump_power": ("400.12", "W")}
    sensor = _consumption_sensor(states, "sensor.heat_pump_power")
    written = []
    sensor.async_write_ha_state = lambda: written.append(sensor.native_value)
    states["sensor.heat_pump_power"] = ("405.38", "W")
    assert written == []  # a change of the power sensor alone writes nothing
    sensor._handle_coordinator_update()
    assert written == [405.38]


def test_instant_consumption_keeps_the_meter_power_through_a_short_gap():
    """A meter restarting does not switch the source to the estimate and back."""
    states = {"sensor.heat_pump_power": ("812.43", "W")}
    sensor = _consumption_sensor(states, "sensor.heat_pump_power")
    start = dt_util.now()
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=start):
        assert sensor.native_value == 812.43
    states["sensor.heat_pump_power"] = ("unavailable", "W")
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=start + timedelta(minutes=1)):
        assert sensor.native_value == 812.43
        assert sensor.extra_state_attributes["electricity_source"] == "meter"
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=start + timedelta(minutes=3)):
        assert sensor.native_value == sensor._calculate_complex_power(sensor._get_heating_status())
        assert sensor.extra_state_attributes["electricity_source"] == "estimate"


def test_instant_consumption_falls_back_to_the_estimate_without_a_meter_reading():
    """A meter power sensor that is unavailable leaves the estimate."""
    sensor = _consumption_sensor({"sensor.heat_pump_power": ("unavailable", "W")}, "sensor.heat_pump_power")
    assert sensor.native_value == sensor._calculate_complex_power(sensor._get_heating_status())
    assert sensor.extra_state_attributes["electricity_source"] == "estimate"


def test_instant_consumption_from_what_the_meter_counted():
    """Without a power sensor: the energy the meter counted over the last minutes."""
    states = {"sensor.heat_pump_energy": ("100.0", UnitOfEnergy.KILO_WATT_HOUR)}
    sensor = _consumption_sensor(states)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    for minutes, reading in ((0, "100.0"), (1, "100.01"), (6, "100.1")):
        states["sensor.heat_pump_energy"] = (reading, UnitOfEnergy.KILO_WATT_HOUR)
        with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=start + timedelta(minutes=minutes)):
            sensor._handle_coordinator_update()
    assert sensor.native_value == 1000  # 0.1 kWh in six minutes


def test_instant_consumption_needs_two_minutes_of_meter_readings():
    """One minute of a meter that counts in steps of a few Wh says too little: the estimate stands in."""
    states = {"sensor.heat_pump_energy": ("100.0", UnitOfEnergy.KILO_WATT_HOUR)}
    sensor = _consumption_sensor(states)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    for minutes, reading in ((0, "100.0"), (1, "100.01")):
        states["sensor.heat_pump_energy"] = (reading, UnitOfEnergy.KILO_WATT_HOUR)
        with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=start + timedelta(minutes=minutes)):
            sensor._handle_coordinator_update()
    assert sensor.native_value == sensor._calculate_complex_power(sensor._get_heating_status())


def _metered_daily_sensor(key, states):
    sensor = _daily_sensor(key)
    sensor.energy_meter = "sensor.heat_pump_energy"
    sensor.hass = _meter_hass(states)
    return sensor


def _daily_poll(sensor, states, when, reading):
    states["sensor.heat_pump_energy"] = (reading, UnitOfEnergy.KILO_WATT_HOUR)
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=when):
        sensor._handle_coordinator_update()


def test_daily_consumption_counts_what_the_meter_counted():
    """The first reading sets the start; then the day adds what the meter counted; after a reset it starts over."""
    states = {}
    sensor = _metered_daily_sensor("daily_consumption", states)
    sensor._get_heating_status().update(STOPPED | {"operationStatus": 4})
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = start - timedelta(minutes=1)
    _daily_poll(sensor, states, start, "50.0")
    first = sensor._state  # the estimate of the minute before the first reading
    assert first < 0.01
    _daily_poll(sensor, states, start + timedelta(minutes=1), "50.3")
    assert sensor._state == pytest.approx(first + 0.3)
    assert sensor.extra_state_attributes == {"electricity_source": "meter"}
    _daily_poll(sensor, states, start + timedelta(minutes=2), "0.1")  # the meter was reset
    after_reset = sensor._state
    assert after_reset - first - 0.3 < 0.01
    _daily_poll(sensor, states, start + timedelta(minutes=3), "0.2")
    assert sensor._state == pytest.approx(after_reset + 0.1)


def test_daily_consumption_estimates_while_the_meter_has_no_reading():
    """No reading: the estimate stands in, also for the interval up to the next reading."""
    states = {}
    sensor = _metered_daily_sensor("daily_consumption", states)
    sensor._get_heating_status().update(STOPPED | {"operationStatus": 4})
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = start - timedelta(minutes=1)
    _daily_poll(sensor, states, start, "50.0")
    _daily_poll(sensor, states, start + timedelta(minutes=1), "unavailable")
    # two minutes of a stopped unit estimated: the one before the first reading, and the unread one
    assert 0 < sensor._state <= 2 * IDLE_W / 60 / 1000 + 1e-9
    assert sensor.extra_state_attributes == {"electricity_source": "estimate"}
    before = sensor._state
    _daily_poll(sensor, states, start + timedelta(minutes=2), "80.0")
    assert sensor._state - before < 0.01  # not the 30 kWh the meter moved while unread


def test_daily_cop_divides_by_what_the_meter_counted():
    """The day's heat over the electricity the meter counted in the same mode."""
    states = {}
    sensor = _metered_daily_sensor("daily_cop_hvac", states)
    sensor._get_heating_status().update(COP_RUN)
    start = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = start - timedelta(minutes=1)
    _daily_poll(sensor, states, start, "50.0")
    first_in, first_out = sensor._energy_in, sensor._energy_out  # the minute before, estimated
    _daily_poll(sensor, states, start + timedelta(minutes=5), "50.1")
    heat_w = sensor._get_thermal_power_values(sensor._get_heating_status())[0]
    assert first_out == pytest.approx(heat_w / 60 / 1000)
    assert sensor._energy_in == pytest.approx(first_in + 0.1)
    assert sensor._energy_out == pytest.approx(heat_w * 6 / 60 / 1000)
    assert sensor.extra_state_attributes["electricity_source"] == "meter"


def test_daily_cop_counts_the_standby_between_compressor_runs():
    """With the compressor stopped the controllers and the crankcase heater still draw: the daily COP counts it."""
    sensor = _daily_sensor("daily_cop_hvac")
    sensor._get_heating_status().update(STOPPED | {"operationStatus": 4})
    now = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = now - timedelta(minutes=1)

    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()

    assert sensor._energy_in == pytest.approx(IDLE_W / 60 / 1000)
    assert sensor._energy_out == 0


@pytest.mark.parametrize("status", [1, 2])
def test_cooling_states_are_not_counted_as_heating(status):
    """In cooling demand/thermostat off a positive delta is not heat output."""
    assert _thermal_power(RUNNING | {"operationStatus": status}) == 0


def test_units_without_compressor_frequency_keep_the_status_rule():
    """No ouHz: thermostat on counts, thermostat off does not, as before."""
    without_hz = {k: v for k, v in RUNNING.items() if k != "ouHz"}

    assert _thermal_power(without_hz | {"operationStatus": 6}) == EXPECTED_W
    assert _thermal_power(without_hz | {"operationStatus": 5}) == 0


# --------------------------------------------------------------------------
# Daily energy
# --------------------------------------------------------------------------

POWERED = RUNNING | {"operationStatus": 6, "ouDischargePress": 20, "ouSuctionPress": 5, "ouDischargeTemperature": 80, "ouCurrent": 5}


def _daily_sensor(key="daily_cop_hvac", last_update_success=True):
    sensor = CSNetHomeDailySensor(_coordinator(dict(POWERED), last_update_success), DEVICE_DATA, {}, DAILY_SENSOR_DESCRIPTIONS[key])
    sensor.hass = SimpleNamespace()
    sensor.async_write_ha_state = lambda: None
    return sensor


async def _restore(sensor, state, saved_at):
    last_state = SimpleNamespace(state=state, last_updated=saved_at)
    with (
        patch.object(CSNetHomeDailySensor, "async_get_last_state", AsyncMock(return_value=last_state)),
        # skip the entity platform part of being added: only the restore is under test
        patch.object(CSNetHomeInstallationSensor, "async_added_to_hass", AsyncMock(), create=True),
    ):
        await sensor.async_added_to_hass()


async def test_daily_total_saved_today_is_restored():
    """A restart during the day keeps the day's total."""
    sensor = _daily_sensor()

    await _restore(sensor, "12.5", dt_util.now())

    assert sensor.native_value == 12.5


async def test_daily_total_saved_yesterday_is_not_restored():
    """A restart across midnight must not bring yesterday's total back."""
    sensor = _daily_sensor()

    await _restore(sensor, "72.21", dt_util.now() - timedelta(days=1))

    assert sensor.native_value == 0


async def _restore_with(sensor, state, saved_at, attributes):
    last_state = SimpleNamespace(state=state, last_updated=saved_at, attributes=attributes)
    with (
        patch.object(CSNetHomeDailySensor, "async_get_last_state", AsyncMock(return_value=last_state)),
        patch.object(CSNetHomeInstallationSensor, "async_added_to_hass", AsyncMock(), create=True),
    ):
        await sensor.async_added_to_hass()


async def test_daily_cop_keeps_its_totals_across_a_restart():
    """The day's COP goes on from the totals before the restart instead of starting over."""
    sensor = _daily_sensor("daily_cop_hvac")
    await _restore_with(sensor, "4.0", dt_util.now(), {"electricity_kwh": 2.0, "heat_kwh": 8.0})
    assert sensor.native_value == 4.0
    assert sensor.extra_state_attributes == {"electricity_kwh": 2.0, "heat_kwh": 8.0, "heat_source": "calculated", "electricity_source": "estimate"}

    # a minute of standby is added to the day's totals, not to new ones
    sensor._get_heating_status().update(STOPPED | {"operationStatus": 4})
    now = dt_util.now()
    sensor._last_update_time = now - timedelta(minutes=1)
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()
    assert 2.0 < sensor._energy_in < 2.01
    assert sensor._energy_out == 8.0
    assert sensor.native_value == round(8.0 / sensor._energy_in, 2)


async def test_daily_cop_totals_from_yesterday_are_not_restored():
    """Yesterday's totals belong to yesterday."""
    sensor = _daily_sensor("daily_cop_dhw")
    await _restore_with(sensor, "4.0", dt_util.now() - timedelta(days=1), {"electricity_kwh": 2.0, "heat_kwh": 8.0})
    assert sensor.extra_state_attributes == {"electricity_kwh": 0.0, "heat_kwh": 0.0, "heat_source": "calculated", "electricity_source": "estimate"}


def test_daily_output_energy_is_gone():
    """The heat produced sensors took its place."""
    assert "daily_heating" not in DAILY_SENSOR_DESCRIPTIONS


def test_failed_poll_adds_no_energy():
    """Without a new reading nothing is accumulated and the clock does not move."""
    sensor = _daily_sensor(last_update_success=False)
    started = dt_util.now() - timedelta(minutes=1)
    sensor._last_update_time = started

    sensor._handle_coordinator_update()

    assert sensor.native_value == 0
    assert sensor._last_update_time == started


def test_gap_after_an_outage_is_capped():
    """One reading stands for a few minutes at most, not for a whole outage."""
    sensor = _daily_sensor()
    now = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = now - timedelta(hours=3)

    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()

    assert sensor._energy_out == pytest.approx(EXPECTED_W * MAX_ENERGY_INTEGRATION_HOURS / 1000)


def test_slow_polling_interval_is_integrated_in_full():
    """With a 10-minute interval each reading stands for the whole 10 minutes."""
    sensor = _daily_sensor()
    sensor.coordinator.update_interval = timedelta(minutes=10)
    now = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = now - timedelta(minutes=10)

    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()

    assert sensor._energy_out == pytest.approx(EXPECTED_W * (10 / 60) / 1000)


def test_failed_poll_across_midnight_resets_once_and_adds_nothing():
    """The day's total is cleared at midnight even when that poll failed."""
    sensor = _daily_sensor(last_update_success=False)
    midnight = dt_util.now().replace(hour=0, minute=0, second=10, microsecond=0)
    sensor._state = 42.0
    sensor._last_update_time = midnight - timedelta(seconds=30)

    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=midnight):
        sensor._handle_coordinator_update()

    assert sensor.native_value == 0


@pytest.mark.parametrize(("status", "key"), [(5, "daily_cop_hvac"), (4, "daily_cop_hvac"), (7, "daily_cop_dhw")])
def test_daily_cop_counts_the_compressor_outside_thermostat_on(status, key):
    """Heat counted in these statuses also reaches the matching daily COP."""
    sensor = _daily_sensor(key)
    heating_status = sensor._get_heating_status()
    heating_status["operationStatus"] = status
    now = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = now - timedelta(minutes=1)

    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()

    assert sensor._energy_out > 0
    assert sensor._energy_in > 0


def test_normal_poll_interval_is_integrated_in_full():
    """A one-minute interval is not affected by the cap."""
    sensor = _daily_sensor()
    now = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = now - timedelta(minutes=1)

    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()

    assert sensor._energy_out == pytest.approx(EXPECTED_W / 60 / 1000)


def _hours_of_heat(hours, kwh_per_hour, use="spaceHeating"):
    """Build CSNet's records of today: each of the first ``hours`` hours with that much heat."""
    today = dt_util.now()
    zero = {"spaceHeating": 0, "spaceCooling": 0, "dhw": 0, "swp": 0}
    return [
        {
            "hourly": [
                {"time": {"year": today.year, "month": today.month, "day": today.day, "hour": h}, "capacity": zero | {use: kwh_per_hour}} for h in range(hours)
            ]
        }
    ]


def _csnet_daily_cop(key, records):
    sensor = _daily_sensor(key)
    sensor.heat_source = "csnet"
    sensor.coordinator.get_server_energy = lambda: records["energy"]
    return sensor


def test_daily_cop_with_csnet_heat_divides_the_recorded_hours():
    """Divide CSNet's heat of the full hours by the electricity of the same hours, not of the hour in progress."""
    records = {"energy": None}
    sensor = _csnet_daily_cop("daily_cop_hvac", records)
    start = dt_util.now().replace(hour=10, minute=0, second=0, microsecond=0)
    sensor._last_update_time = start - timedelta(minutes=1)
    for minute in range(0, 70, 5):
        records["energy"] = _hours_of_heat(11 if minute >= 65 else 10, 1.0)
        with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=start + timedelta(minutes=minute)):
            sensor._handle_coordinator_update()
    # 10:00 and 11:00 were marked; CSNet recorded the hours up to 11:00 by 11:05
    electricity = sensor._electricity_by_hour[11]
    assert 0 < electricity < sensor._energy_in
    assert sensor.native_value == round(11.0 / electricity, 2)
    attributes = sensor.extra_state_attributes
    assert attributes["heat_kwh"] == 11.0
    assert attributes["hours_recorded"] == 11
    assert attributes["heat_source"] == "csnet"
    assert attributes["electricity_today_kwh"] == round(sensor._energy_in, 4)


def test_daily_cop_with_csnet_heat_waits_for_a_matched_hour():
    """Just after a restart no hour start is known yet: the COP stays as it was."""
    records = {"energy": _hours_of_heat(10, 1.0)}
    sensor = _csnet_daily_cop("daily_cop_hvac", records)
    sensor._state = 3.3
    now = dt_util.now().replace(hour=10, minute=30, second=0, microsecond=0)
    sensor._last_update_time = now - timedelta(minutes=1)
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()
    assert sensor.native_value == 3.3
    assert sensor.extra_state_attributes["heat_kwh"] is None


def test_dhw_daily_cop_with_csnet_heat_takes_the_hot_water_heat():
    """The DHW COP divides the hot water heat CSNet recorded, not the space heating."""
    records = {"energy": None}
    sensor = _csnet_daily_cop("daily_cop_dhw", records)
    sensor._get_heating_status().update({"operationStatus": 8})
    start = dt_util.now().replace(hour=10, minute=0, second=0, microsecond=0)
    sensor._last_update_time = start - timedelta(minutes=1)
    records["energy"] = _hours_of_heat(10, 2.0, "dhw") + _hours_of_heat(10, 5.0)
    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=start):
        sensor._handle_coordinator_update()
    assert sensor.extra_state_attributes["heat_kwh"] == 20.0


async def test_daily_cop_restores_the_whole_days_electricity_with_csnet_heat():
    """With CSNet heat the shown electricity is that of the recorded hours; the day's total is restored from its own attribute."""
    sensor = _daily_sensor("daily_cop_hvac")
    sensor.heat_source = "csnet"
    await _restore_with(sensor, "4.0", dt_util.now(), {"electricity_kwh": 2.0, "electricity_today_kwh": 2.5, "heat_kwh": 8.0})
    assert sensor._energy_in == 2.5


@pytest.mark.parametrize(
    ("status", "use"), [(3, "spaceCooling"), (1, "spaceCooling"), (6, "spaceHeating"), (5, "spaceHeating"), (8, "dhw"), (7, "dhw"), (10, "swp")]
)
def test_heat_goes_to_the_use_of_the_operation_status(status, use):
    """The calculated heat is split by use the way CSNet splits it."""
    assert _heat_use(status) == use


def test_calculated_heat_uses_come_from_the_installation_without_csnet_records():
    """Heating always; hot water and pool where the installation has them; cooling where a zone says so."""
    coordinator = SimpleNamespace(get_sensors_data=lambda: [{"zone_id": 1}, {"zone_id": 3}])
    assert _heat_uses(coordinator, None) == ["spaceHeating", "dhw"]
    coordinator = SimpleNamespace(get_sensors_data=lambda: [{"zone_id": 1, "has_cooling": True}, {"zone_id": 4}])
    assert _heat_uses(coordinator, None) == ["spaceHeating", "spaceCooling", "swp"]


def test_calculated_heat_uses_follow_what_csnet_recorded():
    """When CSNet recorded heat, its uses are the ones to split by."""
    coordinator = SimpleNamespace(get_sensors_data=lambda: [])
    energy = _hours_of_heat(2, 1.0, "dhw") + _hours_of_heat(2, 1.0)
    for unit in energy:
        unit["monthly"] = unit["hourly"]
    assert _heat_uses(coordinator, energy) == ["spaceHeating", "dhw"]


# --------------------------------------------------------------------------
# Swimming pool temperature
# --------------------------------------------------------------------------


async def _poll_with_pool(hass, temp_swp):
    pool = {"device_id": 1, "room_id": 5, "zone_id": 4, "parent_id": 6996, "current_temperature": 0}
    api = MagicMock()
    api.logged_in = True
    api.async_get_elements_data = AsyncMock(return_value={"common_data": {"device_status": {}}, "sensors": [pool]})
    api.async_get_installation_devices_data = AsyncMock(return_value={"data": [{"indoors": [{"id": 6996, "heatingStatus": {"tempSWP": temp_swp}}]}]})
    api.async_get_installation_alarms = AsyncMock(return_value=None)
    api.load_translations = AsyncMock()
    api.get_heating_status_from_installation_devices = lambda data, indoor_id=None: extract_heating_status(data, indoor_id)
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=60, entry_id="test", api=api)
    await coordinator._async_update_data()
    return coordinator.get_sensor_data_by_id(1, 5, 4)


async def test_pool_current_temperature_comes_from_the_unit(hass):
    """The pool zone shows tempSWP."""
    assert (await _poll_with_pool(hass, 27))["current_temperature"] == 27


async def test_pool_without_probe_keeps_the_element_value(hass):
    """-127 is not written into the pool zone."""
    assert (await _poll_with_pool(hass, -127))["current_temperature"] == 0


@pytest.mark.parametrize(
    ("descriptions", "key", "meter", "name"),
    [
        (CALCULATED_SENSOR_DESCRIPTIONS, "instant_cop", "sensor.meter", "COP instant (metered)"),
        (DAILY_SENSOR_DESCRIPTIONS, "daily_cop_hvac", "sensor.meter", "COP today heating/cooling (metered)"),
        (DAILY_SENSOR_DESCRIPTIONS, "daily_cop_dhw", None, "COP today hot water (estimated)"),
    ],
)
def test_cops_are_named_like_the_period_cops(descriptions, key, meter, name):
    """COP, then the period, then where the electricity comes from."""
    assert _named_for_its_electricity(descriptions[key], meter).name == name


@pytest.mark.parametrize(
    ("descriptions", "key", "meter", "name"),
    [
        (CALCULATED_SENSOR_DESCRIPTIONS, "instant_consumption", "sensor.meter", "Electricity power (metered)"),
        (DAILY_SENSOR_DESCRIPTIONS, "daily_consumption", None, "Electricity today (estimated)"),
    ],
)
def test_electricity_is_named_by_where_it_comes_from(descriptions, key, meter, name):
    """Electricity, the period, then where it comes from."""
    assert _named_for_its_electricity(descriptions[key], meter).name == name


def test_heat_power_keeps_its_name():
    """The heat power is always calculated: its name says so already."""
    description = CALCULATED_SENSOR_DESCRIPTIONS["heating_power"]
    assert _named_for_its_electricity(description, "sensor.meter") is description
    assert description.name == "Heat power (calculated)"


def test_the_defrost_sensor_is_gone():
    """The Defrost binary sensor is the one: the enum sensor repeated it."""
    from custom_components.csnet_home.sensor import INSTALLATION_SENSOR_DESCRIPTIONS, REMOVED_INSTALLATION_SENSOR_KEYS

    assert "defrost" not in {description.key for description in INSTALLATION_SENSOR_DESCRIPTIONS}
    assert set(REMOVED_INSTALLATION_SENSOR_KEYS) == {"daily_heating", "defrost"}
