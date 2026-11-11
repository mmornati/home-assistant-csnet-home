"""Test the migration from room-name identifiers to stable zone identifiers."""

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.migration import async_migrate_zone_identifiers

SALON = {"device_name": "Hitachi PAC", "device_id": 1234, "room_id": 395, "zone_id": 5, "room_name": "Salon"}
DHW = {"device_name": "Hitachi PAC", "device_id": 1234, "room_id": 396, "zone_id": 3, "room_name": "DHW"}
KEYS = ["current_temperature", "wifi_signal"]


def _entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)
    return entry


async def test_migrates_zone_entities_and_device(hass):
    """Name-based ids move to zone ids, keeping the entity_ids."""
    entry = _entry(hass)
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_or_create(config_entry_id=entry.entry_id, identifiers={(DOMAIN, "Hitachi PAC-Salon")}, name="Hitachi PAC-Salon")
    climate = ent_reg.async_get_or_create("climate", DOMAIN, "csnet_home-climate-1234-Salon", config_entry=entry, device_id=device.id)
    sensor = ent_reg.async_get_or_create("sensor", DOMAIN, "csnet_home-Salon-current_temperature", config_entry=entry, device_id=device.id)
    heater = ent_reg.async_get_or_create("water_heater", DOMAIN, "csnet_home-water-heater-DHW", config_entry=entry)
    other = ent_reg.async_get_or_create("sensor", DOMAIN, "csnet_home-installation-water_flow", config_entry=entry)

    async_migrate_zone_identifiers(hass, entry, [SALON, DHW], KEYS)

    assert ent_reg.async_get(climate.entity_id).unique_id == "csnet_home-climate-1234-395-5"
    assert ent_reg.async_get(sensor.entity_id).unique_id == "csnet_home-zone-1234-395-5-current_temperature"
    assert ent_reg.async_get(heater.entity_id).unique_id == "csnet_home-water-heater-1234-396-3"
    assert ent_reg.async_get(other.entity_id).unique_id == "csnet_home-installation-water_flow"
    assert dev_reg.async_get(device.id).identifiers == {(DOMAIN, "zone-1234-395-5")}


async def test_skips_room_names_shared_by_several_zones(hass):
    """A legacy id shared by two zones cannot be attributed to either."""
    entry = _entry(hass)
    ent_reg = er.async_get(hass)
    climate = ent_reg.async_get_or_create("climate", DOMAIN, "csnet_home-climate-1234-Salon", config_entry=entry)
    twin = dict(SALON, room_id=397, zone_id=1)

    async_migrate_zone_identifiers(hass, entry, [SALON, twin], KEYS)

    assert ent_reg.async_get(climate.entity_id).unique_id == "csnet_home-climate-1234-Salon"


async def test_leaves_rooms_renamed_before_migration(hass):
    """An id whose room name no longer exists in CSNet is left untouched."""
    entry = _entry(hass)
    ent_reg = er.async_get(hass)
    climate = ent_reg.async_get_or_create("climate", DOMAIN, "csnet_home-climate-1234-Bibliotheque", config_entry=entry)

    async_migrate_zone_identifiers(hass, entry, [SALON], KEYS)

    assert ent_reg.async_get(climate.entity_id).unique_id == "csnet_home-climate-1234-Bibliotheque"


async def test_does_not_overwrite_an_existing_zone_id(hass):
    """If the zone id is already registered, the legacy entity is not renamed onto it."""
    entry = _entry(hass)
    ent_reg = er.async_get(hass)
    legacy = ent_reg.async_get_or_create("climate", DOMAIN, "csnet_home-climate-1234-Salon", config_entry=entry)
    current = ent_reg.async_get_or_create("climate", DOMAIN, "csnet_home-climate-1234-395-5", config_entry=entry)

    async_migrate_zone_identifiers(hass, entry, [SALON], KEYS)

    assert ent_reg.async_get(legacy.entity_id).unique_id == "csnet_home-climate-1234-Salon"
    assert ent_reg.async_get(current.entity_id).unique_id == "csnet_home-climate-1234-395-5"


async def test_migration_is_idempotent(hass):
    """Running the migration on every startup changes nothing the second time."""
    entry = _entry(hass)
    ent_reg = er.async_get(hass)
    climate = ent_reg.async_get_or_create("climate", DOMAIN, "csnet_home-climate-1234-Salon", config_entry=entry)

    async_migrate_zone_identifiers(hass, entry, [SALON], KEYS)
    async_migrate_zone_identifiers(hass, entry, [SALON], KEYS)

    assert ent_reg.async_get(climate.entity_id).unique_id == "csnet_home-climate-1234-395-5"


def test_entry_device_prefers_per_entry_lookup():
    """On HA 2026.11+ the device is looked up per config entry, without the deprecated call."""
    from types import SimpleNamespace

    from custom_components.csnet_home.migration import _entry_device

    calls = []
    registry = SimpleNamespace(
        async_get_device_by_identifier=lambda identifier, entry_id: calls.append((identifier, entry_id)) or "device",
        async_get_device=lambda **kwargs: (_ for _ in ()).throw(AssertionError("deprecated call")),
    )

    assert _entry_device(registry, (DOMAIN, "zone-1-2-3"), "entry") == "device"
    assert calls == [((DOMAIN, "zone-1-2-3"), "entry")]
