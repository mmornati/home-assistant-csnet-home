"""Recalculate the COPs of the past from Home Assistant's own long-term statistics.

The period COPs divide the heat produced by the electricity of the same
period. When their heat was wrong (CSNet recording almost no heat for hours,
as on 22 and 23 November 2026) or their electricity was an estimate, their
history keeps the wrong figures. Home Assistant keeps, for every hour, the
mean of the integration's calculated heat power and what the user's
electricity meter counted. From these this module works out, hour by hour,
what each COP sensor would have shown with the calculated heat and the
metered electricity, shows it, and on the user's confirmation writes it
into the long-term statistics of those sensors (the hourly mean, min and
max). The values it replaces are kept, so they can be put back.

Only hours that already have a statistic are rewritten: putting the backup
back then restores every changed hour exactly. The short-term history (the
recorded states of the last days) cannot be changed: Home Assistant offers
no way to rewrite it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import CONF_ENERGY_METER, DOMAIN
from .server_energy import MIN_ELECTRICITY_FOR_COP_KWH

_LOGGER = logging.getLogger(__name__)

BACKUP_STORAGE_VERSION = 1
# The calculated heat power, whose hourly mean gives the heat of each hour
HEAT_POWER_UNIQUE_ID = f"{DOMAIN}-installation-heating_power"
# The COP sensors whose history is recalculated, and what each one shows
COP_SENSORS = {
    f"{DOMAIN}-metered_cop_today": "today",
    f"{DOMAIN}-metered_cop_yesterday": "yesterday",
    f"{DOMAIN}-metered_cop_month": "month",
    f"{DOMAIN}-metered_cop_last_month": "last_month",
    f"{DOMAIN}-installation-daily_cop_hvac": "today",
}
# How far back the statistics are read: the sensors are younger than this
HISTORY_DAYS = 400
# Days listed one by one in the preview; older ones are summed up
PREVIEW_DAYS = 31
# A recalculated value closer than this to the one in the statistics leaves the hour as it is
CHANGE_THRESHOLD = 0.005


def backup_storage_key(entry_id: str) -> str:
    """Return the storage key of the COP statistics a recalculation replaced."""
    return f"{DOMAIN}.cop_history_backup.{entry_id}"


@dataclass
class Hour:
    """The heat and electricity of one hour, in kWh."""

    start: datetime  # UTC, top of the hour
    heat: float
    electricity: float


@dataclass
class Day:
    """The totals of one local day, and the COP shown for it before and after."""

    day: date
    heat: float
    electricity: float
    hours: int
    before: float | None = None

    @property
    def cop(self) -> float | None:
        """Return the day's COP, or None when too little electricity was counted."""
        return round(self.heat / self.electricity, 2) if self.electricity >= MIN_ELECTRICITY_FOR_COP_KWH else None


@dataclass
class Plan:
    """What a recalculation would write, per COP sensor, and the days it covers."""

    days: list[Day] = field(default_factory=list)
    # statistic_id -> {hour start (UTC): new value}
    values: dict[str, dict[datetime, float]] = field(default_factory=dict)
    # statistic_id -> {hour start (UTC): (mean, min, max) now in the statistics}
    current: dict[str, dict[datetime, tuple]] = field(default_factory=dict)
    heat_entity: str | None = None
    meter_entity: str | None = None

    @property
    def hours_changed(self) -> int:
        """Return how many hourly statistics would be rewritten, over every sensor."""
        return sum(len(values) for values in self.values.values())


def _start(row) -> datetime:
    """Return the start of a statistics row as an aware UTC datetime."""
    start = row["start"]
    if isinstance(start, (int, float)):
        return datetime.fromtimestamp(start, tz=dt_util.UTC)
    return dt_util.as_utc(start)


def hours_from_statistics(heat_rows: list, meter_rows: list) -> list[Hour]:
    """Return the hours that have both the heat power's mean (W) and the meter's change (kWh), oldest first."""
    heat = {_start(row): row.get("mean") for row in heat_rows or ()}
    hours = []
    for row in meter_rows or ():
        start = _start(row)
        watts = heat.get(start)
        change = row.get("change")
        if watts is None or change is None or watts < 0 or change < 0:
            # no heat measured in that hour, or a meter reset
            continue
        hours.append(Hour(start, watts / 1000.0, float(change)))
    return sorted(hours, key=lambda hour: hour.start)


def _ratio(heat: float, electricity: float) -> float | None:
    return round(heat / electricity, 2) if electricity >= MIN_ELECTRICITY_FOR_COP_KWH else None


def _hours_in(first: datetime, last: datetime) -> int:
    """Return how many hours there are from one local midnight to another (23 or 25 on a clock change)."""
    return round((dt_util.as_utc(last) - dt_util.as_utc(first)).total_seconds() / 3600)


def _local_midnight(day: date) -> datetime:
    return dt_util.start_of_local_day(day)


def cop_values(hours: list[Hour]) -> tuple[dict[str, dict[datetime, float]], list[Day]]:
    """Return, for each kind of COP sensor, its value at each hour, and the totals of each day.

    "today" is the day's heat over its electricity up to the end of the hour,
    "month" the same since the first of the month. "yesterday" and
    "last_month" are those of the whole previous day or month, only when it
    has every hour (a day or month with hours missing has no figure).
    """
    by_day: dict[date, list[Hour]] = {}
    for hour in hours:
        by_day.setdefault(dt_util.as_local(hour.start).date(), []).append(hour)
    days = [Day(day, sum(h.heat for h in rows), sum(h.electricity for h in rows), len(rows)) for day, rows in sorted(by_day.items())]
    complete_days = {d.day: d for d in days if d.hours == _hours_in(_local_midnight(d.day), _local_midnight(d.day + timedelta(days=1)))}

    months: dict[tuple[int, int], list[Day]] = {}
    for d in days:
        months.setdefault((d.day.year, d.day.month), []).append(d)

    def month_cop(year: int, month: int) -> float | None:
        rows = months.get((year, month)) or []
        first = date(year, month, 1)
        following = date(year + month // 12, month % 12 + 1, 1)
        expected = _hours_in(_local_midnight(first), _local_midnight(following))
        if sum(d.hours for d in rows) != expected:
            return None
        return _ratio(sum(d.heat for d in rows), sum(d.electricity for d in rows))

    values: dict[str, dict[datetime, float]] = {kind: {} for kind in ("today", "yesterday", "month", "last_month")}
    day_heat = day_electricity = month_heat = month_electricity = 0.0
    current_day = current_month = None
    for hour in hours:
        local_day = dt_util.as_local(hour.start).date()
        if local_day != current_day:
            current_day, day_heat, day_electricity = local_day, 0.0, 0.0
        if (local_day.year, local_day.month) != current_month:
            current_month, month_heat, month_electricity = (local_day.year, local_day.month), 0.0, 0.0
        day_heat += hour.heat
        day_electricity += hour.electricity
        month_heat += hour.heat
        month_electricity += hour.electricity
        if (value := _ratio(day_heat, day_electricity)) is not None:
            values["today"][hour.start] = value
        if (value := _ratio(month_heat, month_electricity)) is not None:
            values["month"][hour.start] = value
        previous_day = complete_days.get(local_day - timedelta(days=1))
        if previous_day is not None and previous_day.cop is not None:
            values["yesterday"][hour.start] = previous_day.cop
        last_month = local_day.replace(day=1) - timedelta(days=1)
        if (value := month_cop(last_month.year, last_month.month)) is not None:
            values["last_month"][hour.start] = value
    return values, days


# The COP of space heating and cooling only: recalculated from the whole heat and
# electricity, so only for an installation without hot water or pool
HVAC_COP_UNIQUE_ID = f"{DOMAIN}-installation-daily_cop_hvac"


def _has_other_uses(entry) -> bool:
    """Return True when the installation heats hot water or a pool, or when that is not known."""
    coordinator = getattr(getattr(entry, "runtime_data", None), "coordinator", None)
    if coordinator is None:
        return True
    try:
        zones = {sensor.get("zone_id") for sensor in coordinator.get_sensors_data() or []}
    except Exception:  # pylint: disable=broad-except
        return True
    return bool(zones & {3, 4})


def _cop_entities(hass: HomeAssistant, entry) -> dict[str, str]:
    """Return the entity id of each COP sensor that exists and can be recalculated, with what it shows."""
    registry = er.async_get(hass)
    found = {}
    for unique_id, kind in COP_SENSORS.items():
        if unique_id == HVAC_COP_UNIQUE_ID and _has_other_uses(entry):
            continue
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id:
            found[entity_id] = kind
    return found


class PlanError(Exception):
    """Why no recalculation can be offered: the reason of the flow's abort."""


async def async_plan(hass: HomeAssistant, entry) -> Plan:
    """Work out what a recalculation would write; raise PlanError when it cannot be done.

    It needs the recorder, the user's electricity meter (the estimate is
    what is being corrected) and the calculated heat power sensor.
    """
    # imported here: only the recalculation needs the recorder
    from homeassistant.components.recorder import get_instance  # pylint: disable=import-outside-toplevel
    from homeassistant.components.recorder.statistics import statistics_during_period  # pylint: disable=import-outside-toplevel

    if "recorder" not in hass.config.components:
        raise PlanError("no_recorder")
    meter = entry.data.get(CONF_ENERGY_METER)
    if not meter:
        raise PlanError("no_energy_meter")
    heat_entity = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, HEAT_POWER_UNIQUE_ID)
    cop_entities = _cop_entities(hass, entry)
    if not heat_entity or not cop_entities:
        raise PlanError("no_cop_sensors")

    now = dt_util.utcnow()
    end = now.replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=HISTORY_DAYS)
    stats = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        start,
        end,
        {heat_entity, meter},
        "hour",
        {"power": "W", "energy": "kWh"},
        {"mean", "change"},
    )
    hours = hours_from_statistics(stats.get(heat_entity) or [], stats.get(meter) or [])
    if not hours:
        raise PlanError("no_statistics")
    current_rows = await get_instance(hass).async_add_executor_job(
        statistics_during_period, hass, hours[0].start, end, set(cop_entities), "hour", None, {"mean", "min", "max"}
    )
    values, days = cop_values(hours)

    plan = Plan(days=days, heat_entity=heat_entity, meter_entity=meter)
    for entity_id, kind in cop_entities.items():
        current = {_start(row): (row.get("mean"), row.get("min"), row.get("max")) for row in current_rows.get(entity_id) or ()}
        new = {
            start: value
            for start, value in values[kind].items()
            if start in current and (current[start][0] is None or abs(current[start][0] - value) >= CHANGE_THRESHOLD)
        }
        if new:
            plan.values[entity_id] = new
            plan.current[entity_id] = {start: current[start] for start in new}
    # the COP each day ended with before: the last hour of "COP today" (metered) that day
    today_entity = next((e for e, k in cop_entities.items() if k == "today" and _unique_id(hass, e) == f"{DOMAIN}-metered_cop_today"), None)
    if today_entity:
        last_of_day: dict[date, float] = {}
        for row in current_rows.get(today_entity) or ():
            if row.get("mean") is not None:
                last_of_day[dt_util.as_local(_start(row)).date()] = round(row["mean"], 2)
        for day in plan.days:
            day.before = last_of_day.get(day.day)
    return plan


def _unique_id(hass: HomeAssistant, entity_id: str) -> str | None:
    entry = er.async_get(hass).async_get(entity_id)
    return entry.unique_id if entry else None


def preview(plan: Plan) -> str:
    """Return the days of the plan as the rows of a Markdown table: the COP each day ended with, and the recalculated one.

    The header of the table is in the translations, in the user's language.
    """
    lines = []
    shown = plan.days[-PREVIEW_DAYS:]
    older = plan.days[:-PREVIEW_DAYS]

    def number(value: float | None) -> str:
        return "–" if value is None else f"{value:.2f}"

    if older:
        heat = sum(d.heat for d in older)
        electricity = sum(d.electricity for d in older)
        lines.append(f"| {older[0].day.isoformat()} – {older[-1].day.isoformat()} | {heat:.0f} | {electricity:.1f} | | {number(_ratio(heat, electricity))} |")
    for day in shown:
        lines.append(f"| {day.day.isoformat()} | {day.heat:.1f} | {day.electricity:.1f} | {number(day.before)} | {number(day.cop)} |")
    return "\n".join(lines)


async def _async_metadata(hass: HomeAssistant, entity_ids: set[str]) -> dict:
    from homeassistant.components.recorder import get_instance  # pylint: disable=import-outside-toplevel
    from homeassistant.components.recorder.statistics import get_metadata  # pylint: disable=import-outside-toplevel

    found = await get_instance(hass).async_add_executor_job(lambda: get_metadata(hass, statistic_ids=entity_ids))
    return {statistic_id: dict(meta) for statistic_id, (_id, meta) in found.items()}


def _import(hass: HomeAssistant, metadata: dict, rows: dict[datetime, tuple]) -> None:
    from homeassistant.components.recorder.statistics import async_import_statistics  # pylint: disable=import-outside-toplevel

    statistics = [{"start": start, "mean": mean, "min": low, "max": high} for start, (mean, low, high) in sorted(rows.items())]
    async_import_statistics(hass, metadata, statistics)


async def async_apply(hass: HomeAssistant, entry, plan: Plan) -> int:
    """Keep the values about to be replaced, then write the recalculated ones; return how many hours were written.

    A value already kept by an earlier recalculation stays: the backup holds
    what the statistics had before the first one.
    """
    store = Store(hass, BACKUP_STORAGE_VERSION, backup_storage_key(entry.entry_id))
    backup = await store.async_load() or {}
    # by unique id: the sensors may be renamed before the values are put back
    kept = backup.setdefault("statistics", {})
    for entity_id, rows in plan.current.items():
        unique_id = _unique_id(hass, entity_id)
        if unique_id is None:
            continue
        entity_rows = kept.setdefault(unique_id, {})
        for start, (mean, low, high) in rows.items():
            entity_rows.setdefault(start.isoformat(), [mean, low, high])
    backup.setdefault("created", dt_util.utcnow().isoformat())
    backup["updated"] = dt_util.utcnow().isoformat()
    await store.async_save(backup)

    metadata = await _async_metadata(hass, set(plan.values))
    written = 0
    for entity_id, values in plan.values.items():
        meta = metadata.get(entity_id)
        if meta is None or _unique_id(hass, entity_id) not in kept:
            # never written without its backup
            continue
        _import(hass, meta, {start: (value, value, value) for start, value in values.items()})
        written += len(values)
    _LOGGER.info("COP history recalculated: %s hourly statistics rewritten from the calculated heat and %s", written, plan.meter_entity)
    return written


async def async_backup_hours(hass: HomeAssistant, entry) -> int:
    """Return how many hourly statistics the backup holds (0 without one)."""
    backup = await Store(hass, BACKUP_STORAGE_VERSION, backup_storage_key(entry.entry_id)).async_load() or {}
    return sum(len(rows) for rows in (backup.get("statistics") or {}).values())


async def async_restore(hass: HomeAssistant, entry) -> int:
    """Put the kept values back into the statistics; return how many hours were written.

    What could not be put back (a sensor removed meanwhile) stays in the
    backup; the backup goes once everything is back.
    """
    store = Store(hass, BACKUP_STORAGE_VERSION, backup_storage_key(entry.entry_id))
    backup = await store.async_load() or {}
    kept = backup.get("statistics") or {}
    registry = er.async_get(hass)
    entity_ids = {unique_id: registry.async_get_entity_id("sensor", DOMAIN, unique_id) for unique_id in kept}
    metadata = await _async_metadata(hass, {entity_id for entity_id in entity_ids.values() if entity_id})
    written = 0
    left = {}
    for unique_id, rows in kept.items():
        meta = metadata.get(entity_ids[unique_id] or "")
        if meta is None:
            left[unique_id] = rows
            continue
        values = {datetime.fromisoformat(start): tuple(row) for start, row in rows.items()}
        _import(hass, meta, values)
        written += len(values)
    if left:
        backup["statistics"] = left
        await store.async_save(backup)
    else:
        await store.async_remove()
    _LOGGER.info("COP history put back as it was: %s hourly statistics", written)
    return written
