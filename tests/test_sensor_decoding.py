"""Tests for how raw CSNet values are decoded into sensor states."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.util import dt as dt_util

from custom_components.csnet_home.coordinator import CSNetHomeCoordinator
from custom_components.csnet_home.helpers import extract_heating_status
from custom_components.csnet_home.sensor import (
    CALCULATED_SENSOR_DESCRIPTIONS,
    COMPRESSOR_SENSOR_DESCRIPTIONS,
    DAILY_SENSOR_DESCRIPTIONS,
    INSTALLATION_SENSOR_DESCRIPTIONS,
    MAX_ENERGY_INTEGRATION_HOURS,
    CSNetHomeCalculatedSensor,
    CSNetHomeCompressorSensor,
    CSNetHomeDailySensor,
    CSNetHomeInstallationSensor,
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


RUNNING = {"waterFlow": 25, "waterInletTemp": 40, "waterOutletTemp": 43, "ouHz": 31, "defrosting": 0}
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
    assert _thermal_power(RUNNING | {"operationStatus": 5, probe: -127}) == 0


def test_hot_water_falls_back_to_the_circuit_outlet_probe():
    """Status 8 uses the exchanger outlet, or the normal outlet when that probe is missing."""
    assert _thermal_power(RUNNING | {"operationStatus": 8, "waterOutletHPTemp": 45}) == 2.5 * 1160 * 5
    assert _thermal_power(RUNNING | {"operationStatus": 8, "waterOutletHPTemp": -127}) == EXPECTED_W


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


def _daily_sensor(key="daily_heating", last_update_success=True):
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

    assert sensor.native_value == round(EXPECTED_W * MAX_ENERGY_INTEGRATION_HOURS / 1000, 2)


def test_slow_polling_interval_is_integrated_in_full():
    """With a 10-minute interval each reading stands for the whole 10 minutes."""
    sensor = _daily_sensor()
    sensor.coordinator.update_interval = timedelta(minutes=10)
    now = dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0)
    sensor._last_update_time = now - timedelta(minutes=10)

    with patch("custom_components.csnet_home.sensor.dt_util.now", return_value=now):
        sensor._handle_coordinator_update()

    assert sensor.native_value == round(EXPECTED_W * (10 / 60) / 1000, 2)


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

    assert sensor.native_value == round(EXPECTED_W / 60 / 1000, 2)


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
    hass.data["csnet_home"] = {"test": {"api": api}}
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=60, entry_id="test")
    await coordinator._async_update_data()
    return coordinator.get_sensor_data_by_id(1, 5, 4)


async def test_pool_current_temperature_comes_from_the_unit(hass):
    """The pool zone shows tempSWP."""
    assert (await _poll_with_pool(hass, 27))["current_temperature"] == 27


async def test_pool_without_probe_keeps_the_element_value(hass):
    """-127 is not written into the pool zone."""
    assert (await _poll_with_pool(hass, -127))["current_temperature"] == 0
