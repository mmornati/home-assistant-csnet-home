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
# Electricity recorded by the server counts as metered from this share of the recorded heat
MIN_ELECTRICITY_SHARE = 0.05


def meter_storage_key(entry_id: str) -> str:
    """Return the storage key of the meter readings kept for an entry."""
    return f"{DOMAIN}.energy_meter.{entry_id}"


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


def energy_on_day(energy, day: date, kind: str, use: str | None = None) -> float | None:
    """Return the kWh of one day, or None when the server's records were never read.

    The hours of the day are added up when there are any, so a day in
    progress is counted up to the last full hour; otherwise the day's own
    record is used.
    """
    if not isinstance(energy, list):
        return None
    hours = [r for r in _records(energy, "hourly") if _matches(r, year=day.year, month=day.month, day=day.day)]
    if hours:
        return sum(_amount(r, kind, use) for r in hours)
    return sum(_amount(r, kind, use) for r in _records(energy, "daily") if _matches(r, year=day.year, month=day.month, day=day.day))


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
    heat: at least MIN_ELECTRICITY_SHARE of it (a COP of 20 at the very most).
    """
    heat = sum(_amount(r, HEAT, None) for r in _records(energy, "monthly"))
    electricity = sum(_amount(r, ELECTRICITY, None) for r in _records(energy, "monthly"))
    return electricity > 0 and electricity >= heat * MIN_ELECTRICITY_SHARE


@dataclass(frozen=True, kw_only=True)
class ServerEnergyDescription(SensorEntityDescription):
    """An energy figure read from the server's records."""

    kind: str = HEAT
    span: str = "today"  # today, yesterday or month
    use: str | None = None


def server_energy_descriptions(energy) -> list[ServerEnergyDescription]:
    """Return the sensors this unit gets, from what the server has recorded for it."""
    common = {
        "device_class": SensorDeviceClass.ENERGY,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
        "suggested_display_precision": 0,
    }
    increasing = {**common, "state_class": SensorStateClass.TOTAL_INCREASING}
    descriptions: list[ServerEnergyDescription] = []
    if has_energy(energy, HEAT):
        descriptions += [
            ServerEnergyDescription(key="server_heat_today", name="Heat produced today", **increasing),
            ServerEnergyDescription(key="server_heat_yesterday", name="Heat produced yesterday", span="yesterday", **common),
            ServerEnergyDescription(key="server_heat_month", name="Heat produced this month", span="month", **increasing),
        ]
        used = [use for use in USES if has_energy(energy, HEAT, use)]
        if len(used) > 1:
            # with a single use the split would repeat the total
            descriptions += [
                ServerEnergyDescription(key=f"server_heat_today_{use.lower()}", name=f"Heat produced today ({USES[use]})", use=use, **increasing)
                for use in used
            ]
    if has_pulse_meter(energy):
        descriptions += [
            ServerEnergyDescription(key="server_electricity_today", name="Electricity consumed today", kind=ELECTRICITY, **increasing),
            ServerEnergyDescription(key="server_electricity_yesterday", name="Electricity consumed yesterday", kind=ELECTRICITY, span="yesterday", **common),
            ServerEnergyDescription(key="server_electricity_month", name="Electricity consumed this month", kind=ELECTRICITY, span="month", **increasing),
        ]
    return descriptions


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

    def __init__(self, coordinator, description: ServerEnergyDescription, device_info) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> float | None:
        """Return the kWh of the sensor's span."""
        description = self.entity_description
        return read_span(self.coordinator.get_server_energy(), description.span, description.kind, description.use, dt_util.now())


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

    def __init__(self, hass: HomeAssistant, entry_id: str, entity_id: str) -> None:
        """Initialize the tracker for one meter entity."""
        self.hass = hass
        self.entity_id = entity_id
        self._store = Store(hass, METER_STORAGE_VERSION, meter_storage_key(entry_id))
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
        reading = meter_reading_kwh(self.hass, self.entity_id)
        if reading is None:
            return
        changed = False
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
        reading = meter_reading_kwh(self.hass, self.entity_id)
        if reading is None or reading < current["start"]:
            return None
        return reading - current["start"]

    def electricity_yesterday(self, now: datetime) -> float | None:
        """Return the kWh the meter counted over the whole of yesterday, or None when not measured."""
        last = self._state.get("last_day")
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        if not isinstance(last, dict) or last.get("period") != yesterday:
            return None
        return last.get("energy")


@dataclass(frozen=True, kw_only=True)
class MeteredCopDescription(SensorEntityDescription):
    """A COP from server heat and metered electricity."""

    span: str = "today"


METERED_COP_DESCRIPTIONS = (
    MeteredCopDescription(key="metered_cop_today", name="COP today (metered)"),
    MeteredCopDescription(key="metered_cop_yesterday", name="COP yesterday (metered)", span="yesterday"),
    MeteredCopDescription(key="metered_cop_month", name="COP this month (metered)", span="month"),
)


class CSNetHomeMeteredCopSensor(CoordinatorEntity, SensorEntity):
    """Heat the server recorded divided by the electricity a meter of the user counted."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    entity_description: MeteredCopDescription

    def __init__(self, coordinator, description: MeteredCopDescription, device_info, tracker: MeterTracker) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}"
        self._attr_device_info = device_info
        self._tracker = tracker

    async def async_added_to_hass(self) -> None:
        """Load the kept meter readings before the first state is written."""
        await self._tracker.async_load()
        self._tracker.async_update(dt_util.now())
        await super().async_added_to_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Follow the meter at every poll."""
        self._tracker.async_update(dt_util.now())
        super()._handle_coordinator_update()

    def _figures(self) -> tuple[float | None, float | None]:
        """Return (heat, electricity) in kWh for the sensor's span."""
        now = dt_util.now()
        span = self.entity_description.span
        heat = read_span(self.coordinator.get_server_energy(), span, HEAT, None, now)
        if span == "yesterday":
            return heat, self._tracker.electricity_yesterday(now)
        return heat, self._tracker.electricity("month" if span == "month" else "day", now)

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
            "heat_kwh": heat,
            "electricity_kwh": round(electricity, 3) if electricity is not None else None,
            "meter": self._tracker.entity_id,
        }
