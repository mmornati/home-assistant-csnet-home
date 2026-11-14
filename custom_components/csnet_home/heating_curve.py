"""Heating curve (water law) of each circuit, entered by the user.

The unit's controller works out the water temperature of a heating circuit
from the outdoor temperature with an OTC curve ("loi d'eau"). CSNet reports
which kind of curve each circuit uses (``otcTypeHeatC1``/``otcTypeHeatC2``)
but not the curve itself, so the user copies the installer's values into the
integration options. Nothing is ever sent to the unit.

From those values a sensor gives the water temperature the curve asks for
right now. It follows the unit controller's manual:

- "Points": two points (low ambient temperature, water temperature) and (high
  ambient temperature, water temperature), a straight line between them and a
  flat line outside them.
- "Gradient": a line that starts at 20 °C water for 20 °C outside and rises by
  the gradient (0.2 to 2.2) for every degree the outside drops below 20 °C.
- Both: a vertex offset (-10 to +10 °C) moves the whole curve up or down.

The unit uses the average outdoor temperature (averaged over a period the
installer sets), so the sensor does too. The result is kept within the
circuit's water limits when the unit reports them. The unit can still raise
the water temperature above the curve when a room is far below its setpoint
(room compensation) or lower it in eco mode; the sensor does not include that.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OTC_HEATING_TYPE_GRADIENT, OTC_HEATING_TYPE_NAMES, OTC_HEATING_TYPE_POINTS

CURVE_TYPES = (OTC_HEATING_TYPE_POINTS, OTC_HEATING_TYPE_GRADIENT)

# Zone ids that mean a circuit exists
CIRCUIT_ZONES = {1: frozenset({1, 5}), 2: frozenset({2, 6})}

# Option keys, per circuit: f"c{circuit}_{suffix}"
LOW_AMBIENT = "low_ambient_temperature"
WATER_AT_LOW_AMBIENT = "water_at_low_ambient"
HIGH_AMBIENT = "high_ambient_temperature"
WATER_AT_HIGH_AMBIENT = "water_at_high_ambient"
GRADIENT = "gradient"
VERTEX_OFFSET = "vertex_offset"

POINTS_FIELDS = (LOW_AMBIENT, WATER_AT_LOW_AMBIENT, HIGH_AMBIENT, WATER_AT_HIGH_AMBIENT)
GRADIENT_FIELDS = (GRADIENT,)
FIELDS_BY_TYPE = {OTC_HEATING_TYPE_POINTS: POINTS_FIELDS, OTC_HEATING_TYPE_GRADIENT: GRADIENT_FIELDS}

# Ranges of the unit controller
GRADIENT_RANGE = (0.2, 2.2)
VERTEX_OFFSET_RANGE = (-10.0, 10.0)
AMBIENT_RANGE = (-30.0, 35.0)
WATER_RANGE = (15.0, 80.0)

# The gradient curve starts here: 20 °C of water for 20 °C outside
GRADIENT_ORIGIN = 20.0
# Outdoor temperatures the curve is given at, for a card to draw it
CURVE_SAMPLES = tuple(range(-20, 30, 5))

# Below this the unit reports a missing probe, not a temperature
_NO_PROBE_BELOW = -60


def option_key(circuit: int, field: str) -> str:
    """Return the option key of one field of one circuit."""
    return f"c{circuit}_{field}"


@dataclass(frozen=True)
class HeatingCurve:
    """The heating curve of one circuit."""

    curve_type: int
    low_ambient: float | None = None
    water_at_low_ambient: float | None = None
    high_ambient: float | None = None
    water_at_high_ambient: float | None = None
    gradient: float | None = None
    vertex_offset: float = 0.0

    def water_temperature(self, outdoor: float) -> float:
        """Return the water temperature the curve gives for an outdoor temperature, before limits."""
        if self.curve_type == OTC_HEATING_TYPE_GRADIENT:
            base = GRADIENT_ORIGIN + self.gradient * max(GRADIENT_ORIGIN - outdoor, 0.0)
        elif outdoor <= self.low_ambient:
            base = self.water_at_low_ambient
        elif outdoor >= self.high_ambient:
            base = self.water_at_high_ambient
        else:
            share = (outdoor - self.low_ambient) / (self.high_ambient - self.low_ambient)
            base = self.water_at_low_ambient + share * (self.water_at_high_ambient - self.water_at_low_ambient)
        return base + self.vertex_offset

    def draw_at(self) -> list[float]:
        """Return the outdoor temperatures to give the curve at: every 5 °C, and where the line bends."""
        bends = {GRADIENT_ORIGIN} if self.curve_type == OTC_HEATING_TYPE_GRADIENT else {self.low_ambient, self.high_ambient}
        return sorted({float(t) for t in CURVE_SAMPLES} | bends)


def curve_from_options(options, circuit: int, curve_type) -> HeatingCurve | None:
    """Return the curve the user entered for a circuit, for the curve type the unit uses; None when incomplete."""
    fields = FIELDS_BY_TYPE.get(curve_type)
    if not fields:
        return None
    values = {}
    for field in fields:
        value = options.get(option_key(circuit, field))
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        values[field] = float(value)
    if curve_type == OTC_HEATING_TYPE_POINTS and values[LOW_AMBIENT] >= values[HIGH_AMBIENT]:
        return None
    offset = options.get(option_key(circuit, VERTEX_OFFSET))
    return HeatingCurve(
        curve_type=curve_type,
        low_ambient=values.get(LOW_AMBIENT),
        water_at_low_ambient=values.get(WATER_AT_LOW_AMBIENT),
        high_ambient=values.get(HIGH_AMBIENT),
        water_at_high_ambient=values.get(WATER_AT_HIGH_AMBIENT),
        gradient=values.get(GRADIENT),
        vertex_offset=float(offset) if isinstance(offset, (int, float)) and not isinstance(offset, bool) else 0.0,
    )


def _number(value) -> float | None:
    """Return a reported number, or None when the unit sends nothing usable."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return float(value)


def circuit_curve_type(heating_status, circuit: int) -> int | None:
    """Return the heating curve type the unit reports for a circuit."""
    if not isinstance(heating_status, dict):
        return None
    value = heating_status.get(f"otcTypeHeatC{circuit}")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def water_limits(heating_status, circuit: int) -> tuple[float | None, float | None]:
    """Return the lowest and highest heating water temperature the unit allows for a circuit, when reported."""
    if not isinstance(heating_status, dict):
        return None, None
    low = _number(heating_status.get(f"heatMinC{circuit}"))
    high = _number(heating_status.get(f"heatMaxC{circuit}"))
    low = low if low is not None and low > 0 else None
    high = high if high is not None and high > 0 else None
    if low is not None and high is not None and low > high:
        return None, None
    return low, high


def average_outdoor_temperature(heating_status) -> float | None:
    """Return the average outdoor temperature the unit computes its curves from."""
    if not isinstance(heating_status, dict):
        return None
    value = _number(heating_status.get("outdoorAmbientAverageTemp"))
    if value is None or value <= _NO_PROBE_BELOW:
        return None
    return value


def _clamp(value: float, low: float | None, high: float | None) -> float:
    if high is not None:
        value = min(value, high)
    if low is not None:
        value = max(value, low)
    return value


def curve_circuits(heating_status, zone_ids) -> dict[int, int]:
    """Return the circuits that have a curve the user can describe, with their curve type."""
    circuits = {}
    for circuit, zones in CIRCUIT_ZONES.items():
        curve_type = circuit_curve_type(heating_status, circuit)
        if zone_ids & zones and curve_type in CURVE_TYPES:
            circuits[circuit] = curve_type
    return circuits


class CSNetHomeHeatingCurveSensor(CoordinatorEntity, SensorEntity):
    """Water temperature the heating curve of a circuit asks for, from the user's copy of the curve."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, circuit: int, options, device_info, read_status: Callable) -> None:
        """Initialize the sensor; ``read_status`` returns the unit status of the last poll."""
        super().__init__(coordinator)
        self._circuit = circuit
        self._options = dict(options)
        self._read_status = read_status
        self._attr_name = f"Circuit {circuit} heating curve water temperature"
        self._attr_unique_id = unique_id(circuit)
        self._attr_device_info = device_info

    def _curve(self) -> tuple[HeatingCurve | None, dict]:
        status = self._read_status()
        curve_type = circuit_curve_type(status, self._circuit)
        return curve_from_options(self._options, self._circuit, curve_type), status

    @property
    def available(self) -> bool:
        """Available while the unit uses the kind of curve the user described."""
        curve, status = self._curve()
        return super().available and curve is not None and average_outdoor_temperature(status) is not None

    @property
    def native_value(self) -> float | None:
        """Return the water temperature of the curve at the current average outdoor temperature."""
        curve, status = self._curve()
        outdoor = average_outdoor_temperature(status)
        if curve is None or outdoor is None:
            return None
        low, high = water_limits(status, self._circuit)
        return round(_clamp(curve.water_temperature(outdoor), low, high), 1)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the curve, so a card can draw it, and what the value was computed from."""
        curve, status = self._curve()
        curve_type = circuit_curve_type(status, self._circuit)
        attributes = {
            "curve_type": OTC_HEATING_TYPE_NAMES.get(curve_type, curve_type),
            "outdoor_temperature": average_outdoor_temperature(status),
        }
        if curve is None:
            attributes["configured"] = False
            return attributes
        low, high = water_limits(status, self._circuit)
        attributes.update(
            {
                "configured": True,
                "vertex_offset": curve.vertex_offset,
                "minimum_water_temperature": low,
                "maximum_water_temperature": high,
                # [outdoor, water] every 5 °C and where the line bends, limits applied, for a card to draw the curve
                "curve": [[outdoor, round(_clamp(curve.water_temperature(outdoor), low, high), 1)] for outdoor in curve.draw_at()],
            }
        )
        if curve.curve_type == OTC_HEATING_TYPE_GRADIENT:
            attributes["gradient"] = curve.gradient
        else:
            attributes.update(
                {
                    "low_ambient_temperature": curve.low_ambient,
                    "water_at_low_ambient": curve.water_at_low_ambient,
                    "high_ambient_temperature": curve.high_ambient,
                    "water_at_high_ambient": curve.water_at_high_ambient,
                }
            )
        return attributes


def unique_id(circuit: int) -> str:
    """Return the unique id of a circuit's heating curve sensor."""
    return f"{DOMAIN}-unit-c{circuit}_heating_curve_water_temperature"
