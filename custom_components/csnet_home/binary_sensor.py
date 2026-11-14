"""Binary sensors for what the unit is running right now.

They decode ``heatingStatus.systemStatus2Flags`` the way the CSNet web app
does, plus the defrost state, and sit on the same device as the unit's
other sensors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CSNetHomeConfigEntry, CSNetHomeCoordinator
from .sensor import SYSTEM_STATUS_FLAG_BITS, _get_heating_status_from_installation_data, unit_device_info

_LOGGER = logging.getLogger(__name__)

# Binary sensors only read what the coordinator fetched
PARALLEL_UPDATES = 0

# Zone ids of the two circuits (room control, water control) and of the hot water tank
CIRCUIT_1_ZONES = frozenset({1, 5})
CIRCUIT_2_ZONES = frozenset({2, 6})
DHW_ZONES = frozenset({3})


@dataclass(frozen=True, kw_only=True)
class CSNetHomeBinarySensorDescription(BinarySensorEntityDescription):
    """A binary sensor read from the unit status.

    ``flag`` names a bit of systemStatus2Flags; without it the sensor reads
    ``status_key`` (1 means on). ``needs_zone`` limits the sensor to units
    that have one of these zones.
    """

    flag: str | None = None
    status_key: str | None = None
    needs_zone: frozenset[int] | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[CSNetHomeBinarySensorDescription, ...] = (
    CSNetHomeBinarySensorDescription(key="compressor", name="Compressor", device_class=BinarySensorDeviceClass.RUNNING, flag="compressor_on"),
    CSNetHomeBinarySensorDescription(key="defrost", name="Defrost", device_class=BinarySensorDeviceClass.RUNNING, status_key="defrosting"),
    CSNetHomeBinarySensorDescription(key="water_pump_1", name="Water pump 1", device_class=BinarySensorDeviceClass.RUNNING, flag="water_pump_1"),
    CSNetHomeBinarySensorDescription(key="water_pump_2", name="Water pump 2", device_class=BinarySensorDeviceClass.RUNNING, flag="water_pump_2"),
    CSNetHomeBinarySensorDescription(key="water_pump_3", name="Water pump 3", device_class=BinarySensorDeviceClass.RUNNING, flag="water_pump_3"),
    CSNetHomeBinarySensorDescription(key="circuit_1_demand", name="Circuit 1 demand", flag="c1_demand", needs_zone=CIRCUIT_1_ZONES),
    CSNetHomeBinarySensorDescription(key="circuit_2_demand", name="Circuit 2 demand", flag="c2_demand", needs_zone=CIRCUIT_2_ZONES),
    CSNetHomeBinarySensorDescription(
        key="dhw_heater",
        name="DHW electric heater",
        device_class=BinarySensorDeviceClass.RUNNING,
        flag="dhw_heater_on",
        needs_zone=DHW_ZONES,
    ),
    CSNetHomeBinarySensorDescription(
        key="dhw_recirculation",
        name="DHW recirculation",
        device_class=BinarySensorDeviceClass.RUNNING,
        flag="dhw_recirculation",
        needs_zone=DHW_ZONES,
    ),
    # Equipment an installer may or may not have fitted, which the unit does
    # not announce: there for who has it, not shown to everyone
    CSNetHomeBinarySensorDescription(
        key="backup_heater",
        name="Backup heater",
        device_class=BinarySensorDeviceClass.RUNNING,
        flag="space_heater_on",
        entity_registry_enabled_default=False,
    ),
    CSNetHomeBinarySensorDescription(
        key="boiler",
        name="Boiler",
        device_class=BinarySensorDeviceClass.RUNNING,
        flag="boiler_on",
        entity_registry_enabled_default=False,
    ),
    CSNetHomeBinarySensorDescription(
        key="smart_function_input",
        name="Smart function input",
        flag="smart_function_input",
        entity_registry_enabled_default=False,
    ),
    CSNetHomeBinarySensorDescription(key="forced_off", name="Forced off", flag="forced_off", entity_registry_enabled_default=False),
)


def _read(heating_status, description: CSNetHomeBinarySensorDescription) -> bool | None:
    """Return the state of one binary sensor, or None when the unit does not report it."""
    if not isinstance(heating_status, dict):
        return None
    if description.flag is not None:
        flags = heating_status.get("systemStatus2Flags")
        if not isinstance(flags, int) or isinstance(flags, bool) or flags < 0:
            return None
        return bool(flags & (1 << SYSTEM_STATUS_FLAG_BITS[description.flag]))
    value = heating_status.get(description.status_key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return None
    return value == 1


async def async_setup_entry(hass: HomeAssistant, entry: CSNetHomeConfigEntry, async_add_entities) -> None:
    """Set up the binary sensors of the unit."""
    coordinator = entry.runtime_data.coordinator
    created: set[str] = set()

    @callback
    def _add_reported() -> None:
        """Add the sensors the unit reports a value for and that do not exist yet.

        Runs at setup and after every poll, so a unit status that was missing
        at setup (a failed request) does not leave the sensors out until a reload.
        """
        if len(created) == len(BINARY_SENSOR_DESCRIPTIONS):
            return
        heating_status = _get_heating_status_from_installation_data(coordinator.get_installation_devices_data())
        if not isinstance(heating_status, dict):
            return
        zone_ids = {sensor.get("zone_id") for sensor in coordinator.get_sensors_data()}
        entities = []
        for description in BINARY_SENSOR_DESCRIPTIONS:
            if description.key in created:
                continue
            if description.needs_zone is not None and not zone_ids & description.needs_zone:
                continue
            # a unit that does not report the value gets no entity instead of an unknown one
            if _read(heating_status, description) is None:
                continue
            created.add(description.key)
            entities.append(CSNetHomeBinarySensor(coordinator, description))
        if entities:
            async_add_entities(entities)

    _add_reported()
    entry.async_on_unload(coordinator.async_add_listener(_add_reported))


class CSNetHomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Something the unit is running or asking for right now."""

    _attr_has_entity_name = True
    entity_description: CSNetHomeBinarySensorDescription

    def __init__(self, coordinator: CSNetHomeCoordinator, description: CSNetHomeBinarySensorDescription) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-binary-{description.key}"

    def _heating_status(self):
        """Return the unit status of the last poll."""
        return _get_heating_status_from_installation_data(self.coordinator.get_installation_devices_data())

    @property
    def is_on(self) -> bool | None:
        """Return True when the unit reports this as running or active."""
        return _read(self._heating_status(), self.entity_description)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device of the unit, the one its sensors are on."""
        return unit_device_info(self.coordinator)
