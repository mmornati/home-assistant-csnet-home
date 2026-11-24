"""The automatic heat source: CSNet's hours, with the calculated heat for the hours CSNet missed."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from homeassistant.util import dt as dt_util

from custom_components.csnet_home.server_energy import (
    AutoHeatCounter,
    CSNetHomeServerEnergySensor,
    auto_heat_storage_key,
    energy_in_hour,
    server_energy_descriptions,
)

ZERO = {"spaceHeating": 0, "spaceCooling": 0, "dhw": 0, "swp": 0}


def hour(day, h, heat, dhw=0):
    """One hourly record of CSNet for a November 2026 day."""
    return {"time": {"year": 2026, "month": 11, "day": day, "hour": h}, "input": ZERO, "capacity": ZERO | {"spaceHeating": heat, "dhw": dhw}}


def daily(day, heat, month=11):
    """One daily record of CSNet."""
    return {"time": {"year": 2026, "month": month, "day": day}, "input": ZERO, "capacity": ZERO | {"spaceHeating": heat}}


def local(day, h, minute=0, month=11):
    """Return a local time in November 2026."""
    return dt_util.now().replace(year=2026, month=month, day=day, hour=h, minute=minute, second=0, microsecond=0)


class Unit:
    """CSNet's records as the coordinator returns them, changed by the test as time goes."""

    def __init__(self):
        """Start without any record."""
        self.hourly: list = []
        self.daily: list = []

    def records(self):
        """Return the records, as the coordinator does."""
        return [{"indoorId": 1, "hourly": self.hourly, "daily": self.daily, "monthly": []}]


def run(counter, start, end, watts, use="spaceHeating", step=5):
    """Feed the counter a reading every `step` minutes from start to end (included)."""
    when = start
    while when <= end:
        counter.async_update(when, watts, use)
        when += timedelta(minutes=step)


async def _counter(hass, unit):
    counter = AutoHeatCounter(hass, "entry", unit.records)
    await counter.async_load()
    return counter


def test_an_hour_is_found_by_its_date_and_hour():
    """The heat of one hour is what CSNet recorded, or None when no unit recorded it."""
    energy = [{"hourly": [hour(22, 10, 4)]}, {"hourly": [hour(22, 10, 2), hour(22, 11, 0)]}]
    day = local(22, 0).date()
    assert energy_in_hour(energy, day, 10, "capacity") == 6
    assert energy_in_hour(energy, day, 11, "capacity") == 0
    assert energy_in_hour(energy, day, 12, "capacity") is None


async def test_csnet_hours_are_kept_and_missed_hours_calculated(hass, hass_storage):
    """6 kW calculated all morning. CSNet recorded 5 kWh at 8, 0 at 9 (missed), nothing at 10."""
    unit = Unit()
    unit.hourly = [hour(22, 8, 5), hour(22, 9, 0)]
    counter = await _counter(hass, unit)
    run(counter, local(22, 7, 55), local(22, 11, 30), 6000)
    now = local(22, 11, 30)
    # 8h: CSNet's 5; 9h: CSNet's 0 is less than half of 6 -> 6; 10h: no record -> 6;
    # 11h so far: the readings of 11:00 to 11:30, each with the five minutes before it
    assert counter.energy("today", None, now) == pytest.approx(5 + 6 + 6 + 3.5, abs=0.05)
    sources = counter.hour_sources(now)
    assert sources["csnet"] == 1
    # 9h and 10h, and 7h, which had a reading (at 7:55) and no record
    assert sources["calculated"] == 3
    # CSNet has nothing for the hours before, and they were not counted: their heat is not known
    assert sources["unknown"] == 7


async def test_a_quiet_hour_keeps_csnets_zero(hass, hass_storage):
    """Under AUTO_MIN_HOUR_KWH of calculated heat, CSNet's figure stands, even 0."""
    unit = Unit()
    unit.hourly = [hour(22, 3, 0)]
    counter = await _counter(hass, unit)
    run(counter, local(22, 3, 0), local(22, 4, 0), 1000)
    assert counter.energy("today", None, local(22, 4, 0)) == pytest.approx(0.0 + 1000 * 5 / 60 / 1000, abs=0.01)


async def test_today_never_goes_down(hass, hass_storage):
    """A whole kWh of CSNet replacing a little more calculated heat holds the figure until the heat catches up."""
    unit = Unit()
    counter = await _counter(hass, unit)
    run(counter, local(22, 8, 0), local(22, 9, 0), 6000)
    before = counter.energy("today", None, local(22, 9, 0))
    # 8:05 to 8:55 in 8h, 9:00 in 9h
    assert before == pytest.approx(5.5 + 0.5, abs=0.01)
    # CSNet's record of 8h arrives: 5 kWh, under the 5.5 calculated
    unit.hourly = [hour(22, 8, 5)]
    assert counter.energy("today", None, local(22, 9, 1)) == before
    run(counter, local(22, 9, 5), local(22, 9, 30), 6000)
    assert counter.energy("today", None, local(22, 9, 30)) == pytest.approx(5 + 0.5 + 3.0, abs=0.01)


async def test_yesterday_and_the_month_from_kept_hours_and_days(hass, hass_storage):
    """Three days at 6 kW with CSNet missing the afternoons; the month adds CSNet's days before the counting."""
    unit = Unit()
    unit.daily = [daily(1, 50), daily(19, 40)]
    unit.hourly = [hour(d, h, 6) for d in (20, 21, 22) for h in range(12)]
    counter = await _counter(hass, unit)
    run(counter, local(19, 23, 55), local(22, 0, 30), 6000, step=10)
    now = local(22, 0, 30)
    # yesterday (the 21st): 12 hours of CSNet's 6 and 12 calculated hours of 6
    assert counter.energy("yesterday", None, now) == pytest.approx(144, rel=0.01)
    # the 20th's hours are no longer kept: its total was kept when they went
    assert "2026-11-20" in counter._periods["days"]
    assert counter._periods["days"]["2026-11-20"]["spaceHeating"] == pytest.approx(144, rel=0.01)
    # the month: CSNet's 1st and 19th, then the 20th, the 21st and today's half hour
    assert counter.energy("month", None, now) == pytest.approx(50 + 40 + 144 + 144 + 3, rel=0.01)


async def test_yesterday_is_unknown_when_an_hour_is_known_by_nobody(hass, hass_storage):
    """Home Assistant stopped for hours of yesterday and CSNet missed them too: no figure."""
    unit = Unit()
    counter = await _counter(hass, unit)
    run(counter, local(20, 23, 55), local(21, 10, 0), 6000)
    run(counter, local(21, 14, 0), local(22, 0, 10), 6000)
    assert counter.energy("yesterday", None, local(22, 0, 10)) is None


async def test_the_hours_survive_a_restart(hass, hass_storage):
    """What was counted is loaded back."""
    unit = Unit()
    counter = await _counter(hass, unit)
    run(counter, local(22, 8, 0), local(22, 9, 0), 6000)
    hass_storage[auto_heat_storage_key("entry")] = {"version": 1, "minor_version": 1, "key": auto_heat_storage_key("entry"), "data": counter._data_to_save()}
    again = await _counter(hass, unit)
    assert again.energy("today", None, local(22, 9, 0)) == pytest.approx(counter.energy("today", None, local(22, 9, 0)))


async def test_heat_sensor_names_and_hours(hass, hass_storage):
    """The heat sensors say "auto", and today's tells how many hours came from where."""
    names = [d.name for d in server_energy_descriptions(None, ["spaceHeating"], heat_label="auto")]
    assert names == ["Heat today (auto)", "Heat yesterday (auto)", "Heat this month (auto)"]
    unit = Unit()
    now = dt_util.now().replace(minute=30, second=0, microsecond=0)
    if now.hour < 2:
        now = now.replace(hour=3)
    unit.hourly = [hour(now.day, now.hour - 2, 5)] if now.month == 11 else []
    counter = await _counter(hass, unit)
    coordinator = SimpleNamespace(get_server_energy=unit.records, async_add_listener=lambda *a, **k: lambda: None, last_update_success=True)
    description = server_energy_descriptions(None, ["spaceHeating"], heat_label="auto")[0]
    sensor = CSNetHomeServerEnergySensor(coordinator, description, None, counter)
    attributes = sensor.extra_state_attributes
    assert attributes["heat_source"] == "auto"
    assert {"hours_from_csnet", "hours_calculated"} <= set(attributes)


def test_daily_cop_divides_only_the_hours_followed_from_start_to_end():
    """Hours 14 and 17 (in progress) were followed; 15 ended in an outage and 16 began in it: both are left out."""
    from custom_components.csnet_home.sensor import CSNetHomeDailySensor

    asked = []

    def heat_by_hour(now, hours, uses):
        asked.append((sorted(hours), uses))
        return {hour: 5.0 for hour in hours}

    sensor = SimpleNamespace(
        coordinator=SimpleNamespace(produced_energy=SimpleNamespace(heat_by_hour=heat_by_hour)),
        _electricity_by_hour={14: 10.0, 15: 12.0, 17: 15.0},
        _energy_in=16.0,
        _key="daily_cop_hvac",
    )
    heat, electricity = CSNetHomeDailySensor._auto_figures(sensor, local(22, 17, 30))
    assert asked == [([14, 17], ("spaceHeating", "spaceCooling"))]
    assert heat == 10.0
    assert electricity == pytest.approx(2.0 + 1.0)
    # nothing followed yet: no figure
    sensor._electricity_by_hour = {}
    assert CSNetHomeDailySensor._auto_figures(sensor, local(22, 17, 30)) == (None, None)


async def test_a_use_csnet_missed_is_calculated(hass, hass_storage):
    """The hot water CSNet missed in an hour whose heating it kept is the calculated one."""
    unit = Unit()
    unit.hourly = [hour(22, 8, 3, dhw=0)]
    counter = await _counter(hass, unit)
    run(counter, local(22, 8, 5), local(22, 8, 30), 4000, use="spaceHeating")
    run(counter, local(22, 8, 35), local(22, 9, 0), 4000, use="dhw")
    now = local(22, 9, 0)
    # 8h: heating from CSNet (3), hot water calculated (4 kW for 25 minutes, 8:35 to 8:55)
    assert counter.energy("today", "spaceHeating", now) == pytest.approx(3.0)
    assert counter.energy("today", "dhw", now) == pytest.approx(4 * 25 / 60 + 4 * 5 / 60, abs=0.01)


async def test_a_day_waits_for_csnets_records_before_it_is_kept(hass, hass_storage):
    """Right after a start CSNet's records are not read yet: the older hours are kept until they are."""
    unit = Unit()
    unit.hourly = [hour(20, h, 6) for h in range(24)]
    records = {"energy": None}
    counter = AutoHeatCounter(hass, "entry", lambda: records["energy"])
    await counter.async_load()
    run(counter, local(20, 23, 0), local(20, 23, 30), 6000)
    run(counter, local(22, 0, 10), local(22, 0, 20), 6000)
    assert "2026-11-20" in counter._periods["hours"]
    records["energy"] = unit.records()
    run(counter, local(22, 0, 30), local(22, 0, 30), 6000)
    assert "2026-11-20" not in counter._periods["hours"]
    # every hour is CSNet's, 23h too: its 6 kWh are more than the 3 measured in half an hour
    assert counter._periods["days"]["2026-11-20"]["spaceHeating"] == pytest.approx(24 * 6)


async def test_a_running_total_in_an_hourly_record_is_left_out(hass, hass_storage):
    """The oldest hour CSNet keeps once held 23121 kWh for a day of 80: the day's record counts, not that hour."""
    unit = Unit()
    unit.hourly = [hour(8, 23, 23121)]
    unit.daily = [daily(8, 80), daily(9, 70)]
    counter = await _counter(hass, unit)
    assert counter.energy("month", None, local(10, 0, 30)) == pytest.approx(150)


async def test_a_large_correction_is_shown_even_downwards(hass, hass_storage):
    """A figure that was far too high (a bad record since dropped) does not stay for the rest of the month."""
    unit = Unit()
    unit.daily = [daily(8, 23121)]
    counter = await _counter(hass, unit)
    assert counter.energy("month", None, local(10, 0, 30)) == pytest.approx(23121)
    unit.daily = [daily(8, 80)]
    assert counter.energy("month", None, local(10, 0, 31)) == pytest.approx(80)
