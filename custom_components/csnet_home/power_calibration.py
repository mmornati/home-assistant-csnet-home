"""Self-calibration of the estimated compressor power.

The unit reports its current in whole Amps, truncated: 6 A means 6.0 to 6.99 A.
That gives a range the real power lies in. Whenever the model's estimate falls
outside that range the model is wrong in a known direction, so a correction
factor is moved a little towards the range. Over time the model fits the unit
it runs on, instead of the unit it was first tuned with.

The model's error changes with the compressor speed, so one factor is kept per
band of frequency.
"""

from __future__ import annotations

import logging

from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

POWER_CALIBRATION_STORAGE_VERSION = 1
# Width of a frequency band, and the band everything faster falls in
BAND_WIDTH_HZ = 20
LAST_BAND = 6
# Share of the distance to the range covered at each reading outside it
LEARNING_RATE = 0.05
# The factor stays within these, whatever the readings say
MIN_FACTOR = 0.6
MAX_FACTOR = 1.6
# A factor is written to storage once it has moved this much
SAVE_STEP = 0.01


def power_calibration_storage_key(entry_id: str) -> str:
    """Return the storage key of a config entry's power calibration."""
    return f"{DOMAIN}.{entry_id}.power_calibration"


class PowerCalibration:
    """Correction factors of the compressor power model, learnt from the reported current."""

    def __init__(self, hass=None, entry_id: str | None = None) -> None:
        """Initialize with no correction; without hass nothing is kept across restarts."""
        self.hass = hass
        self.factors: dict[int, float] = {}
        self._saved: dict[int, float] = {}
        self._store = Store(hass, POWER_CALIBRATION_STORAGE_VERSION, power_calibration_storage_key(entry_id)) if hass and entry_id else None

    @staticmethod
    def band(hz: float) -> int:
        """Return the frequency band of a compressor speed."""
        return max(0, min(int(hz // BAND_WIDTH_HZ), LAST_BAND))

    def factor(self, hz: float) -> float:
        """Return the correction factor for a compressor speed."""
        return self.factors.get(self.band(hz), 1.0)

    def learn(self, hz: float, compressor_power: float, low: float, high: float) -> None:
        """Move the factor towards the range the reported current allows.

        ``compressor_power`` is the model's uncorrected figure, ``low`` and
        ``high`` the range for it. Called once per reading of the unit.
        """
        if compressor_power <= 0 or high <= 0:
            return
        band = self.band(hz)
        current = self.factors.get(band, 1.0)
        estimate = compressor_power * current
        if estimate < low:
            target = low / compressor_power
        elif estimate > high:
            target = high / compressor_power
        else:
            return
        factor = max(MIN_FACTOR, min(MAX_FACTOR, current + LEARNING_RATE * (target - current)))
        self.factors[band] = factor
        if self._store is not None and abs(factor - self._saved.get(band, 1.0)) >= SAVE_STEP:
            self._saved[band] = factor
            self.hass.async_create_task(self._async_save())

    def as_attributes(self) -> dict[str, float]:
        """Return the learnt factors, by frequency band, for display."""
        attributes = {}
        for band in sorted(self.factors):
            label = f"{band * BAND_WIDTH_HZ}+ Hz" if band == LAST_BAND else f"{band * BAND_WIDTH_HZ}-{(band + 1) * BAND_WIDTH_HZ - 1} Hz"
            attributes[label] = round(self.factors[band], 3)
        return attributes

    async def async_load(self) -> None:
        """Load the factors learnt before the last restart."""
        if self._store is None:
            return
        try:
            stored = await self._store.async_load()
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not load the power calibration: %s", exc)
            return
        if not isinstance(stored, dict) or not isinstance(stored.get("factors"), dict):
            return
        for band, factor in stored["factors"].items():
            try:
                band, factor = int(band), float(factor)
            except (TypeError, ValueError):
                continue
            if 0 <= band <= LAST_BAND and MIN_FACTOR <= factor <= MAX_FACTOR:
                self.factors[band] = self._saved[band] = factor

    async def _async_save(self) -> None:
        """Write the factors to storage."""
        try:
            await self._store.async_save({"factors": {str(band): factor for band, factor in self.factors.items()}})
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not save the power calibration: %s", exc)


class CrankcaseHeaterTracker:
    """Tell whether the crankcase heater is on, from the discharge temperature.

    With the compressor stopped the heater runs in cycles: the discharge
    temperature climbs a few degrees while it heats and falls back while it
    rests. The direction of the last change says which of the two it is. The
    temperature comes in whole degrees, so the state holds between changes.
    """

    def __init__(self) -> None:
        """Start as heating: nothing is known until the temperature moves."""
        self.heating = True
        self._temperature = None

    def update(self, compressor_running: bool, discharge_temperature) -> bool:
        """Take a new reading into account, once per reading, and return whether the heater is on."""
        if compressor_running:
            # A compressor that has just run is hot: no heating until it has
            # cooled down and the temperature climbs again
            self.heating = False
            self._temperature = None
            return self.heating
        if not isinstance(discharge_temperature, (int, float)):
            return self.heating
        if self._temperature is not None:
            if discharge_temperature > self._temperature:
                self.heating = True
            elif discharge_temperature < self._temperature:
                self.heating = False
        self._temperature = discharge_temperature
        return self.heating
