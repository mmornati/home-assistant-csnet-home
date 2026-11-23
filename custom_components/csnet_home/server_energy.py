"""Energy the CSNet server has recorded for the unit, and COP from a real electricity meter.

The server keeps, per indoor unit, hourly, daily and monthly records of the
heat produced (``capacity``) and, for units with a pulse meter, of the
electricity taken (``input``), per use. These are the figures of the web
app's consumption page.

A COP needs the electricity too. Most units have no pulse meter, so the user
can name any Home Assistant energy sensor that measures the heat pump; the
COP is then server heat divided by what that sensor counted.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# The uses the server splits energy by, with the name shown for each
USES = {
    "spaceHeating": "space heating",
    "spaceCooling": "space cooling",
    "dhw": "hot water",
    "swp": "pool",
}
HEAT = "capacity"
ELECTRICITY = "input"

METER_STORAGE_VERSION = 1
# A period only counts as measured from its start when the meter was read this soon after it began
PERIOD_START_TOLERANCE = timedelta(minutes=20)
# Below this much electricity a ratio says nothing (the server counts heat in whole kWh)
MIN_ELECTRICITY_FOR_COP_KWH = 0.5
# Longest time one reading of the estimated power may stand for
ESTIMATE_MAX_INTEGRATION_HOURS = 10 / 60
# The running total of the estimate is written at most this often (and on shutdown)
ESTIMATE_SAVE_DELAY_S = 60
# The unit's heat counter (`unitCapacity`, whole kWh) goes back to 0 after 249
# (seen on a Yutaki S 8 HP, 21 November 2026); CSNet's hourly heat is its rise
UNIT_HEAT_COUNTER_WRAP = 250
# A drop from this close to the wrap is the counter starting over; any other drop is a reset
UNIT_HEAT_COUNTER_WRAP_MARGIN = 30
# After a longer gap the counter may have gone round more than once: start again from the reading
UNIT_HEAT_COUNTER_MAX_GAP = timedelta(hours=24)
# Electricity recorded by the server counts as metered from this share of the recorded heat
MIN_ELECTRICITY_SHARE = 0.05
RECENT_MONTHS = 3


def meter_storage_key(entry_id: str) -> str:
    """Return the storage key of the meter readings kept for an entry."""
    return f"{DOMAIN}.energy_meter.{entry_id}"


def estimated_meter_storage_key(entry_id: str) -> str:
    """Return the storage key of the period readings of the estimated electricity."""
    return f"{DOMAIN}.estimated_meter.{entry_id}"


def produced_energy_storage_key(entry_id: str) -> str:
    """Return the storage key of the heat the integration measured, by use and period."""
    return f"{DOMAIN}.produced_energy.{entry_id}"


def unit_heat_storage_key(entry_id: str) -> str:
    """Return the storage key of the heat counted from the unit's own heat counter."""
    return f"{DOMAIN}.unit_heat.{entry_id}"


def estimated_energy_storage_key(entry_id: str) -> str:
    """Return the storage key of the running total of the estimated electricity."""
    return f"{DOMAIN}.estimated_energy.{entry_id}"


def _amount(record, kind: str, use: str | None) -> float:
    """Return the kWh of one record, for one use or for all of them."""
    block = record.get(kind) if isinstance(record, dict) else None
    if not isinstance(block, dict):
        return 0.0
    uses = (use,) if use else tuple(USES)
    total = 0.0
    for key in uses:
        value = block.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
            total += value
    return total


def _matches(record, **parts) -> bool:
    """Return True when the record's time has these parts (year, month, day, hour)."""
    when = record.get("time") if isinstance(record, dict) else None
    return isinstance(when, dict) and all(when.get(name) == value for name, value in parts.items())


def _records(energy, period: str):
    """Yield the records of one period (hourly, daily, monthly) of every indoor unit."""
    if not isinstance(energy, list):
        return
    for unit in energy:
        records = unit.get(period) if isinstance(unit, dict) else None
        if isinstance(records, list):
            yield from records


def _units(energy):
    """Yield the indoor units of the records."""
    if isinstance(energy, list):
        for unit in energy:
            if isinstance(unit, dict):
                yield unit


def energy_on_day(energy, day: date, kind: str, use: str | None = None, before_hour: int | None = None) -> float | None:
    """Return the kWh of one day, or None when the server's records were never read.

    For each indoor unit the hours of the day are added up when it has any,
    so a day in progress is counted up to the last full hour; a unit without
    hours for that day contributes the day's own record. With ``before_hour``
    only the hours before it count (the hours that are complete).
    """
    if not isinstance(energy, list):
        return None
    total = 0.0
    for unit in _units(energy):
        hours = [r for r in unit.get("hourly") or [] if _matches(r, year=day.year, month=day.month, day=day.day)]
        if hours or before_hour is not None:
            total += sum(_amount(r, kind, use) for r in hours if before_hour is None or (r["time"].get("hour") or 0) < before_hour)
        else:
            total += sum(_amount(r, kind, use) for r in unit.get("daily") or [] if _matches(r, year=day.year, month=day.month, day=day.day))
    return total


def hours_complete_on_day(energy, day: date) -> int | None:
    """Return how many hours of the day the server has recorded (the hour after the last record), or None.

    The record stamped with hour h holds the energy of h:00 to h+1:00 and
    appears a few minutes after that hour has ended.
    """
    hours = [
        r["time"].get("hour")
        for r in _records(energy, "hourly")
        if _matches(r, year=day.year, month=day.month, day=day.day) and isinstance(r["time"].get("hour"), int)
    ]
    return max(hours) + 1 if hours else None


def energy_in_month(energy, day: date, kind: str, use: str | None = None) -> float | None:
    """Return the kWh of the month the day is in, or None when the records were never read."""
    if not isinstance(energy, list):
        return None
    months = [r for r in _records(energy, "monthly") if _matches(r, year=day.year, month=day.month)]
    if months:
        return sum(_amount(r, kind, use) for r in months)
    return sum(_amount(r, kind, use) for r in _records(energy, "daily") if _matches(r, year=day.year, month=day.month))


def has_energy(energy, kind: str, use: str | None = None, period: str = "monthly") -> bool:
    """Return True when the server has ever recorded this kind of energy (for this use)."""
    return any(_amount(r, kind, use) > 0 for r in _records(energy, period))


def has_pulse_meter(energy) -> bool:
    """Return True when the recorded electricity is that of a real meter.

    A unit without a pulse meter still gets a stray kWh now and then in the
    server's records. A real meter records electricity in proportion to the
    heat: at least MIN_ELECTRICITY_SHARE of it (a COP of 20 at the very most),
    over the last RECENT_MONTHS months on record.
    """
    months = sorted(
        (r for r in _records(energy, "monthly") if isinstance(r, dict) and isinstance(r.get("time"), dict)),
        key=lambda r: (r["time"].get("year") or 0, r["time"].get("month") or 0),
    )
    # the last months only: a meter fitted recently must not be judged against years without one
    recent = months[-RECENT_MONTHS:]
    heat = sum(_amount(r, HEAT, None) for r in recent)
    electricity = sum(_amount(r, ELECTRICITY, None) for r in recent)
    return electricity > 0 and electricity >= heat * MIN_ELECTRICITY_SHARE


@dataclass(frozen=True, kw_only=True)
class ServerEnergyDescription(SensorEntityDescription):
    """An energy figure read from the server's records."""

    kind: str = HEAT
    span: str = "today"  # today, yesterday or month
    use: str | None = None


def server_energy_descriptions(energy, heat_uses: list[str] | None = None, electricity: str | None = None) -> list[ServerEnergyDescription]:
    """Return the heat and electricity sensors of the unit.

    Each is named by what it is, the period and where it comes from: "Heat
    today (csnet)", "Electricity this month (metered)". With ``heat_uses`` the
    heat is the integration's own measure ("calculated"): its sensors always
    exist, split by those uses; else it is what the server recorded.
    ``electricity`` is "metered" or "estimated" when the electricity is the
    user's meter or the integration's estimate: its sensors always exist.
    Without it, they show what the server recorded, for a unit with a pulse
    meter only. Today's electricity is Electricity today, a sensor of its own.
    """
    common = {
        "device_class": SensorDeviceClass.ENERGY,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
        "suggested_display_precision": 0,
    }
    # TOTAL with a reset time, not TOTAL_INCREASING: the server may correct a
    # figure downwards, which must not be taken for a meter reset
    increasing = {**common, "state_class": SensorStateClass.TOTAL}
    descriptions: list[ServerEnergyDescription] = []
    if heat_uses is not None or has_energy(energy, HEAT):
        heat = "calculated" if heat_uses is not None else "csnet"
        descriptions += [
            ServerEnergyDescription(key="server_heat_today", name=f"Heat today ({heat})", **increasing),
            ServerEnergyDescription(key="server_heat_yesterday", name=f"Heat yesterday ({heat})", span="yesterday", **common),
            ServerEnergyDescription(key="server_heat_month", name=f"Heat this month ({heat})", span="month", **increasing),
        ]
        used = heat_uses if heat_uses is not None else [use for use in USES if has_energy(energy, HEAT, use)]
        if len(used) > 1:
            # with a single use the split would repeat the total
            descriptions += [
                ServerEnergyDescription(key=f"server_heat_today_{use.lower()}", name=f"Heat today {USES[use]} ({heat})", use=use, **increasing) for use in used
            ]
    if electricity is None and has_pulse_meter(energy):
        electricity = "csnet"
    if electricity is not None:
        descriptions += [
            ServerEnergyDescription(
                key="server_electricity_yesterday", name=f"Electricity yesterday ({electricity})", kind=ELECTRICITY, span="yesterday", **common
            ),
            ServerEnergyDescription(
                key="server_electricity_month", name=f"Electricity this month ({electricity})", kind=ELECTRICITY, span="month", **increasing
            ),
        ]
    return descriptions


# Removed: Electricity today, a sensor of its own, is today's electricity
REMOVED_ENERGY_KEYS = ("server_electricity_today",)


def read_span(energy, span: str, kind: str, use: str | None, now: datetime) -> float | None:
    """Return the kWh of today, yesterday or this month."""
    today = now.date()
    if span == "month":
        return energy_in_month(energy, today, kind, use)
    return energy_on_day(energy, today - timedelta(days=1) if span == "yesterday" else today, kind, use)


class CSNetHomeServerEnergySensor(CoordinatorEntity, SensorEntity):
    """Energy the CSNet server has recorded for the unit."""

    _attr_has_entity_name = True
    entity_description: ServerEnergyDescription

    def __init__(
        self,
        coordinator,
        description: ServerEnergyDescription,
        device_info,
        produced: ProducedEnergyCounter | None = None,
        tracker: MeterTracker | None = None,
        counter: EstimatedEnergyCounter | None = None,
    ) -> None:
        """Initialize the sensor.

        With ``produced`` its heat is the integration's own measure. With
        ``tracker`` its electricity is what the user's meter counted, or with
        ``counter`` too the integration's estimate, followed like a meter.
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}"
        self._attr_device_info = device_info
        self._produced = produced if description.kind == HEAT else None
        self._tracker = tracker if description.kind == ELECTRICITY else None
        self._counter = counter if self._tracker is not None else None
        if self._tracker is not None:
            # a meter counts in Wh: its figures are worth more than whole kWh
            self._attr_suggested_display_precision = 2

    async def async_added_to_hass(self) -> None:
        """Load the heat counted, or the meter's period readings, before the first state is written."""
        if self._tracker is not None:
            await self._tracker.async_load()
            self._follow_electricity()
        await super().async_added_to_hass()

    def _follow_electricity(self) -> None:
        """Take the period readings (the estimate is brought up to date before the sensors)."""
        self._tracker.async_update(dt_util.now())

    @callback
    def _handle_coordinator_update(self) -> None:
        """Take the meter's reading first (the heat is counted before the sensors)."""
        if self._tracker is not None:
            self._follow_electricity()
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> float | None:
        """Return the kWh of the sensor's span."""
        description = self.entity_description
        now = dt_util.now()
        if self._produced is not None:
            value = self._produced.energy(description.span, description.use, now)
            return round(value, 3) if value is not None else None
        if self._tracker is not None:
            value = {
                "today": lambda: self._tracker.electricity("day", now),
                "yesterday": lambda: self._tracker.electricity_yesterday(now),
                "month": lambda: self._tracker.electricity("month", now),
            }[description.span]()
            return round(value, 3) if value is not None else None
        return read_span(self.coordinator.get_server_energy(), description.span, description.kind, description.use, now)

    @property
    def extra_state_attributes(self):
        """Say where the heat or the electricity comes from."""
        if self.entity_description.kind == HEAT:
            return {"heat_source": self._produced.source if self._produced is not None else "csnet"}
        if self._tracker is None:
            return {"electricity_source": "csnet"}
        return {"electricity_source": "estimate" if self._counter is not None else "meter"}

    @property
    def last_reset(self) -> datetime | None:
        """Return when the counter started: the start of the day or of the month."""
        if self.entity_description.state_class != SensorStateClass.TOTAL:
            return None
        start = dt_util.start_of_local_day()
        return start.replace(day=1) if self.entity_description.span == "month" else start


def meter_reading_kwh(hass: HomeAssistant, entity_id: str) -> float | None:
    """Return what an energy sensor of Home Assistant counts, in kWh, or None when it has no usable reading."""
    state = hass.states.get(entity_id)
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
        return None
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None
    factor = {
        UnitOfEnergy.KILO_WATT_HOUR: 1.0,
        UnitOfEnergy.WATT_HOUR: 0.001,
        UnitOfEnergy.MEGA_WATT_HOUR: 1000.0,
    }.get(state.attributes.get("unit_of_measurement"))
    if factor is None:
        return None
    return value * factor


def _period_ids(now: datetime) -> dict[str, tuple[str, datetime]]:
    """Return, for the day and the month, the period's id and when it began."""
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "day": (now.strftime("%Y-%m-%d"), start_of_day),
        "month": (now.strftime("%Y-%m"), start_of_day.replace(day=1)),
    }


class MeterTracker:
    """Remember what the electricity meter read at the start of the day and of the month.

    The meter is a running total. To know the electricity of a period, its
    reading at the start of the period is kept (also across restarts). A
    period the meter was not read at the start of is not measured: it gets no
    figure instead of a partial one.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str, entity_id: str, reader=None, storage_key: str | None = None) -> None:
        """Initialize the tracker for one meter entity.

        ``reader`` returns the running total in kWh in place of the entity's
        state: the estimated electricity is followed the same way as a meter.
        """
        self.hass = hass
        self.entity_id = entity_id
        self._reader = reader or (lambda: meter_reading_kwh(hass, entity_id))
        self._store = Store(hass, METER_STORAGE_VERSION, storage_key or meter_storage_key(entry_id))
        self._state: dict = {}
        self._loaded = False

    async def async_load(self) -> None:
        """Load the readings kept before the last restart; another meter's readings are dropped."""
        if self._loaded:
            return
        self._loaded = True
        try:
            stored = await self._store.async_load()
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not load the meter readings: %s", exc)
            return
        if isinstance(stored, dict) and stored.get("entity_id") == self.entity_id and isinstance(stored.get("periods"), dict):
            self._state = stored["periods"]

    @callback
    def async_update(self, now: datetime) -> None:
        """Take the meter's current reading into account."""
        reading = self._reader()
        if reading is None:
            return
        changed = False
        # the reading at the start of each hour of today: what was used up to that hour
        day_id = now.strftime("%Y-%m-%d")
        hours = self._state.get("hours")
        if not isinstance(hours, dict) or hours.get("period") != day_id or not isinstance(hours.get("marks"), dict):
            hours = self._state["hours"] = {"period": day_id, "marks": {}}
            changed = True
        if str(now.hour) not in hours["marks"] and now - now.replace(minute=0, second=0, microsecond=0) <= PERIOD_START_TOLERANCE:
            hours["marks"][str(now.hour)] = reading
            changed = True
        for scope, (period, began) in _period_ids(now).items():
            current = self._state.get(scope)
            read_at_start = now - began <= PERIOD_START_TOLERANCE
            if not isinstance(current, dict) or reading < current.get("start", 0):
                # first reading, or the meter was reset: this period is not measured from its start
                self._state[scope] = {"period": period, "start": reading, "from_start": isinstance(current, dict) is False and read_at_start}
                changed = True
            elif current.get("period") != period:
                # a new period: close the previous one if it was measured from start to end
                self._state[f"last_{scope}"] = {
                    "period": current.get("period"),
                    "energy": reading - current["start"] if current.get("from_start") and read_at_start else None,
                }
                self._state[scope] = {"period": period, "start": reading, "from_start": read_at_start}
                changed = True
        if changed:
            self.hass.async_create_task(self._async_save())

    async def _async_save(self) -> None:
        """Store the readings."""
        try:
            await self._store.async_save({"entity_id": self.entity_id, "periods": self._state})
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not save the meter readings: %s", exc)

    def electricity(self, scope: str, now: datetime) -> float | None:
        """Return the kWh the meter counted since the start of today or of this month, or None when not measured."""
        current = self._state.get(scope)
        period, _began = _period_ids(now)[scope]
        if not isinstance(current, dict) or current.get("period") != period or not current.get("from_start"):
            return None
        reading = self._reader()
        if reading is None or reading < current["start"]:
            return None
        return reading - current["start"]

    def electricity_until_hour(self, now: datetime, hour: int) -> float | None:
        """Return the kWh counted today from midnight to the start of the given hour, or None when not measured.

        The server counts heat by full hours, and an hour's record arrives a
        few minutes after it ended. This is the electricity that goes with
        the heat of the hours the server has recorded.
        """
        day_id = now.strftime("%Y-%m-%d")
        day = self._state.get("day")
        hours = self._state.get("hours")
        if not isinstance(day, dict) or day.get("period") != day_id or not day.get("from_start"):
            return None
        if not isinstance(hours, dict) or hours.get("period") != day_id:
            return None
        reading = (hours.get("marks") or {}).get(str(hour))
        if not isinstance(reading, (int, float)) or reading < day["start"]:
            return None
        return reading - day["start"]

    def _closed(self, scope: str, period: str) -> float | None:
        """Return the kWh of the previous day or month when it was measured from start to end."""
        last = self._state.get(f"last_{scope}")
        if not isinstance(last, dict) or last.get("period") != period:
            return None
        return last.get("energy")

    def electricity_yesterday(self, now: datetime) -> float | None:
        """Return the kWh the meter counted over the whole of yesterday, or None when not measured."""
        return self._closed("day", (now - timedelta(days=1)).strftime("%Y-%m-%d"))

    def electricity_last_month(self, now: datetime) -> float | None:
        """Return the kWh the meter counted over the whole of last month, or None when not measured."""
        return self._closed("month", (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m"))


class EstimatedEnergyCounter:
    """A running total of the estimated electricity, kept across restarts.

    It stands in for a meter where the user has none, so the COP of the day
    and of the month can be worked out the same way: heat the server recorded
    over the electricity of the same period.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str, max_hours: float = ESTIMATE_MAX_INTEGRATION_HOURS) -> None:
        """Initialize; it is fed the estimated power of each new reading."""
        self.hass = hass
        self._max_hours = max_hours
        self._store = Store(hass, METER_STORAGE_VERSION, estimated_energy_storage_key(entry_id))
        self.total_kwh = 0.0
        self._last_time: datetime | None = None
        self._loaded = False

    async def async_load(self) -> None:
        """Load the total kept before the last restart."""
        if self._loaded:
            return
        self._loaded = True
        try:
            stored = await self._store.async_load()
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not load the estimated electricity: %s", exc)
            return
        if isinstance(stored, dict) and isinstance(stored.get("total_kwh"), (int, float)) and stored["total_kwh"] >= 0:
            self.total_kwh = float(stored["total_kwh"])

    def reading_kwh(self) -> float:
        """Return the running total, as a meter would."""
        return self.total_kwh

    @callback
    def async_update(self, now: datetime, watts: float) -> None:
        """Add the estimated power of a new reading for the time since the last one.

        Called once per update of the coordinator, by the listener that also
        lets the power model learn from the reading.
        """
        if self._last_time is not None and watts > 0:
            # after an outage the last reading says nothing about the gap
            hours = min((now - self._last_time).total_seconds() / 3600.0, self._max_hours)
            if hours > 0:
                self.total_kwh += watts * hours / 1000.0
                self._store.async_delay_save(lambda: {"total_kwh": self.total_kwh}, ESTIMATE_SAVE_DELAY_S)
        self._last_time = now


class ProducedEnergyCounter:
    """The heat the integration measures, per use, for today, yesterday, this month and last month.

    It stands in for the heat CSNet records, when the user chooses the
    integration's own measure or when CSNet has recorded no heat for the unit.
    It is kept across restarts. Today and this month count from when the
    integration started counting. Yesterday and last month have a figure once
    the counting had started before they began: the first, partial day or
    month has none. An outage only loses the heat of its own minutes.
    """

    # what the heat sensors say their heat is
    source = "calculated"

    def __init__(self, hass: HomeAssistant, entry_id: str, max_hours: float = ESTIMATE_MAX_INTEGRATION_HOURS, storage_key: str | None = None) -> None:
        """Initialize; it is fed the heat of each new reading."""
        self.hass = hass
        self._max_hours = max_hours
        self._store = Store(hass, METER_STORAGE_VERSION, storage_key or produced_energy_storage_key(entry_id))
        self._periods: dict = {}
        self._last_time: datetime | None = None
        self._loaded = False

    async def async_load(self) -> None:
        """Load the figures kept before the last restart."""
        if self._loaded:
            return
        self._loaded = True
        try:
            stored = await self._store.async_load()
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not load the heat produced: %s", exc)
            return
        if isinstance(stored, dict) and isinstance(stored.get("periods"), dict):
            self._periods = stored["periods"]
            try:
                # the last reading before the restart: the first reading after it stands for a few minutes at most
                self._last_time = datetime.fromisoformat(stored["last_time"]) if stored.get("last_time") else None
            except (TypeError, ValueError):
                self._last_time = None
            self._restore(stored)

    def _restore(self, stored: dict) -> None:
        """Take back what a subclass keeps besides the periods."""

    def _roll(self, now: datetime) -> None:
        """Start a new day or month when one began."""
        for scope, (period, _began) in _period_ids(now).items():
            current = self._periods.get(scope)
            if isinstance(current, dict) and current.get("period") == period:
                continue
            if isinstance(current, dict):
                # the period that ended: complete unless the counting started in the middle of it
                self._periods[f"last_{scope}"] = {**current, "complete": bool(current.get("from_start"))}
            # counted from its start when the counting was already going on before
            self._periods[scope] = {"period": period, "from_start": isinstance(current, dict), "uses": {}}

    @callback
    def async_update(self, now: datetime, watts: float, use: str | None) -> None:
        """Add the heat of a new reading, to its use, for the time since the last one.

        Called once per update of the coordinator, by the listener that also
        lets the power model learn from the reading.
        """
        hours = (now - self._last_time).total_seconds() / 3600.0 if self._last_time is not None else None
        self._roll(now)
        if hours is not None and watts > 0 and use:
            # after an outage the last reading says nothing about the gap
            self._add(watts * min(hours, self._max_hours) / 1000.0, use)
        self._last_time = now
        # saved a minute later at most, and when Home Assistant stops
        self._store.async_delay_save(self._data_to_save, ESTIMATE_SAVE_DELAY_S)

    def _data_to_save(self) -> dict:
        """Return what is kept across restarts."""
        return {"periods": self._periods, "last_time": self._last_time.isoformat() if self._last_time else None}

    def energy(self, span: str, use: str | None, now: datetime) -> float | None:
        """Return the kWh of today, yesterday, this month or last month (of one use, or all), or None when not counted."""
        today = now.date()
        if span in ("today", "month"):
            scope = "day" if span == "today" else "month"
            period = _period_ids(now)[scope][0]
            bucket = self._periods.get(scope)
            if not isinstance(bucket, dict) or bucket.get("period") != period:
                # nothing counted yet in this period
                return 0.0
        else:
            scope = "day" if span == "yesterday" else "month"
            period = (today - timedelta(days=1)).strftime("%Y-%m-%d") if span == "yesterday" else (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
            bucket = self._periods.get(f"last_{scope}")
            if not isinstance(bucket, dict) or bucket.get("period") != period or not bucket.get("complete"):
                return None
        uses = bucket.get("uses") or {}
        return float(sum(uses.values()) if use is None else uses.get(use, 0.0))

    def _add(self, kwh: float, use: str) -> None:
        """Add heat to today and this month."""
        for scope in ("day", "month"):
            uses = self._periods[scope]["uses"]
            uses[use] = uses.get(use, 0.0) + kwh


class UnitHeatCounter(ProducedEnergyCounter):
    """The heat the unit counts itself, read from its heat counter, for today, yesterday, this month and last month.

    The unit reports a running total of the heat it produced in whole kWh
    (``unitCapacity``), which starts over after 249. CSNet's hourly heat is
    the rise of that counter; counting the rise here gives the same figure
    without CSNet's records, also while CSNet fails to record it. The last
    reading is kept across restarts, so the heat of an outage is counted too
    (on the day it ends).
    """

    source = "unit_counter"

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize; it is fed the counter of each new reading."""
        super().__init__(hass, entry_id, storage_key=unit_heat_storage_key(entry_id))
        self._last_reading: int | None = None
        # whether the counter ever rose: a unit whose counter stands still gets no sensors
        self.has_counted = False

    def _restore(self, stored: dict) -> None:
        """Take back the last reading of the counter."""
        reading = stored.get("last_reading")
        self._last_reading = reading if isinstance(reading, int) and not isinstance(reading, bool) else None
        self.has_counted = stored.get("has_counted") is True

    @staticmethod
    def rise(previous: int, reading: int) -> int | None:
        """Return the kWh between two readings of the counter, or None when it was reset."""
        if reading >= previous:
            return reading - previous
        wrap = UNIT_HEAT_COUNTER_WRAP if previous < UNIT_HEAT_COUNTER_WRAP else 256
        if previous >= wrap - UNIT_HEAT_COUNTER_WRAP_MARGIN:
            # the counter started over
            return wrap - previous + reading
        return None

    @callback
    def async_update_reading(self, now: datetime, reading, use: str | None) -> None:
        """Add the rise of the counter since the last reading to the use of the moment."""
        if not isinstance(reading, int) or isinstance(reading, bool) or reading < 0:
            return
        previous = self._last_reading
        gap = now - self._last_time if self._last_time is not None else None
        self._roll(now)
        if previous is not None and gap is not None and timedelta(0) <= gap <= UNIT_HEAT_COUNTER_MAX_GAP:
            kwh = self.rise(previous, reading)
            if kwh is None:
                _LOGGER.debug("The unit's heat counter went from %s to %s: counting again from there", previous, reading)
            elif kwh:
                self._add(float(kwh), use or "spaceHeating")
                self.has_counted = True
        self._last_reading = reading
        self._last_time = now
        self._store.async_delay_save(self._data_to_save, ESTIMATE_SAVE_DELAY_S)

    def _data_to_save(self) -> dict:
        """Return what is kept across restarts, with the last reading."""
        return {**super()._data_to_save(), "last_reading": self._last_reading, "has_counted": self.has_counted}


def unit_heat_descriptions() -> list[ServerEnergyDescription]:
    """Return the heat sensors of the unit's own heat counter."""
    common = {
        "device_class": SensorDeviceClass.ENERGY,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
        "suggested_display_precision": 0,
    }
    increasing = {**common, "state_class": SensorStateClass.TOTAL}
    return [
        ServerEnergyDescription(key="unit_heat_today", name="Heat today (unit counter)", **increasing),
        ServerEnergyDescription(key="unit_heat_yesterday", name="Heat yesterday (unit counter)", span="yesterday", **common),
        ServerEnergyDescription(key="unit_heat_month", name="Heat this month (unit counter)", span="month", **increasing),
    ]


@dataclass(frozen=True, kw_only=True)
class MeteredCopDescription(SensorEntityDescription):
    """A COP from server heat and metered (or estimated) electricity."""

    span: str = "today"


METERED_COP_DESCRIPTIONS = (
    MeteredCopDescription(key="metered_cop_today", name="COP today (metered)"),
    MeteredCopDescription(key="metered_cop_yesterday", name="COP yesterday (metered)", span="yesterday"),
    MeteredCopDescription(key="metered_cop_month", name="COP this month (metered)", span="month"),
    MeteredCopDescription(key="metered_cop_last_month", name="COP last month (metered)", span="last_month"),
)

# The same COPs with the estimated electricity, for an installation without a meter
ESTIMATED_COP_DESCRIPTIONS = (
    MeteredCopDescription(key="estimated_cop_today", name="COP today (estimated)"),
    MeteredCopDescription(key="estimated_cop_yesterday", name="COP yesterday (estimated)", span="yesterday"),
    MeteredCopDescription(key="estimated_cop_month", name="COP this month (estimated)", span="month"),
    MeteredCopDescription(key="estimated_cop_last_month", name="COP last month (estimated)", span="last_month"),
)


def unit_cop_descriptions(electricity: str) -> list[MeteredCopDescription]:
    """Return the COPs with the heat of the unit's own counter, the electricity "metered" or "estimated"."""
    return [
        MeteredCopDescription(key=f"unit_cop_{key}", name=f"COP {label} (unit counter, {electricity})", span=span)
        for key, label, span in (
            ("today", "today", "today"),
            ("yesterday", "yesterday", "yesterday"),
            ("month", "this month", "month"),
            ("last_month", "last month", "last_month"),
        )
    ]


class CSNetHomeMeteredCopSensor(CoordinatorEntity, SensorEntity):
    """Heat produced divided by the electricity of the same period.

    The heat is what the server recorded, or the integration's own measure
    (``produced``). The electricity is what a meter of the user counted, or,
    without one, the integration's estimate (``counter``).
    """

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    entity_description: MeteredCopDescription

    def __init__(
        self,
        coordinator,
        description: MeteredCopDescription,
        device_info,
        tracker: MeterTracker,
        counter: EstimatedEnergyCounter | None = None,
        produced: ProducedEnergyCounter | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}"
        self._attr_device_info = device_info
        self._tracker = tracker
        self._counter = counter
        self._produced = produced

    def _follow(self) -> None:
        """Take the period readings (the heat and the estimate are brought up to date before the sensors)."""
        self._tracker.async_update(dt_util.now())

    async def async_added_to_hass(self) -> None:
        """Load the kept meter readings before the first state is written."""
        await self._tracker.async_load()
        self._follow()
        await super().async_added_to_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Follow the meter at every poll."""
        self._follow()
        super()._handle_coordinator_update()

    def _figures(self) -> tuple[float | None, float | None]:
        """Return (heat, electricity) in kWh for the sensor's span."""
        now = dt_util.now()
        span = self.entity_description.span
        if self._produced is not None:
            # the integration's heat is counted as it is produced: the electricity up to now goes with it
            electricity = {
                "today": lambda: self._tracker.electricity("day", now),
                "yesterday": lambda: self._tracker.electricity_yesterday(now),
                "month": lambda: self._tracker.electricity("month", now),
                "last_month": lambda: self._tracker.electricity_last_month(now),
            }[span]()
            return self._produced.energy(span, None, now), electricity
        energy = self.coordinator.get_server_energy()
        if span == "today":
            # both up to the last hour the server has recorded: it counts heat by the hour
            complete = hours_complete_on_day(energy, now.date())
            if complete is None:
                return None, None
            return energy_on_day(energy, now.date(), HEAT, before_hour=complete), self._tracker.electricity_until_hour(now, complete)
        if span == "yesterday":
            # the last hour of yesterday is delivered a few minutes after midnight: no figure before that
            complete = hours_complete_on_day(energy, now.date() - timedelta(days=1))
            if complete is not None and complete < 24:
                return None, self._tracker.electricity_yesterday(now)
            return read_span(energy, span, HEAT, None, now), self._tracker.electricity_yesterday(now)
        if span == "last_month":
            return energy_in_month(energy, now.date().replace(day=1) - timedelta(days=1), HEAT), self._tracker.electricity_last_month(now)
        return read_span(energy, span, HEAT, None, now), self._tracker.electricity("month", now)

    @property
    def native_value(self) -> float | None:
        """Return the COP, or None while the period is not measured or too little was used."""
        heat, electricity = self._figures()
        if heat is None or electricity is None or electricity < MIN_ELECTRICITY_FOR_COP_KWH:
            return None
        return round(heat / electricity, 2)

    @property
    def extra_state_attributes(self):
        """Return the two figures the COP is made of."""
        heat, electricity = self._figures()
        return {
            "heat_kwh": round(heat, 3) if heat is not None else None,
            "heat_source": self._produced.source if self._produced is not None else "csnet",
            "electricity_kwh": round(electricity, 3) if electricity is not None else None,
            "meter": None if self._counter is not None else self._tracker.entity_id,
            "electricity_source": "estimate" if self._counter is not None else "meter",
        }
