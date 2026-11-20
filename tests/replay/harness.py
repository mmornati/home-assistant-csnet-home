"""Replay a sample through the integration as Home Assistant runs it.

The config entry is set up as usual, but the API client answers each request
with what the sample recorded at that time, and the clock follows the
sample. After each poll the states of the integration's entities are read,
so the figures a change would show on a real unit can be compared.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.const import CONF_ENERGY_METER, CONF_HEAT_SOURCE, CONF_POWER_SUPPLY, DEFAULT_HEAT_SOURCE, DOMAIN

from .sample import Sample

METER_ENERGY_ENTITY = "sensor.replay_meter_energy"
METER_POWER_ENTITY = "sensor.replay_meter_power"
# Replies of one poll arrive within a few seconds of each other
POLL_WINDOW_SECONDS = 15
DEFAULT_INSTALLATIONS = {"status": "success", "data": [{"id": 0}]}

# What is read after each poll, by the key of the entity's unique id
TRACKED = {
    "compressor_hz": f"{DOMAIN}-compressor-compressor_frequency",
    "instant_consumption_w": f"{DOMAIN}-installation-instant_consumption",
    "output_power_w": f"{DOMAIN}-installation-heating_power",
    "instant_cop": f"{DOMAIN}-installation-instant_cop",
    "daily_consumption_kwh": f"{DOMAIN}-installation-daily_consumption",
    "daily_hvac_cop": f"{DOMAIN}-installation-daily_cop_hvac",
    # Heat produced today: CSNet's records or the integration's own measure, per the setting
    "server_heat_today_kwh": f"{DOMAIN}-server_heat_today",
    "server_heat_month_kwh": f"{DOMAIN}-server_heat_month",
    "metered_cop_today": f"{DOMAIN}-metered_cop_today",
    "outdoor_temperature": f"{DOMAIN}-installation-external_temperature",
}


@dataclass
class Poll:
    """What the entities showed after one poll."""

    time: datetime
    values: dict[str, Any]
    meter_energy_kwh: float | None = None
    meter_power_w: float | None = None


@dataclass
class ReplayResult:
    """The outcome of a replay."""

    sample: Sample
    polls: list[Poll] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    entity_count: int = 0
    heat_source: str = DEFAULT_HEAT_SOURCE
    # The poll indexes before which Home Assistant was restarted
    restarts: list[int] = field(default_factory=list)


class _Feeder:
    """Answer the API client's requests with the sample's replies up to the current time."""

    def __init__(self, sample: Sample) -> None:
        self._events = [e for e in sample.events if e.kind != "meter"]
        self._meters = [e for e in sample.events if e.kind == "meter"]
        self._index = 0
        self._meter_index = 0
        self.latest: dict[str, Any] = {}
        self.meter: dict[str, Any] = {}
        self.local_now: datetime | None = None
        # A recording starts between two requests of the slower kinds (alarms,
        # energy records): until the first one, its first reply stands in
        self._first: dict[str, Any] = {}
        for event in self._events:
            self._first.setdefault(event.kind, event.data)

    def advance(self, t: float) -> None:
        """Take every reply recorded up to t (plus the rest of that poll)."""
        limit = t + POLL_WINDOW_SECONDS
        while self._index < len(self._events) and self._events[self._index].t <= limit:
            event = self._events[self._index]
            self.latest[event.kind] = event.data
            self._index += 1
        while self._meter_index < len(self._meters) and self._meters[self._meter_index].t <= limit:
            self.meter = self._meters[self._meter_index].values
            self._meter_index += 1

    def reply(self, description: str) -> Any:
        """Return the reply to a request, as the API client names it."""
        kind = description.replace(" ", "_")
        if kind in self.latest:
            return self.latest[kind]
        if kind == "installations":
            return DEFAULT_INSTALLATIONS
        if kind == "energy_records":
            return _energy_until(self._first.get(kind), self.local_now)
        return self._first.get(kind)


def _written(record: dict) -> datetime | None:
    """Return when CSNet wrote a record, in the unit's local time (naive).

    Its "timestamp" is that local time read as if it were UTC: the date and
    time fields are used instead.
    """
    time = record.get("time") or {}
    try:
        return datetime(time["year"], time["month"], time["day"], time.get("hour") or 0, time.get("minute") or 0, time.get("second") or 0)
    except (KeyError, TypeError, ValueError):
        return None


def _energy_until(reply: Any, local_now: datetime | None) -> Any:
    """Return energy records without the hours written after a (naive local) time.

    Only used for the few minutes before a recording's first energy reply;
    the day's and month's records are left as they are (CSNet stamps them
    with their last update).
    """
    if local_now is None or not isinstance(reply, dict) or not isinstance(reply.get("data"), list):
        return reply
    units = []
    for unit in reply["data"]:
        unit = dict(unit)
        if isinstance(unit.get("hourly"), list):
            unit["hourly"] = [r for r in unit["hourly"] if (_written(r) or local_now) <= local_now]
        units.append(unit)
    return {**reply, "data": units}


def _number(state) -> Any:
    if state is None or state.state in ("unknown", "unavailable", ""):
        return None
    try:
        return float(state.state)
    except ValueError:
        return state.state


class _ErrorCollector(logging.Handler):
    """Keep the errors the integration logs during the replay."""

    def __init__(self) -> None:
        super().__init__(logging.ERROR)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(f"{record.name}: {record.getMessage()}")


async def replay_sample(
    hass: HomeAssistant,
    freezer,
    sample: Sample,
    *,
    power_supply: str | None = None,
    max_polls: int | None = None,
    heat_source: str | None = None,
    restart_before: tuple[int, ...] = (),
) -> ReplayResult:
    """Replay a sample and return what the entities showed after each poll.

    ``heat_source`` picks the heat produced setting; ``restart_before`` lists
    poll indexes before which the entry is unloaded and set up again, the way
    a restart of Home Assistant does.
    """
    header = sample.header
    if header.get("time_zone"):
        await hass.config.async_set_time_zone(header["time_zone"])
    feeder = _Feeder(sample)
    result = ReplayResult(sample)
    has_meter_energy = bool((header.get("meter") or {}).get("energy"))
    has_meter_power = bool((header.get("meter") or {}).get("power"))

    data = {
        CONF_USERNAME: "replay",
        CONF_PASSWORD: "replay",
        CONF_SCAN_INTERVAL: int(header.get("scan_interval") or 60),
    }
    if has_meter_energy:
        data[CONF_ENERGY_METER] = METER_ENERGY_ENTITY
    if power_supply or header.get("power_supply"):
        data[CONF_POWER_SUPPLY] = power_supply or header["power_supply"]
    if heat_source:
        data[CONF_HEAT_SOURCE] = heat_source
        result.heat_source = heat_source
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    entry.add_to_hass(hass)

    polls = sample.poll_times()
    if max_polls:
        polls = polls[:max_polls]
    if not polls:
        return result

    async def fake_get_json(self, url, headers, description, renew_session=True):  # noqa: ARG001
        return feeder.reply(description)

    async def fake_login(self):
        self.logged_in = True
        return True

    def set_meter(when: datetime) -> tuple[float | None, float | None]:
        energy = feeder.meter.get("energy_kwh")
        power = feeder.meter.get("power_w")
        if has_meter_energy:
            hass.states.async_set(
                METER_ENERGY_ENTITY,
                "unknown" if energy is None else str(energy),
                {"unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
            )
        if has_meter_power:
            hass.states.async_set(
                METER_POWER_ENTITY,
                "unknown" if power is None else str(power),
                {"unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
            )
        return energy, power

    errors = _ErrorCollector()
    logger = logging.getLogger("custom_components.csnet_home")
    logger.addHandler(errors)
    try:
        with (
            patch.object(CSNetHomeAPI, "_async_get_json", fake_get_json),
            patch.object(CSNetHomeAPI, "async_login", fake_login),
            patch.object(CSNetHomeAPI, "load_translations", AsyncMock()),
            patch.object(CSNetHomeAPI, "close", AsyncMock()),
            patch.object(CSNetHomeAPI, "_async_ensure_session", AsyncMock(return_value=True)),
        ):
            first = sample.at(polls[0])
            freezer.move_to(first)
            feeder.advance(polls[0])
            feeder.local_now = dt_util.as_local(first).replace(tzinfo=None)
            set_meter(first)
            assert await hass.config_entries.async_setup(entry.entry_id), "the entry did not set up"
            await hass.async_block_till_done()
            coordinator = entry.runtime_data.coordinator
            # the replay decides when to poll, not the coordinator's timer
            coordinator.update_interval = None

            registry = er.async_get(hass)
            entities = {name: registry.async_get_entity_id("sensor", DOMAIN, uid) for name, uid in TRACKED.items()}
            result.entity_count = len(er.async_entries_for_config_entry(registry, entry.entry_id))

            for index, t in enumerate(polls):
                when = sample.at(t)
                if index:
                    freezer.move_to(when)
                    feeder.advance(t)
                    feeder.local_now = dt_util.as_local(when).replace(tzinfo=None)
                    energy, power = set_meter(when)
                    if index in restart_before:
                        # the first poll of a set up is the entry's own refresh
                        assert await hass.config_entries.async_unload(entry.entry_id)
                        await hass.async_block_till_done()
                        assert await hass.config_entries.async_setup(entry.entry_id), "the entry did not set up again"
                        await hass.async_block_till_done()
                        coordinator = entry.runtime_data.coordinator
                        coordinator.update_interval = None
                        result.restarts.append(index)
                    else:
                        async_fire_time_changed(hass, when)
                        await coordinator.async_refresh()
                        await hass.async_block_till_done()
                else:
                    energy, power = feeder.meter.get("energy_kwh"), feeder.meter.get("power_w")
                values = {name: _number(hass.states.get(entity_id)) if entity_id else None for name, entity_id in entities.items()}
                result.polls.append(Poll(dt_util.as_local(when), values, energy, power))

            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()
    finally:
        logger.removeHandler(errors)
    result.errors = errors.messages
    return result
