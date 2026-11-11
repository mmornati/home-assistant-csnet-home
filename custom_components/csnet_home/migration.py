"""Registry migration from room-name identifiers to stable zone identifiers.

Before 2.11 the zone entities and devices were identified by the CSNet room
name, so renaming a room in CSNet Manager orphaned them and created new ones.
They are now identified by the zone's (device, room id, element type). This
module rewrites the old name-based identifiers in place, keeping each entity's
entity_id, history and customisations.

Only identifiers whose room name still exists in CSNet can be mapped: a room
renamed before this migration ran can no longer be matched to its zone.
"""

import logging
from collections import Counter

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .helpers import legacy_zone_device_identifier, zone_device_identifier, zone_key

_LOGGER = logging.getLogger(__name__)


def _legacy_unique_ids(sensor_data, sensor_keys):
    """Yield (platform, old unique_id, new unique_id) for one zone."""
    room_name = sensor_data.get("room_name", "unknown")
    key = zone_key(sensor_data)

    yield (
        "climate",
        f"{DOMAIN}-climate-{sensor_data.get('device_id')}-{room_name}",
        f"{DOMAIN}-climate-{key}",
    )

    entity_type = {3: "water-heater", 4: "swimming-pool"}.get(sensor_data.get("zone_id"))
    if entity_type:
        yield (
            "water_heater",
            f"{DOMAIN}-{entity_type}-{room_name}",
            f"{DOMAIN}-{entity_type}-{key}",
        )

    for sensor_key in sensor_keys:
        yield (
            "sensor",
            f"{DOMAIN}-{room_name}-{sensor_key}",
            f"{DOMAIN}-zone-{key}-{sensor_key}",
        )


def async_migrate_zone_identifiers(hass: HomeAssistant, entry: ConfigEntry, sensors_data, sensor_keys) -> None:
    """Move zone entities and devices from room-name to stable zone identifiers."""
    # Two zones sharing a room name had colliding legacy identifiers: there is
    # no way to tell which zone such an identifier belonged to, so skip them.
    name_counts = Counter(s.get("room_name") for s in sensors_data)
    zones = [s for s in sensors_data if name_counts[s.get("room_name")] == 1]

    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    for sensor_data in zones:
        for platform, old_id, new_id in _legacy_unique_ids(sensor_data, sensor_keys):
            entity_id = entity_registry.async_get_entity_id(platform, DOMAIN, old_id)
            if entity_id is None:
                continue
            if entity_registry.async_get_entity_id(platform, DOMAIN, new_id):
                _LOGGER.debug("Not migrating %s: %s is already registered", entity_id, new_id)
                continue
            entity_registry.async_update_entity(entity_id, new_unique_id=new_id)
            _LOGGER.info("Migrated %s unique_id %s -> %s", entity_id, old_id, new_id)

        old_device = device_registry.async_get_device(identifiers={(DOMAIN, legacy_zone_device_identifier(sensor_data))})
        new_identifier = (DOMAIN, zone_device_identifier(sensor_data))
        if old_device is None or entry.entry_id not in old_device.config_entries:
            continue
        if device_registry.async_get_device(identifiers={new_identifier}):
            continue
        device_registry.async_update_device(old_device.id, new_identifiers={new_identifier})
        _LOGGER.info("Migrated device %s to identifier %s", old_device.name, new_identifier[1])
