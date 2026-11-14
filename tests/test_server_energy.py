"""Server energy records, the meter tracker and the metered COP."""

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.util import dt as dt_util

from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.coordinator import SERVER_ENERGY_POLL_SECONDS, SERVER_ENERGY_RETRY_SECONDS, CSNetHomeCoordinator
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
    has_pulse_meter,
    hours_complete_on_day,
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
    """A stray kWh, in a month or in a day, is not a meter (seen on the maintainer's unit)."""
    assert has_energy(ENERGY, ELECTRICITY) is True
    assert has_pulse_meter(ENERGY) is False
    stray_day = [dict(ENERGY[0], daily=ENERGY[0]["daily"] + [rec(60, 1, year=2026, month=11, day=10)])]
    assert has_pulse_meter(stray_day) is False
    assert "server_electricity_today" not in [d.key for d in server_energy_descriptions(stray_day)]
    assert [d.key for d in server_energy_descriptions(ENERGY)] == ["server_heat_today", "server_heat_yesterday", "server_heat_month"]


def test_unit_with_a_meter_and_hot_water_gets_the_split_and_the_electricity():
    """Electricity sensors need electricity in proportion to the heat; the split needs two uses."""
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
    assert api.async_get_power_data.await_count == 2
    # a failed request is not repeated on every poll, only after the retry delay
    api.async_get_power_data.side_effect = None
    api.async_get_power_data.return_value = None
    for _ in range(3):
        clock[0] += 60
        await coordinator._async_update_data()
    assert api.async_get_power_data.await_count == 2
    clock[0] += SERVER_ENERGY_RETRY_SECONDS
    await coordinator._async_update_data()
    assert api.async_get_power_data.await_count == 3
    assert coordinator.get_server_energy() is ENERGY


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
    """Heat and electricity both up to the last hour the server has recorded; unknown while not measured."""
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 0, 1))
    coordinator = SimpleNamespace(get_server_energy=lambda: ENERGY, async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    tracker = MeterTracker(hass, "entry", "sensor.any_meter")
    await tracker.async_load()
    sensors = {d.span: CSNetHomeMeteredCopSensor(coordinator, d, None, tracker) for d in METERED_COP_DESCRIPTIONS}

    _set_meter(hass, "500.0")
    tracker.async_update(dt_util.now())
    assert sensors["today"].native_value is None  # ENERGY has hours 0 to 7, but 08:00 was not reached yet

    # 08:01: the meter is read at the start of the hour; the eight recorded hours have 40 kWh of heat
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 8, 1))
    _set_meter(hass, "510.0")
    tracker.async_update(dt_util.now())
    assert sensors["today"].native_value == 4.0
    assert sensors["today"].extra_state_attributes == {"heat_kwh": 40, "electricity_kwh": 10.0, "meter": "sensor.any_meter"}

    # 08:55: more electricity was used, but the hour is not recorded yet: the COP does not sag
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 8, 55))
    _set_meter(hass, "511.2")
    tracker.async_update(dt_util.now())
    assert sensors["today"].native_value == 4.0

    # 09:01: a new hour began, but the server has not delivered the 08:00 hour yet: still 4.0, no dip
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 9, 1))
    _set_meter(hass, "512.0")
    tracker.async_update(dt_util.now())
    assert sensors["today"].native_value == 4.0

    assert sensors["yesterday"].native_value is None  # the 12th was not measured
    assert sensors["month"].native_value is None  # nor November from its first day
    assert sensors["last_month"].native_value is None

    _set_meter(hass, "unavailable")
    assert sensors["today"].native_value == 4.0  # the readings it needs were already taken
    assert sensors["month"].native_value is None


async def test_cop_today_is_unknown_when_the_hour_was_not_read_at_its_start(hass, hass_storage, monkeypatch):
    """No reading at 08:00 (Home Assistant was off then): no figure while the server's last hour ends at 08:00."""
    coordinator = SimpleNamespace(get_server_energy=lambda: ENERGY, async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    tracker = MeterTracker(hass, "entry", "sensor.any_meter")
    await tracker.async_load()
    today = CSNetHomeMeteredCopSensor(coordinator, METERED_COP_DESCRIPTIONS[0], None, tracker)

    _set_meter(hass, "500.0")
    tracker.async_update(at(13, 0, 1))
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 8, 40))
    _set_meter(hass, "510.0")
    tracker.async_update(dt_util.now())
    assert today.native_value is None

    # the readings are kept across a restart
    await hass.async_block_till_done()
    restarted = MeterTracker(hass, "entry", "sensor.any_meter")
    await restarted.async_load()
    assert restarted._state["hours"] == {"period": "2026-11-13", "marks": {"0": 500.0}}


def test_hours_recorded_so_far():
    """The hour after the last record of the day, or None without records for it."""
    assert hours_complete_on_day(ENERGY, date(2026, 11, 13)) == 8
    assert hours_complete_on_day(ENERGY, date(2026, 11, 12)) == 24
    assert hours_complete_on_day(ENERGY, date(2026, 11, 1)) is None
    assert hours_complete_on_day(None, date(2026, 11, 13)) is None


async def test_cop_last_month_needs_a_month_measured_from_start_to_end(hass, hass_storage, monkeypatch):
    """October is closed at the first poll of November, if it was measured from its first minutes."""
    coordinator = SimpleNamespace(get_server_energy=lambda: ENERGY, async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    tracker = MeterTracker(hass, "entry", "sensor.any_meter")
    await tracker.async_load()
    last_month = next(CSNetHomeMeteredCopSensor(coordinator, d, None, tracker) for d in METERED_COP_DESCRIPTIONS if d.span == "last_month")

    _set_meter(hass, "1000.0")
    tracker.async_update(at(1, 0, 2, month=10))
    _set_meter(hass, "1300.0")
    tracker.async_update(at(1, 0, 3, month=11))
    monkeypatch.setattr(dt_util, "now", lambda: at(13, 9, 0))
    assert tracker.electricity_last_month(dt_util.now()) == pytest.approx(300.0)
    assert last_month.native_value == 3.0  # 900 kWh of heat in October


async def test_cop_sensors_exist_only_while_a_meter_is_configured(hass, hass_storage):
    """With a meter: three COP sensors. Meter removed: their registry entries are removed too."""
    from homeassistant.helpers import entity_registry as er

    from custom_components.csnet_home.const import DOMAIN
    from custom_components.csnet_home.sensor import _server_energy_sensors

    coordinator = SimpleNamespace(
        get_server_energy=lambda: ENERGY,
        get_installation_devices_data=lambda: {},
        get_common_data=lambda: {},
        async_add_listener=lambda *a, **k: lambda: None,
        last_update_success=True,
    )
    with_meter = SimpleNamespace(entry_id="entry", data={"energy_meter": "sensor.any_meter"})
    keys = [s.entity_description.key for s in _server_energy_sensors(hass, with_meter, coordinator)]
    assert keys[-4:] == ["metered_cop_today", "metered_cop_yesterday", "metered_cop_month", "metered_cop_last_month"]

    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}-metered_cop_today")
    without_meter = SimpleNamespace(entry_id="entry", data={"energy_meter": None})
    keys = [s.entity_description.key for s in _server_energy_sensors(hass, without_meter, coordinator)]
    assert not [key for key in keys if key.startswith("metered_cop")]
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}-metered_cop_today") is None


def test_each_unit_uses_its_hours_or_its_day_record():
    """One unit with hours for the day and one with only the day's record are both counted."""
    two = [
        {"hourly": [rec(5, year=2026, month=11, day=13, hour=h) for h in range(8)], "daily": []},
        {"hourly": [], "daily": [rec(30, year=2026, month=11, day=13)]},
    ]
    assert energy_on_day(two, date(2026, 11, 13), HEAT) == 70
    # up to a given hour only complete hours count, and day records cannot be split
    assert energy_on_day(two, date(2026, 11, 13), HEAT, before_hour=4) == 20


def test_a_meter_fitted_recently_is_recognised():
    """Years of records without electricity do not hide a meter that counts now."""
    old = [rec(1000, year=2025, month=m) for m in range(1, 13)]
    recent = [rec(900, 250, year=2026, month=9), rec(950, 260, year=2026, month=10), rec(1000, 280, year=2026, month=11)]
    assert has_pulse_meter([{"monthly": old + recent}]) is True
    assert has_pulse_meter([{"monthly": old + [rec(900, 1, year=2026, month=11)]}]) is False


def test_heat_counters_carry_a_reset_time_instead_of_being_ever_increasing(monkeypatch):
    """A figure the server corrects downwards must not look like a meter reset to the recorder."""
    from homeassistant.components.sensor import SensorStateClass

    monkeypatch.setattr(dt_util, "now", lambda: NOW)
    coordinator = SimpleNamespace(get_server_energy=lambda: ENERGY, async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    sensors = {d.key: CSNetHomeServerEnergySensor(coordinator, d, None) for d in server_energy_descriptions(ENERGY)}

    assert sensors["server_heat_today"].state_class is SensorStateClass.TOTAL
    assert sensors["server_heat_today"].last_reset == dt_util.start_of_local_day()
    assert sensors["server_heat_month"].last_reset == dt_util.start_of_local_day().replace(day=1)
    assert sensors["server_heat_yesterday"].state_class is None
    assert sensors["server_heat_yesterday"].last_reset is None


async def test_energy_request_never_signs_in_again(hass):
    """A page instead of data fails that request only: no new login, no failed-login count."""
    import aiohttp

    api = CSNetHomeAPI(hass, "user", "pass")
    api.logged_in = True
    api.xsrf_token = "token"
    api.async_login = AsyncMock(return_value=True)
    api._register_login_failure = MagicMock()
    response = MagicMock()
    response.status = 200
    response.url = "https://www.csnetmanager.com/data/power/indoors"
    response.json = AsyncMock(side_effect=aiohttp.ContentTypeError(MagicMock(), ()))
    manager = MagicMock()
    manager.__aenter__ = AsyncMock(return_value=response)
    manager.__aexit__ = AsyncMock(return_value=False)
    api.session = MagicMock()
    api.session.closed = False
    api.session.get = MagicMock(return_value=manager)

    assert await api.async_get_power_data() is None
    assert api.session.get.call_count == 1
    api.async_login.assert_not_awaited()
    api._register_login_failure.assert_not_called()
    assert api.logged_in is True


async def test_energy_sensors_through_home_assistant_and_added_when_data_arrives_late(hass, hass_storage):
    """Real setup: no records at start, records on a later poll; the sensors appear and validate."""
    from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.csnet_home.const import DOMAIN

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass", "energy_meter": "sensor.any_meter"})
    entry.add_to_hass(hass)
    _set_meter(hass, "100.0")
    from unittest.mock import patch

    update = AsyncMock(return_value={"sensors": [], "common_data": {}})
    with (
        patch("custom_components.csnet_home.coordinator.CSNetHomeCoordinator._async_update_data", update),
        patch("custom_components.csnet_home.CSNetHomeAPI.close", AsyncMock()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get("sensor.system_controller_heat_produced_today") is None

        coordinator = entry.runtime_data.coordinator
        coordinator._server_energy = ENERGY
        coordinator.async_set_updated_data({"sensors": [], "common_data": {}})
        await hass.async_block_till_done()

        state = hass.states.get("sensor.system_controller_heat_produced_this_month")
        assert state is not None and float(state.state) == 1200
        assert state.attributes["state_class"] == "total"
        assert state.attributes["last_reset"]
        assert hass.states.get("sensor.system_controller_heat_produced_yesterday") is not None
        assert hass.states.get("sensor.system_controller_cop_today_metered") is not None
        assert hass.states.get("sensor.system_controller_cop_last_month_metered").state == "unknown"

        # further polls add nothing twice
        coordinator.async_set_updated_data({"sensors": [], "common_data": {}})
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
