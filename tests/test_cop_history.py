"""Recalculating the COPs of the past from Home Assistant's statistics."""

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.cop_history import (
    Hour,
    Plan,
    PlanError,
    async_apply,
    async_backup_hours,
    async_plan,
    async_restore,
    cop_values,
    hours_from_statistics,
    preview,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_db_url, enable_custom_integrations):
    """Prepare the recorder's database before Home Assistant starts, as the recorder fixtures need."""
    yield


def _hours(first_day: date, days: int, heat_kw=6.0, electricity_kwh=2.0, skip=()):
    """Return every hour of `days` local days, with the same heat and electricity in each, except the skipped indexes."""
    start = dt_util.as_utc(dt_util.start_of_local_day(first_day))
    end = dt_util.as_utc(dt_util.start_of_local_day(first_day + timedelta(days=days)))
    hours, when, index = [], start, 0
    while when < end:
        if index not in skip:
            hours.append(Hour(when, heat_kw, electricity_kwh))
        when += timedelta(hours=1)
        index += 1
    return hours


def test_hours_need_both_the_heat_and_the_meter():
    """An hour without the heat power's mean or the meter's change is left out; so is a meter reset."""
    start = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    heat = [{"start": start.timestamp(), "mean": 6000.0}, {"start": (start + timedelta(hours=1)).timestamp(), "mean": 3000.0}]
    meter = [
        {"start": start.timestamp(), "change": 2.0},
        {"start": (start + timedelta(hours=1)).timestamp(), "change": -14000.0},
        {"start": (start + timedelta(hours=2)).timestamp(), "change": 1.0},
    ]
    assert hours_from_statistics(heat, meter) == [Hour(start, 6.0, 2.0)]


def test_each_kind_of_cop_at_each_hour():
    """Two whole days at 6 kWh of heat for 2 kWh: every COP is 3, yesterday's from the second day on."""
    first = date(2026, 11, 20)
    hours = _hours(first, 2)
    values, days = cop_values(hours)
    assert [d.cop for d in days] == [3.0, 3.0]
    assert set(values["today"].values()) == {3.0}
    assert len(values["today"]) == len(hours)
    assert set(values["month"].values()) == {3.0}
    second_day = dt_util.as_utc(dt_util.start_of_local_day(first + timedelta(days=1)))
    assert min(values["yesterday"]) == second_day
    assert set(values["yesterday"].values()) == {3.0}
    # last month has no hour at all: no figure
    assert values["last_month"] == {}


def test_today_is_the_ratio_so_far_and_waits_for_enough_electricity():
    """The day's heat over its electricity up to each hour, from half a kWh of electricity on."""
    first = date(2026, 11, 20)
    hours = [Hour(h.start, 1.0, 0.2) for h in _hours(first, 1)]
    hours[3] = Hour(hours[3].start, 5.0, 0.2)
    values, _days = cop_values(hours)
    starts = [h.start for h in hours]
    # 0.2, then 0.4 kWh: too little; the third hour reaches 0.6 kWh
    assert starts[0] not in values["today"] and starts[1] not in values["today"]
    assert values["today"][starts[2]] == 5.0
    assert values["today"][starts[3]] == round(8.0 / 0.8, 2)


def test_a_day_with_hours_missing_is_not_yesterday():
    """Yesterday's COP needs every hour of yesterday."""
    first = date(2026, 11, 20)
    values, days = cop_values(_hours(first, 2, skip=(5,)))
    assert days[0].hours == 23
    assert values["yesterday"] == {}


def test_preview_lists_the_days_and_sums_up_the_older_ones():
    """The last days one per row, before them one row for all the older ones."""
    _values, days = cop_values(_hours(date(2026, 10, 1), 40))
    days[-1].before = 1.04
    rows = preview(Plan(days=days)).splitlines()
    assert len(rows) == 32
    assert rows[0].startswith("| 2026-10-01 – 2026-10-09 |")
    assert rows[-1] == "| 2026-11-09 | 144.0 | 48.0 | 1.04 | 3.00 |"


async def test_no_recalculation_without_a_meter(hass):
    """The estimate is what is being corrected: a meter is needed."""
    hass.config.components.add("recorder")
    entry = MockConfigEntry(domain=DOMAIN, data={})
    with pytest.raises(PlanError, match="no_energy_meter"):
        await async_plan(hass, entry)


def _meta(entity_id, kind):
    from homeassistant.components.recorder.models import StatisticMeanType

    base = {"name": None, "source": "recorder", "statistic_id": entity_id}
    if kind == "power":
        return base | {"has_sum": False, "mean_type": StatisticMeanType.ARITHMETIC, "unit_class": "power", "unit_of_measurement": "W"}
    if kind == "energy":
        return base | {"has_sum": True, "mean_type": StatisticMeanType.NONE, "unit_class": "energy", "unit_of_measurement": "kWh"}
    return base | {"has_sum": False, "mean_type": StatisticMeanType.ARITHMETIC, "unit_class": None, "unit_of_measurement": None}


async def test_recalculate_then_put_back(recorder_mock, hass):
    """Through the recorder: the COPs are written from the heat power and the meter, then put back as they were."""
    from homeassistant.components.recorder.statistics import async_import_statistics, statistics_during_period
    from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done

    registry = er.async_get(hass)
    heat = registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}-installation-heating_power", suggested_object_id="heat_power").entity_id
    cop = registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}-metered_cop_today", suggested_object_id="cop_today").entity_id
    meter = "sensor.heat_pump_energy"

    first = (dt_util.now() - timedelta(days=3)).date()
    hours = _hours(first, 2)
    total = 1000.0
    meter_rows = []
    for h in hours:
        total += h.electricity
        meter_rows.append({"start": h.start, "sum": total, "state": total})
    async_import_statistics(hass, _meta(heat, "power"), [{"start": h.start, "mean": 6000.0, "min": 6000.0, "max": 6000.0} for h in hours])
    # the first hour of the meter has no change before it: the rows start an hour earlier
    async_import_statistics(hass, _meta(meter, "energy"), [{"start": hours[0].start - timedelta(hours=1), "sum": 1000.0, "state": 1000.0}, *meter_rows])
    async_import_statistics(hass, _meta(cop, "cop"), [{"start": h.start, "mean": 1.0, "min": 0.5, "max": 1.5} for h in hours])
    await async_wait_recording_done(hass)

    entry = MockConfigEntry(domain=DOMAIN, data={"energy_meter": meter})
    entry.add_to_hass(hass)
    # an installation without hot water: the heating/cooling COP is recalculated too
    entry.runtime_data = SimpleNamespace(coordinator=SimpleNamespace(get_sensors_data=lambda: [{"zone_id": 1}]))
    plan = await async_plan(hass, entry)
    assert plan.heat_entity == heat
    assert plan.hours_changed == len(hours)
    assert [d.before for d in plan.days] == [1.0, 1.0]
    assert [d.cop for d in plan.days] == [3.0, 3.0]

    assert await async_apply(hass, entry, plan) == len(hours)
    await async_wait_recording_done(hass)

    def read():
        return statistics_during_period(hass, hours[0].start, hours[-1].start + timedelta(hours=1), {cop}, "hour", None, {"mean", "min", "max"})[cop]

    rows = await hass.async_add_executor_job(read)
    assert {(r["mean"], r["min"], r["max"]) for r in rows} == {(3.0, 3.0, 3.0)}
    assert await async_backup_hours(hass, entry) == len(hours)

    # a second recalculation finds nothing to change
    again = await async_plan(hass, entry)
    assert again.hours_changed == 0

    assert await async_restore(hass, entry) == len(hours)
    await async_wait_recording_done(hass)
    rows = await hass.async_add_executor_job(read)
    assert {(r["mean"], r["min"], r["max"]) for r in rows} == {(1.0, 0.5, 1.5)}
    assert await async_backup_hours(hass, entry) == 0


async def _options_menu(hass, entry):
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.MENU
    return result


async def test_options_show_the_recalculation_and_write_it_once_confirmed(hass):
    """The form shows the days; unticked it asks again, ticked it writes and says how many hours."""
    hours = _hours(date(2026, 11, 20), 2)
    _values, days = cop_values(hours)
    plan = Plan(days=days, values={"sensor.cop_today": {hours[0].start: 3.0}}, heat_entity="sensor.heat", meter_entity="sensor.meter")
    entry = MockConfigEntry(domain=DOMAIN, data={"energy_meter": "sensor.meter"})
    result = await _options_menu(hass, entry)
    with patch("custom_components.csnet_home.cop_history.async_plan", return_value=plan):
        result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "recalculate_cop"})
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "recalculate_cop"
    placeholders = result["description_placeholders"]
    assert placeholders["first"] == "2026-11-20" and placeholders["last"] == "2026-11-21"
    assert placeholders["hours"] == "1"
    assert "| 2026-11-21 |" in placeholders["table"]

    result = await hass.config_entries.options.async_configure(result["flow_id"], {"confirm": False})
    assert result["errors"] == {"confirm": "confirm_required"}

    with patch("custom_components.csnet_home.cop_history.async_apply", return_value=1) as apply:
        result = await hass.config_entries.options.async_configure(result["flow_id"], {"confirm": True})
    apply.assert_awaited_once()
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "cop_history_recalculated"
    # nothing was changed in the settings
    assert dict(entry.options) == {}


async def test_options_say_why_no_recalculation(hass):
    """Without a meter the flow stops with the reason."""
    hass.config.components.add("recorder")
    entry = MockConfigEntry(domain=DOMAIN, data={})
    result = await _options_menu(hass, entry)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "recalculate_cop"})
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "no_energy_meter"


async def test_options_offer_to_put_back_after_a_recalculation(hass, hass_storage):
    """With a backup the menu offers to put it back, and does once confirmed."""
    from custom_components.csnet_home.cop_history import backup_storage_key

    entry = MockConfigEntry(domain=DOMAIN, data={})
    key = backup_storage_key(entry.entry_id)
    hass_storage[key] = {
        "version": 1,
        "minor_version": 1,
        "key": key,
        "data": {"statistics": {"sensor.cop_today": {"2026-11-20T10:00:00+00:00": [1.0, 0.5, 1.5]}}},
    }
    result = await _options_menu(hass, entry)
    assert result["menu_options"] == ["heating_curves", "recalculate_cop", "restore_cop"]
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "restore_cop"})
    assert result["description_placeholders"] == {"hours": "1"}
    with patch("custom_components.csnet_home.cop_history.async_restore", return_value=1) as restore:
        result = await hass.config_entries.options.async_configure(result["flow_id"], {"confirm": True})
    restore.assert_awaited_once()
    assert result["reason"] == "cop_history_restored"


def test_the_heating_cop_is_left_alone_with_hot_water_or_unknown_uses(hass):
    """The recalculated COP covers every use: the heating/cooling COP only gets it without hot water or pool."""
    from custom_components.csnet_home.cop_history import _cop_entities

    registry = er.async_get(hass)
    hvac = registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}-installation-daily_cop_hvac").entity_id
    with_dhw = SimpleNamespace(runtime_data=SimpleNamespace(coordinator=SimpleNamespace(get_sensors_data=lambda: [{"zone_id": 1}, {"zone_id": 3}])))
    heating_only = SimpleNamespace(runtime_data=SimpleNamespace(coordinator=SimpleNamespace(get_sensors_data=lambda: [{"zone_id": 1}])))
    assert hvac not in _cop_entities(hass, with_dhw)
    assert hvac not in _cop_entities(hass, SimpleNamespace())
    assert hvac in _cop_entities(hass, heating_only)


async def test_put_back_keeps_what_has_no_sensor_any_more(hass, hass_storage):
    """A sensor removed since the recalculation keeps its values in the backup."""
    from custom_components.csnet_home.cop_history import backup_storage_key

    hass.config.components.add("recorder")
    entry = MockConfigEntry(domain=DOMAIN, data={})
    key = backup_storage_key(entry.entry_id)
    rows = {"2026-11-20T10:00:00+00:00": [1.0, 0.5, 1.5]}
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": {"statistics": {f"{DOMAIN}-metered_cop_today": rows}}}
    with patch("custom_components.csnet_home.cop_history._async_metadata", return_value={}):
        assert await async_restore(hass, entry) == 0
    assert await async_backup_hours(hass, entry) == 1
