"""More readings of the unit: eco offsets, board software, and equipment not every unit has.

Each sensor is created only when the unit reports a real value for it, and
the ones for a hot water tank, fan coils, a cascade or an R290 unit only on
units that have that equipment. Most of them could not be tried on a real
unit: what they read and how is taken from the CSNet web app.

The unit status also carries per-zone "wired" and "wireless" thermostat
temperatures. They are not exposed: on a unit with two circuits the
"wireless" value of one zone mirrors the other zone's, so what each field
means could not be established.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfVolumeFlowRate
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

CIRCUIT_1_ZONES = frozenset({1, 5})
CIRCUIT_2_ZONES = frozenset({2, 6})
DHW_ZONES = frozenset({3})


def _degrees_above_zero(value) -> float | None:
    """Return a whole number of degrees; zero and negative values are "not reported"."""
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        return None
    return float(value)


def _degrees(value) -> float | None:
    """Return a whole number of degrees; negative values are "not reported"."""
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        return None
    return float(value)


def _positive_hundredths(value) -> float | None:
    """Return a flow sent in hundredths of m3/h; zero and negative values are "not reported"."""
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        return None
    return round(value / 100, 2)


def _count(value) -> int | None:
    """Return a number of units; negative values are "not reported"."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return None
    return value


DHW_MODES = {0: "economic", 1: "standard", 2: "high_demand"}
FAN_SPEEDS = {0: "off", 1: "low", 2: "medium", 3: "high"}


def _dhw_mode(value) -> str | None:
    """Return how the tank is heated; the web app shows anything but 1 and 2 as economic."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return None
    return DHW_MODES.get(value, "economic")


def _fan_speed(value) -> str | None:
    """Return the speed a fan coil is running at."""
    if not isinstance(value, int) or isinstance(value, bool):
        return None
    return FAN_SPEEDS.get(value)


def _has_fan_coils(status) -> bool:
    """Return True on units set up for fan coils (the web app's fan coil bit)."""
    bits = status.get("systemConfigBits")
    return isinstance(bits, int) and not isinstance(bits, bool) and bits > 0 and bool(bits & 0x2000)


def _is_cascade(status, cascade) -> bool:
    """Return True when the unit is part of a cascade with units enabled."""
    enabled = cascade.get("cascadeEnabledUnits") if isinstance(cascade, dict) else None
    return isinstance(enabled, int) and not isinstance(enabled, bool) and enabled > 0


def _hex_version(value) -> str | None:
    """Return a board software number the way the other software sensors show it."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return None
    return f"0x{value:04X}"


@dataclass(frozen=True, kw_only=True)
class UnitSensorDescription(SensorEntityDescription):
    """A reading taken from one key of the unit status."""

    status_key: str
    convert: Callable
    needs_zone: frozenset[int] | None = None
    # "status" reads heatingStatus, "cascade" reads the unit's cascadeInfo
    source: str = "status"
    # an extra condition on the unit: (heatingStatus, cascadeInfo) -> bool
    applies: Callable | None = None


_OFFSET = {"native_unit_of_measurement": UnitOfTemperature.CELSIUS, "entity_category": EntityCategory.DIAGNOSTIC}

UNIT_SENSOR_DESCRIPTIONS: tuple[UnitSensorDescription, ...] = (
    # How many degrees "eco" takes off the setpoint
    UnitSensorDescription(
        key="c1_eco_offset_heating",
        name="Circuit 1 eco offset (heating)",
        status_key="ecoOffsetTempHeatC1",
        convert=_degrees,
        needs_zone=CIRCUIT_1_ZONES,
        **_OFFSET,
    ),
    UnitSensorDescription(
        key="c2_eco_offset_heating",
        name="Circuit 2 eco offset (heating)",
        status_key="ecoOffsetTempHeatC2",
        convert=_degrees,
        needs_zone=CIRCUIT_2_ZONES,
        **_OFFSET,
    ),
    UnitSensorDescription(
        key="indoor_board_software",
        name="Indoor board software",
        status_key="pcbSoft",
        convert=_hex_version,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Hot water tank / Yutampo
    UnitSensorDescription(
        key="dhw_mode",
        name="DHW mode",
        status_key="controlTypeDHW",
        convert=_dhw_mode,
        needs_zone=DHW_ZONES,
        device_class=SensorDeviceClass.ENUM,
        options=list(DHW_MODES.values()),
    ),
    UnitSensorDescription(
        key="dhw_anti_legionella_temperature",
        name="DHW anti-legionella temperature",
        status_key="antiLegionellaSettingDHW",
        convert=_degrees_above_zero,
        needs_zone=DHW_ZONES,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Fan coils: the speed the fan runs at, next to the one asked for on the climate entity
    UnitSensorDescription(
        key="c1_fan_speed_actual",
        name="Circuit 1 fan speed (actual)",
        status_key="realFan1Speed",
        convert=_fan_speed,
        needs_zone=CIRCUIT_1_ZONES,
        applies=lambda status, cascade: _has_fan_coils(status),
        device_class=SensorDeviceClass.ENUM,
        options=list(FAN_SPEEDS.values()),
    ),
    UnitSensorDescription(
        key="c2_fan_speed_actual",
        name="Circuit 2 fan speed (actual)",
        status_key="realFan2Speed",
        convert=_fan_speed,
        needs_zone=CIRCUIT_2_ZONES,
        applies=lambda status, cascade: _has_fan_coils(status),
        device_class=SensorDeviceClass.ENUM,
        options=list(FAN_SPEEDS.values()),
    ),
    # R290 units report the flow of the primary water circuit
    UnitSensorDescription(
        key="primary_water_flow",
        name="Primary water flow",
        status_key="primaryFlowR290",
        convert=_positive_hundredths,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Cascade: several units working as one
    UnitSensorDescription(
        key="cascade_units_enabled",
        name="Cascade units enabled",
        status_key="cascadeEnabledUnits",
        convert=_count,
        source="cascade",
        applies=_is_cascade,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    UnitSensorDescription(
        key="cascade_units_working",
        name="Cascade units working",
        status_key="cascadeWorkingUnits",
        convert=_count,
        source="cascade",
        applies=_is_cascade,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    UnitSensorDescription(
        key="cascade_units_required",
        name="Cascade units required",
        status_key="cascadeRequiredUnits",
        convert=_count,
        source="cascade",
        applies=_is_cascade,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def _parts(unit) -> tuple[dict, dict]:
    """Return (heatingStatus, cascadeInfo) of an indoor unit, as dictionaries."""
    if not isinstance(unit, dict):
        return {}, {}
    status = unit.get("heatingStatus")
    cascade = unit.get("cascadeInfo")
    return (status if isinstance(status, dict) else {}), (cascade if isinstance(cascade, dict) else {})


def read_unit_value(unit, description: UnitSensorDescription):
    """Return the value of one sensor from an indoor unit, or None when it does not apply or is not reported."""
    status, cascade = _parts(unit)
    if description.applies is not None and not description.applies(status, cascade):
        return None
    source = cascade if description.source == "cascade" else status
    return description.convert(source.get(description.status_key))


def unit_sensor_descriptions(unit, zone_ids) -> list[UnitSensorDescription]:
    """Return the sensors this unit gets: its circuits' and equipment's, and only what it reports."""
    if not isinstance(unit, dict):
        return []
    return [
        description
        for description in UNIT_SENSOR_DESCRIPTIONS
        if (description.needs_zone is None or zone_ids & description.needs_zone) and read_unit_value(unit, description) is not None
    ]


class CSNetHomeUnitSensor(CoordinatorEntity, SensorEntity):
    """One more reading of the unit."""

    _attr_has_entity_name = True
    entity_description: UnitSensorDescription

    def __init__(self, coordinator, description: UnitSensorDescription, device_info, read_unit) -> None:
        """Initialize the sensor; ``read_unit`` returns the indoor unit of the last poll."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-unit-{description.key}"
        self._attr_device_info = device_info
        self._read_unit = read_unit

    @property
    def native_value(self):
        """Return the reading, or None when the unit does not report it right now."""
        return read_unit_value(self._read_unit(), self.entity_description)
