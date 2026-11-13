"""Server energy records, the meter tracker and the metered COP."""

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.util import dt as dt_util

from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.coordinator import SERVER_ENERGY_POLL_SECONDS, CSNetHomeCoordinator
from custom_components.csnet_home.server_energy import (
    ELECTRICITY,
    HEAT,
    METERED_COP_DESCRIPTIONS,
    CSNetHomeMeteredCopSensor,
    CSNetHomeServerEnergySensor,
    MeterTracker,
    energy_in_month,
    energy_on_day,
    has_energy,
    meter_reading_kwh,
    meter_storage_key,
    server_energy_descriptions,
)

ZERO = {"spaceHeating": 0, "spaceCooling": 0, "dhw": 0, "swp": 0}


def rec(heat=0, electricity=0, dhw=0, **when):
    """Build one record of the server."""
    return {"time": when, "input": ZERO | {"spaceHeating": electricity}, "capacity": ZERO | {"spaceHeating": heat, "dhw": dhw}}


# One unit without a pulse meter, as the maintainer's: heat only, a stray kWh of input in a month
ENERGY = [
    {
        "indoorId": 6996,
        "hourly": [rec(5, year=2026, month=11, day=13, hour=h) for h in range(8)] + [rec(4, year=2026, month=11, day=12, hour=h) for h in range(24)],
        "daily": [rec(96, year=2026, month=11, day=12), rec(88, year=2026, month=11, day=11), rec(70, year=2026, month=10, day=31)],
        "monthly": [rec(1200, 2, year=2026, month=11), rec(900, year=2026, month=10)],
    }
]
NOW = datetime(2026, 11, 13, 8, 30, tzinfo=dt_util.UTC)


def test_today_adds_up_the_hours_recorded_so_far():
    """A day in progress is counted up to its last full hour."""
    assert energy_on_day(ENERGY, date(2026, 11, 13), HEAT) == 40
    assert energy_on_day(ENERGY, date(2026, 11, 12), HEAT) == 96
    # a day with no hourly records left falls back to its daily record
    assert energy_on_day(ENERGY, date(2026, 11, 11), HEAT) == 88
    assert energy_on_day(ENERGY, date(2026, 11, 1), HEAT) == 0


def test_month_uses_the_monthly_record_then_the_days():
    """The month's own record wins; without one the days of the month are added."""
    assert energy_in_month(ENERGY, date(2026, 11, 13), HEAT) == 1200
    without_month = [dict(ENERGY[0], monthly=[])]
    assert energy_in_month(without_month, date(2026, 11, 13), HEAT) == 96 + 88


@pytest.mark.parametrize("energy", [None, "text", {}])
def test_no_records_is_unknown_not_zero(energy):
    """Before the first answer the sensors are unknown."""
    assert energy_on_day(energy, date(2026, 11, 13), HEAT) is None
    assert energy_in_month(energy, date(2026, 11, 13), HEAT) is None


def test_odd_records_are_skipped():
    """Missing blocks, text and negative values do not break the sums."""
    energy = [
        {"hourly": [{"time": {"year": 2026, "month": 11, "day": 13, "hour": 1}, "capacity": {"spaceHeating": "x", "dhw": -3}}, "junk", {"time": None}]},
        "junk",
    ]
    assert energy_on_day(energy, date(2026, 11, 13), HEAT) == 0


def test_several_indoor_units_are_added_up():
    """The installation's figure is the sum of its units."""
    two = ENERGY + [{"indoorId": 7000, "hourly": [rec(3, year=2026, month=11, day=13, hour=1)], "daily": [], "monthly": []}]
    assert energy_on_day(two, date(2026, 11, 13), HEAT) == 43


def test_unit_without_a_meter_gets_heat_sensors_only():
    """A stray kWh in a monthly record is not a meter."""
    assert has_energy(ENERGY, ELECTRICITY) is True
    assert has_energy(ENERGY, ELECTRICITY, period="daily") is False
    assert [d.key for d in server_energy_descriptions(ENERGY)] == ["server_heat_today", "server_heat_yesterday", "server_heat_month"]


def test_unit_with_a_meter_and_hot_water_gets_the_split_and_the_electricity():
    """Electricity sensors need days with electricity; the split needs two uses."""
    energy = [{"daily": [rec(50, 12, dhw=8, year=2026, month=11, day=12)], "monthly": [rec(900, 250, dhw=120, year=2026, month=11)], "hourly": []}]
    keys = [d.key for d in server_energy_descriptions(energy)]
    assert keys == [
        "server_heat_today",
        "server_heat_yesterday",
        "server_heat_month",
        "server_heat_today_spaceheating",
        "server_heat_today_dhw",
        "server_electricity_today",
        "server_electricity_yesterday",
        "server_electricity_month",
    ]


@pytest.mark.parametrize("energy", [None, [], [{"hourly": [], "daily": [], "monthly": []}]])
def test_nothing_recorded_gives_no_sensors(energy):
    """No records, no entities."""
    assert server_energy_descriptions(energy) == []


def test_sensor_reads_its_span(monkeypatch):
    """Today, yesterday and this month, through the entity."""
    monkeypatch.setattr(dt_util, "now", lambda: NOW)
    coordinator = SimpleNamespace(get_server_energy=lambda: ENERGY, async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    values = {d.key: CSNetHomeServerEnergySensor(coordinator, d, None).native_value for d in server_energy_descriptions(ENERGY)}
    assert values == {"server_heat_today": 40, "server_heat_yesterday": 96, "server_heat_month": 1200}


async def test_coordinator_reads_the_records_every_15_minutes_and_keeps_them_on_failure(hass, hass_storage, monkeypatch):
    """One request per 15 minutes; a failed one keeps the last records and never fails the poll."""
    clock = [1000.0]
    monkeypatch.setattr("custom_components.csnet_home.coordinator.time.monotonic", lambda: clock[0])
    api = MagicMock(spec=CSNetHomeAPI)
    api.logged_in = True
    api.async_get_elements_data = AsyncMock(side_effect=lambda: {"sensors": [], "common_data": {"name": "Home"}})
    api.async_get_installation_devices_data = AsyncMock(return_value={})
    api.async_get_installation_alarms = AsyncMock(return_value={"data": []})
    api.load_translations = AsyncMock()
    api.async_get_power_data = AsyncMock(return_value=ENERGY)
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    coordinator = CSNetHomeCoordinator(hass, 60, "entry", api=api)

    for _ in range(3):
        await coordinator._async_update_data()
        clock[0] += 60
    assert api.async_get_power_data.await_count == 1
    assert coordinator.get_server_energy() is ENERGY

    clock[0] += SERVER_ENERGY_POLL_SECONDS
    api.async_get_power_data.side_effect = RuntimeError("boom")
    await coordinator._async_update_data()
    api.async_get_power_data.side_effect = None
    api.async_get_power_data.return_value = None
    clock[0] += 60
    await coordinator._async_update_data()
    assert coordinator.get_server_energy() is ENERGY
    assert api.async_get_power_data.await_count == 3


def _set_meter(hass, value, unit="kWh"):
    """Set the state of the user's energy sensor."""
    hass.states.async_set("sensor.any_meter", value, {"unit_of_measurement": unit, "device_class": "energy"})


@pytest.mark.parametrize(
    ("state", "unit", "expected"),
    [
        ("1234.5", "kWh", 1234.5),
        ("1500", "Wh", 1.5),
        ("2", "MWh", 2000.0),
        ("unavailable", "kWh", None),
        ("unknown", "kWh", None),
        ("abc", "kWh", None),
        ("5", "W", None),
        ("5", None, None),
    ],
)
async def test_meter_reading_in_kwh(hass, state, unit, expected):
    """Any energy sensor works: its unit is converted, anything unusable is no reading."""
    _set_meter(hass, state, unit)
    assert meter_reading_kwh(hass, "sensor.any_meter") == expected
    assert meter_reading_kwh(hass, "sensor.missing") is None


def at(day, hour, minute=0, month=11):
    """Return a local time in November 2026."""
    return datetime(2026, month, day, hour, minute, tzinfo=dt_util.UTC)


async def test_a_day_is_measured_only_when_the_meter_was_read_at_its_start(hass, hass_storage):
    """Started in the middle of a day: no figure for it; the next day is measured."""
    tracker = MeterTracker(hass, "entry", "sensor.any_meter")
    await tracker.async_load()

    _set_meter(hass, "100.0")
    tracker.async_update(at(12, 15, 0))
    _set_meter(hass, "110.0")
    assert tracker.electricity("day", at(12, 20, 0)) is None

    # first poll after midnight
    _set_meter(hass, "112.0")
    tracker.async_update(at(13, 0, 1))
    _set_meter(hass, "115.5")
    assert tracker.electricity("day", at(13, 8, 0)) == pytest.approx(3.5)
    # the 12th was not measured from its start: no figure for yesterday
    assert tracker.electricity_yesterday(at(13, 8, 0)) is None

    _set_meter(hass, "130.0")
    tracker.async_update(at(14, 0, 2))
    assert tracker.electricity_yesterday(at(14, 9, 0)) == pytest.approx(18.0)
    await hass.async_block_till_done()
    assert hass_storage[meter_storage_key("entry")]["data"]["entity_id"] == "sensor.any_meter"


async def test_readings_survive_a_restart_and_a_late_start_is_not_trusted(hass, hass_storage):
    """A restart keeps the day's start; a first reading long after midnight does not start a measured day."""
    tracker = MeterTracker(hass, "entry", "sensor.any_meter")
    await tracker.async_load()
    _set_meter(hass, "200.0")
    tracker.async_update(at(13, 0, 1))
    await hass.async_block_till_done()

    restarted = MeterTracker(hass, "entry", "sensor.any_meter")
    await restarted.async_load()
    _set_meter(hass, "206.0")
    restarted.async_update(at(13, 10, 0))
    assert restarted.electricity("day", at(13, 10, 0)) == pytest.approx(6.0)

    # Home Assistant was off over midnight: the 14th starts at 09:00, so neither day is complete
    _set_meter(hass, "230.0")
    restarted.async_update(at(14, 9, 0))
    assert restarted.electricity("day", at(14, 9, 30)) is None
    assert restarted.electricity_yesterday(at(14, 9, 30)) is None


async def test_meter_reset_and_another_meter_start_over(hass, hass_storage):
    """A total that goes down, or a different sensor, cannot be compared with the kept start."""
    tracker = MeterTracker(hass, "entry", "sensor.any_meter")
    await tracker.async_load()
    _set_meter(hass, "300.0")
    tracker.async_update(at(13, 0, 1))
    _set_meter(hass, "2.0")
    tracker.async_update(at(13, 6, 0))
    assert tracker.electricity("day", at(13, 7, 0)) is None
    await hass.async_block_till_done()

    other = MeterTracker(hass, "entry", "sensor.other_meter")
    await other.async_load()
    assert other._state == {}


async def test_metered_cop_is_heat_over_measured_electricity(hass, hass_storage, monkeypatch):
    """Server heat divided by what the meter counted; unknown while the period is not measured."""
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 0, 1))
    coordinator = SimpleNamespace(get_server_energy=lambda: ENERGY, async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    tracker = MeterTracker(hass, "entry", "sensor.any_meter")
    await tracker.async_load()
    sensors = {d.span: CSNetHomeMeteredCopSensor(coordinator, d, None, tracker) for d in METERED_COP_DESCRIPTIONS}

    _set_meter(hass, "500.0")
    tracker.async_update(dt_util.now())
    assert sensors["today"].native_value is None  # nothing used yet

    monkeypatch.setattr(dt_util, "now", lambda: at(13, 8, 30))
    _set_meter(hass, "510.0")
    assert sensors["today"].native_value == 4.0  # 40 kWh of heat for 10 kWh
    assert sensors["today"].extra_state_attributes == {"heat_kwh": 40, "electricity_kwh": 10.0, "meter": "sensor.any_meter"}
    assert sensors["yesterday"].native_value is None  # the 12th was not measured
    assert sensors["month"].native_value is None  # nor November from its first day

    _set_meter(hass, "510.2")
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 8, 31))
    assert sensors["today"].native_value == pytest.approx(3.92)

    _set_meter(hass, "unavailable")
    assert sensors["today"].native_value is None
