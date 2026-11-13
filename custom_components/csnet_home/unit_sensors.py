"""More readings of the unit: eco offsets, board software.

Each sensor is created only when the unit reports a real value for it.

The unit status also carries per-zone "wired" and "wireless" thermostat
temperatures. They are not exposed: on a unit with two circuits the
"wireless" value of one zone mirrors the other zone's, so what each field
means could not be established.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

CIRCUIT_1_ZONES = frozenset({1, 5})
CIRCUIT_2_ZONES = frozenset({2, 6})


def _degrees(value) -> float | None:
    """Return a whole number of degrees; negative values are "not reported"."""
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        return None
    return float(value)


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
)


def unit_sensor_descriptions(heating_status, zone_ids) -> list[UnitSensorDescription]:
    """Return the sensors this unit gets: its circuits', and only what it reports."""
    if not isinstance(heating_status, dict):
        return []
    return [
        description
        for description in UNIT_SENSOR_DESCRIPTIONS
        if (description.needs_zone is None or zone_ids & description.needs_zone) and description.convert(heating_status.get(description.status_key)) is not None
    ]


class CSNetHomeUnitSensor(CoordinatorEntity, SensorEntity):
    """One more reading of the unit."""

    _attr_has_entity_name = True
    entity_description: UnitSensorDescription

    def __init__(self, coordinator, description: UnitSensorDescription, device_info, read_status) -> None:
        """Initialize the sensor; ``read_status`` returns the unit status of the last poll."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-unit-{description.key}"
        self._attr_device_info = device_info
        self._read_status = read_status

    @property
    def native_value(self):
        """Return the reading, or None when the unit does not report it right now."""
        status = self._read_status()
        if not isinstance(status, dict):
            return None
        return self.entity_description.convert(status.get(self.entity_description.status_key))
