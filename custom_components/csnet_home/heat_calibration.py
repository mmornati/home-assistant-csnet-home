"""Self-calibration of the measured heat against the unit's own heat counter.

The integration measures the heat from the water flow and two temperatures the
unit reports in whole degrees. With the usual difference of 2 to 5 °C between
them, a probe that reads a few tenths low or high changes the heat by 5 to 25 %,
differently on each unit. The unit also counts the heat it produced itself, in
whole kWh (``unitCapacity``): its own controller and CSNet show that counter.

Between two steps of that counter the unit produced a known number of kWh.
Over the same time the integration measured its own figure. Their ratio is the
correction for this unit; it is learnt slowly, one window of the counter after
another, and kept across restarts. One factor is kept for each use: space
heating and cooling (both at the water outlet; a unit's probes may read
differently cold than warm) and hot water (the exchanger outlet).

A window counts only when all of it was one use, measured at its own probe,
with no defrost, no backup heater or boiler, and no reading missing.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

HEAT_CALIBRATION_STORAGE_VERSION = 1
# The uses calibrated, each with a factor of its own: space heating and
# cooling at the water outlet, hot water at the exchanger outlet
CALIBRATED_USES = ("spaceHeating", "spaceCooling", "dhw")
# kWh of the counter a window needs before it is learnt from: the counter's
# steps are seen at the next reading, so a window is a few readings long at
# each end; a longer window makes that share small
MIN_WINDOW_KWH = {"spaceHeating": 5, "spaceCooling": 5, "dhw": 2}
# Readings further apart than this break a window: heat in between is unknown
MAX_READING_GAP = timedelta(minutes=5)
# A window whose ratio falls outside these says something else went on: it is left out
MIN_SAMPLE = 0.5
MAX_SAMPLE = 2.0
# The correction stays within these, whatever the windows say
MIN_FACTOR = 0.6
MAX_FACTOR = 1.6
# The first windows are averaged; after that each one moves the factor by this share
MIN_LEARNING_RATE = 0.1
SAVE_DELAY_S = 60


def heat_calibration_storage_key(entry_id: str) -> str:
    """Return the storage key of a config entry's heat calibration."""
    return f"{DOMAIN}.{entry_id}.heat_calibration"


class HeatCalibration:
    """Correction factors of the measured heat, learnt from the unit's heat counter."""

    def __init__(self, hass=None, entry_id: str | None = None) -> None:
        """Initialize with no correction; without hass nothing is kept across restarts."""
        self.hass = hass
        self.factors: dict[str, float] = {}
        self.windows: dict[str, int] = {}
        self._store = Store(hass, HEAT_CALIBRATION_STORAGE_VERSION, heat_calibration_storage_key(entry_id)) if hass and entry_id else None
        self._last_reading: int | None = None
        self._last_time: datetime | None = None
        self._reset_window()

    def factor(self, use: str | None) -> float:
        """Return the correction of the heat measured for a use."""
        return self.factors.get(use, 1.0) if use in CALIBRATED_USES else 1.0

    def _reset_window(self) -> None:
        """Drop the window under way: the next step of the counter starts a new one."""
        self._started = False
        self._use: str | None = None
        self._clean = False
        self._counted = 0
        self._measured_kwh = 0.0

    def _start_window(self, use: str | None, clean: bool) -> None:
        """Start a window at a step of the counter."""
        self._started = True
        self._use = use
        self._clean = clean and use in CALIBRATED_USES
        self._counted = 0
        self._measured_kwh = 0.0

    def observe(self, now: datetime, reading, use: str | None, measured_watts: float, clean: bool) -> None:
        """Take a new reading of the unit: its heat counter, what it does, and the heat measured, uncorrected.

        ``clean`` says whether the heat of this reading was measured at the
        use's own probe, with no defrost and no other heat source. Called once
        per update of the coordinator.
        """
        from .server_energy import UnitHeatCounter  # pylint: disable=import-outside-toplevel

        if not isinstance(reading, int) or isinstance(reading, bool) or reading < 0:
            self._last_reading = None
            self._reset_window()
            return
        previous, last_time = self._last_reading, self._last_time
        self._last_reading, self._last_time = reading, now
        if previous is None or last_time is None or not timedelta(0) < now - last_time <= MAX_READING_GAP:
            self._reset_window()
            return
        hours = (now - last_time).total_seconds() / 3600
        rise = UnitHeatCounter.rise(previous, reading, hours)
        if rise is None:
            self._reset_window()
            return
        if self._started:
            self._measured_kwh += max(measured_watts or 0.0, 0.0) * hours / 1000
            self._counted += rise
            if not clean or use != self._use:
                self._clean = False
        if rise <= 0:
            return
        if self._started and self._clean:
            if self._counted < MIN_WINDOW_KWH[self._use]:
                return
            self._learn(self._use, self._counted, self._measured_kwh)
        self._start_window(use, clean)

    def _learn(self, use: str, counted: int, measured_kwh: float) -> None:
        """Move the factor of a use towards the ratio of a finished window."""
        if measured_kwh <= 0:
            return
        sample = counted / measured_kwh
        if not MIN_SAMPLE <= sample <= MAX_SAMPLE:
            _LOGGER.debug("Heat window of %s left out: counter %s kWh, measured %.2f kWh", use, counted, measured_kwh)
            return
        windows = self.windows.get(use, 0)
        current = self.factors.get(use, 1.0)
        rate = max(MIN_LEARNING_RATE, 1 / (windows + 1))
        self.factors[use] = max(MIN_FACTOR, min(MAX_FACTOR, current + rate * (sample - current)))
        self.windows[use] = windows + 1
        if self._store is not None:
            self._store.async_delay_save(self._data_to_save, SAVE_DELAY_S)

    def as_attributes(self) -> dict:
        """Return the learnt factors and the windows each one comes from, for display."""
        return {use: {"factor": round(self.factors[use], 3), "windows": self.windows.get(use, 0)} for use in CALIBRATED_USES if use in self.factors}

    def _data_to_save(self) -> dict:
        """Return what is kept across restarts."""
        return {"factors": dict(self.factors), "windows": dict(self.windows)}

    async def async_load(self) -> None:
        """Load the factors learnt before the last restart."""
        if self._store is None:
            return
        try:
            stored = await self._store.async_load()
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not load the heat calibration: %s", exc)
            return
        if not isinstance(stored, dict):
            return
        factors, windows = stored.get("factors"), stored.get("windows")
        if not isinstance(factors, dict):
            return
        for use, factor in factors.items():
            if use not in CALIBRATED_USES or not isinstance(factor, (int, float)) or isinstance(factor, bool):
                continue
            if MIN_FACTOR <= factor <= MAX_FACTOR:
                self.factors[use] = float(factor)
                count = windows.get(use) if isinstance(windows, dict) else None
                self.windows[use] = count if isinstance(count, int) and not isinstance(count, bool) and count > 0 else 1
