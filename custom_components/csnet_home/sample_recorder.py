"""Record what CSNet Manager sends, to share it as a sample for testing changes.

A sample is a gzip-compressed JSON Lines file. The first line is a header that
says what was recorded; every other line is one reply from CSNet Manager, as
received but redacted the same way as the diagnostics download:

    {"t": 61.2, "kind": "installation_devices", "data": {...}}

``t`` is the number of seconds since the recording started. When a meter is
given, its reading is recorded after each reply with the readings, so the
estimates can be compared against it later:

    {"t": 61.2, "kind": "meter", "energy_kwh": 1234.5, "power_w": 1830.0}

The samples are replayed by the integration's tests (``tests/replay``) and
shared at https://github.com/mmornati/csnet-home-samples.
"""

from __future__ import annotations

import gzip
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .diagnostics import REDACTED, redact
from .server_energy import meter_reading_kwh

_LOGGER = logging.getLogger(__name__)

SAMPLE_FORMAT = "csnet-home-sample"
SAMPLE_VERSION = 1
SAMPLES_DIR = "csnet_home_samples"
SHARE_URL = "https://github.com/mmornati/csnet-home-samples"

# What each request of the API client is recorded as
KINDS = {
    "elements": "elements",
    "installation devices": "installation_devices",
    "installation alarms": "installation_alarms",
    "energy records": "energy_records",
    "installations": "installations",
}
# The meter is read once per poll, after this reply
METER_AFTER_KIND = "installation_devices"
# Replies asked for less often and rarely different: written only when they changed.
# The energy records hold two weeks of hours (about 100 kB) and change once an hour.
WRITE_WHEN_CHANGED = {"energy_records", "installation_alarms", "installations"}
# Lines are written in batches: a poll a minute, written every ten minutes
FLUSH_SECONDS = 600


# Identifiers the diagnostics download never meets but the raw replies carry
_EXTRA_KEYS = {"installation_id"}


def _firmware_version(value: Any) -> Any:
    """Keep the version of a firmware string ("H-0302 0101000065574967"), not what follows it."""
    if isinstance(value, str) and " " in value.strip():
        return f"{value.split()[0]} {REDACTED}"
    return value


def _redact_extra(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            key: (REDACTED if key in _EXTRA_KEYS and value not in (None, "", 0) else _firmware_version(value) if key == "firmware" else _redact_extra(value))
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_redact_extra(item) for item in data]
    return data


def redact_reply(kind: str, data: Any) -> Any:
    """Return a reply with what identifies the account or the home removed."""
    data = _redact_extra(redact(data))
    # "name" holds the installation's name here; elsewhere it names a zone or a device
    if kind == "elements" and isinstance(data, dict) and isinstance(data.get("data"), dict) and data["data"].get("name"):
        data["data"]["name"] = REDACTED
    if kind == "installations" and isinstance(data, dict) and isinstance(data.get("data"), list):
        # names, addresses and the people who may use an installation: only how many there are matters
        return {"status": data.get("status"), "data": [{"id": index} for index, _ in enumerate(data["data"])]}
    return data


def _float_state(hass: HomeAssistant, entity_id: str | None) -> float | None:
    """Return an entity's state as a number, or None."""
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
        return None
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None
    if state.attributes.get("unit_of_measurement") == "kW":
        value *= 1000
    return value


class SampleRecorder:
    """Write the replies of CSNet Manager to a sample file for a while."""

    def __init__(
        self,
        hass: HomeAssistant,
        path: Path,
        header: dict[str, Any],
        duration_seconds: float,
        meter_energy_entity: str | None = None,
        meter_power_entity: str | None = None,
    ) -> None:
        """Prepare a recording; nothing is written before ``async_start``."""
        self.hass = hass
        self.path = path
        self._header = header
        self._started = time.monotonic()
        self._ends = self._started + duration_seconds
        self._last_flush = self._started
        self._meter_energy_entity = meter_energy_entity
        self._meter_power_entity = meter_power_entity
        self._lines: list[str] = []
        self._last_reply: dict[str, str] = {}
        self.replies = 0

    @property
    def active(self) -> bool:
        """Return whether replies are still recorded."""
        return time.monotonic() < self._ends

    @property
    def ends_at(self) -> datetime:
        """Return when the recording stops."""
        return dt_util.utcnow() + timedelta(seconds=max(0.0, self._ends - time.monotonic()))

    async def async_start(self) -> None:
        """Create the file with its header."""
        line = json.dumps(self._header, separators=(",", ":"), ensure_ascii=False)
        await self.hass.async_add_executor_job(self._write, [line], "wt")

    def add(self, description: str, data: Any) -> None:
        """Record one reply of CSNet Manager. Called by the API client for every reply it reads."""
        kind = KINDS.get(description)
        if kind is None or not self.active:
            return
        elapsed = round(time.monotonic() - self._started, 1)
        try:
            payload = json.dumps(redact_reply(kind, data), separators=(",", ":"), ensure_ascii=False)
        except (TypeError, ValueError) as err:
            _LOGGER.debug("Could not record the %s reply: %s", description, err)
            return
        self.replies += 1
        if kind in WRITE_WHEN_CHANGED:
            if self._last_reply.get(kind) == payload:
                return
            self._last_reply[kind] = payload
        self._lines.append(f'{{"t":{elapsed},"kind":"{kind}","data":{payload}}}')
        if kind == METER_AFTER_KIND and (self._meter_energy_entity or self._meter_power_entity):
            meter = {"t": elapsed, "kind": "meter"}
            if self._meter_energy_entity:
                meter["energy_kwh"] = meter_reading_kwh(self.hass, self._meter_energy_entity)
            if self._meter_power_entity:
                meter["power_w"] = _float_state(self.hass, self._meter_power_entity)
            self._lines.append(json.dumps(meter, separators=(",", ":")))
        if time.monotonic() - self._last_flush >= FLUSH_SECONDS:
            self.hass.async_create_task(self.async_flush())

    async def async_flush(self) -> None:
        """Write the recorded lines to the file."""
        self._last_flush = time.monotonic()
        lines, self._lines = self._lines, []
        if lines:
            await self.hass.async_add_executor_job(self._write, lines, "at")

    def _write(self, lines: list[str], mode: str) -> None:
        """Write lines to the file; each write is a gzip member of its own, which gzip readers join."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(self.path, mode, encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")


def sample_header(
    *,
    integration_version: str,
    scan_interval: float | None,
    time_zone: str,
    power_supply: str | None,
    meter_energy: bool,
    meter_power: bool,
    notes: str | None,
) -> dict[str, Any]:
    """Return the first line of a sample file."""
    return {
        "format": SAMPLE_FORMAT,
        "version": SAMPLE_VERSION,
        "source": "recorder",
        "start": dt_util.utcnow().isoformat(timespec="seconds"),
        "time_zone": time_zone,
        "integration_version": integration_version,
        "scan_interval": scan_interval,
        "power_supply": power_supply,
        "meter": {"energy": meter_energy, "power": meter_power},
        "notes": notes or "",
    }


def sample_path(config_dir: str) -> Path:
    """Return a new sample file's path in Home Assistant's configuration folder."""
    stamp = dt_util.now().strftime("%Y%m%d-%H%M")
    return Path(config_dir) / SAMPLES_DIR / f"csnet-sample-{stamp}.jsonl.gz"
