"""Dashboard cards: the roles the websocket command gives, and how the card file is served."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import CONF_CARD_LANGUAGE, CONF_ENERGY_METER, DOMAIN
from custom_components.csnet_home.dashboard import CARDS_FILE, FRONTEND_DIR, FRONTEND_URL, async_register_dashboard, dashboard_entities

FRONTEND_FILE = FRONTEND_DIR / CARDS_FILE


def _add(registry, domain, unique_id, entity_id, disabled=False):
    """Register one integration entity under a chosen entity id."""
    object_id = entity_id.split(".", 1)[1]
    entry = registry.async_get_or_create(domain, DOMAIN, unique_id, suggested_object_id=object_id)
    if disabled:
        registry.async_update_entity(entry.entity_id, disabled_by=er.RegistryEntryDisabler.USER)
    return entry.entity_id


async def test_roles_follow_unique_ids_not_entity_ids(hass: HomeAssistant):
    """Renamed entities are still found; disabled ones and other integrations are left out."""
    registry = er.async_get(hass)
    power = _add(registry, "sensor", f"{DOMAIN}-installation-instant_consumption", "sensor.my_renamed_power")
    _add(registry, "sensor", f"{DOMAIN}-installation-out_water_temperature", "sensor.depart")
    _add(registry, "binary_sensor", f"{DOMAIN}-binary-defrost", "binary_sensor.degivrage", disabled=True)
    registry.async_get_or_create("sensor", "other_integration", f"{DOMAIN}-installation-water_flow")

    roles = dashboard_entities(hass)
    assert roles["unit"] == {"power": power, "water_out": "sensor.depart"}
    assert roles["circuits"] == []
    assert roles["dhw"] is None
    assert roles["pool"] is None


async def test_circuits_tank_and_gateway(hass: HomeAssistant):
    """Each circuit gets its climate, demand, curve; zone 3 is the tank; the gateway sensors come from a zone."""
    registry = er.async_get(hass)
    c1 = _add(registry, "climate", f"{DOMAIN}-climate-11-21-1", "climate.etage")
    c2 = _add(registry, "climate", f"{DOMAIN}-climate-11-22-6", "climate.plancher")
    _add(registry, "sensor", f"{DOMAIN}-zone-11-21-1-current_temperature", "sensor.etage_temp")
    _add(registry, "binary_sensor", f"{DOMAIN}-binary-circuit_1_demand", "binary_sensor.c1_demand")
    _add(registry, "sensor", f"{DOMAIN}-unit-c2_heating_curve_water_temperature", "sensor.c2_curve")
    _add(registry, "sensor", f"{DOMAIN}-zone-11-21-1-connectivity", "sensor.gw_conn")
    tank = _add(registry, "water_heater", f"{DOMAIN}-water-heater-11-23-3", "water_heater.ecs")
    _add(registry, "binary_sensor", f"{DOMAIN}-binary-dhw_heater", "binary_sensor.ecs_heating")

    roles = dashboard_entities(hass)
    assert roles["circuits"] == [
        {"circuit": 1, "zone_id": 1, "water_control": False, "climate": c1, "current_temperature": "sensor.etage_temp", "demand": "binary_sensor.c1_demand"},
        {"circuit": 2, "zone_id": 6, "water_control": True, "climate": c2, "current_temperature": None, "curve": "sensor.c2_curve"},
    ]
    assert roles["dhw"] == {"water_heater": tank, "heating": "binary_sensor.ecs_heating"}
    assert roles["gateway"] == {"connectivity": "sensor.gw_conn"}


async def test_websocket_command_answers_the_roles(hass: HomeAssistant, hass_ws_client):
    """The cards ask ``csnet_home/dashboard``."""
    await async_register_dashboard(hass, "9.9.9")
    _add(er.async_get(hass), "sensor", f"{DOMAIN}-installation-set_water_temperature", "sensor.target")
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/dashboard"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["unit"] == {"water_target": "sensor.target"}


async def test_card_file_is_served_and_loaded_with_the_version(hass: HomeAssistant):
    """The file is served from the integration and loaded in every browser, once."""
    hass.config.components.add("frontend")
    hass.http = MagicMock(async_register_static_paths=AsyncMock())
    with patch("homeassistant.components.frontend.add_extra_js_url") as add_js:
        await async_register_dashboard(hass, "2.14.0")
        await async_register_dashboard(hass, "2.14.0")
    hass.http.async_register_static_paths.assert_awaited_once()
    config = hass.http.async_register_static_paths.await_args.args[0][0]
    assert config.url_path == FRONTEND_URL
    assert Path(config.path) == FRONTEND_DIR
    add_js.assert_called_once_with(hass, f"{FRONTEND_URL}/{CARDS_FILE}?v=2.14.0")


async def test_no_frontend_no_files(hass: HomeAssistant):
    """Without the frontend (tests, headless installs) only the websocket command is registered."""
    hass.http = MagicMock(async_register_static_paths=AsyncMock())
    with patch("homeassistant.components.frontend.add_extra_js_url") as add_js:
        await async_register_dashboard(hass, "2.14.0")
    hass.http.async_register_static_paths.assert_not_awaited()
    add_js.assert_not_called()


def test_card_file_ships_every_card_and_language():
    """Every card listed for the picker, and the same texts in English, French and Spanish."""
    source = FRONTEND_FILE.read_text(encoding="utf-8")
    for tag in (
        "csnet-heat-pump-card",
        "csnet-water-circuit-card",
        "csnet-heating-curve-card",
        "csnet-performance-card",
        "csnet-system-health-card",
        "csnet-refrigerant-card",
        "csnet-temperatures-card",
        "csnet-activity-card",
        "csnet-daily-energy-card",
        "csnet-power-profile-card",
        "csnet-energy-signature-card",
    ):
        assert f'"{tag}"' in source
    texts = source[source.index("const TEXTS = {") : source.index("function lang(")]
    blocks = {}
    for language in ("en", "fr", "es"):
        start = texts.index(f"  {language}: {{")
        end = texts.index("\n  },", start)
        blocks[language] = {line.strip().split(":", 1)[0] for line in texts[start:end].splitlines()[1:] if ":" in line}
    assert blocks["en"] == blocks["fr"] == blocks["es"]


def test_manifest_loads_after_the_frontend():
    """The frontend is set up first when it is there, without being required."""
    manifest = json.loads((FRONTEND_DIR.parent / "manifest.json").read_text(encoding="utf-8"))
    assert {"frontend", "http"} <= set(manifest["after_dependencies"])
    assert manifest["dependencies"] == []


async def test_meter_and_its_power_sensor(hass: HomeAssistant):
    """The meter chosen in the settings, and the power sensor beside it on the same device, become roles."""
    other_entry = MockConfigEntry(domain="shelly")
    other_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(config_entry_id=other_entry.entry_id, identifiers={("shelly", "meter")})
    registry = er.async_get(hass)

    def meter_entity(object_id, device_class):
        return registry.async_get_or_create(
            "sensor", "shelly", object_id, suggested_object_id=object_id, device_id=device.id, original_device_class=device_class
        ).entity_id

    energy = meter_entity("shelly_total_active_energy", "energy")
    meter_entity("shelly_phase_a_active_power", "power")
    power = meter_entity("shelly_total_active_power", "power")
    MockConfigEntry(domain=DOMAIN, data={CONF_ENERGY_METER: energy}).add_to_hass(hass)

    unit = dashboard_entities(hass)["unit"]
    assert unit["meter_energy"] == energy
    assert unit["meter_power"] == power


async def test_meter_power_is_chosen_by_shared_words(hass: HomeAssistant):
    """Same start for every sensor: the one sharing a word with the meter wins, not the last alphabetically."""
    other_entry = MockConfigEntry(domain="other")
    other_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(config_entry_id=other_entry.entry_id, identifiers={("other", "unit")})
    registry = er.async_get(hass)
    for object_id, device_class in (("unit_daily_consumption", "energy"), ("unit_instant_consumption", "power"), ("unit_output_power", "power")):
        registry.async_get_or_create("sensor", "other", object_id, suggested_object_id=object_id, device_id=device.id, original_device_class=device_class)
    MockConfigEntry(domain=DOMAIN, data={CONF_ENERGY_METER: "sensor.unit_daily_consumption"}).add_to_hass(hass)
    assert dashboard_entities(hass)["unit"]["meter_power"] == "sensor.unit_instant_consumption"


async def test_meter_without_device_or_power_sensor(hass: HomeAssistant):
    """A meter alone (a template sensor, for example) gives only the energy role."""
    MockConfigEntry(domain=DOMAIN, data={CONF_ENERGY_METER: "sensor.template_energy"}).add_to_hass(hass)
    unit = dashboard_entities(hass)["unit"]
    assert unit == {"meter_energy": "sensor.template_energy"}


async def test_no_meter_no_meter_roles(hass: HomeAssistant):
    """Without a meter in the settings nothing is added."""
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    assert dashboard_entities(hass)["unit"] == {}


async def test_card_language_from_the_settings(hass: HomeAssistant):
    """A language chosen for the cards reaches them; "auto" (the default) leaves each user's profile language."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_CARD_LANGUAGE: "fr"})
    entry.add_to_hass(hass)
    assert dashboard_entities(hass)["language"] == "fr"
    hass.config_entries.async_update_entry(entry, data={CONF_CARD_LANGUAGE: "auto"})
    assert "language" not in dashboard_entities(hass)
    hass.config_entries.async_update_entry(entry, data={})
    assert "language" not in dashboard_entities(hass)


def test_card_editor_offers_a_language():
    """Every card editor ends with the language choice, in the languages the cards speak."""
    source = FRONTEND_FILE.read_text(encoding="utf-8")
    assert "editor.schema = [...this.editorSchema(), LANGUAGE_FIELD];" in source
    field = source[source.index("const LANGUAGE_FIELD = {") : source.index("class CsnetCardEditor")]
    for code in ("auto", "en", "fr", "es"):
        assert f'value: "{code}"' in field


def test_statistics_stop_at_the_end_asked():
    """Home Assistant also answers the row that starts at the end time; the cards drop it.

    Without this, "yesterday" (days up to midnight) also counted today.
    """
    source = FRONTEND_FILE.read_text(encoding="utf-8")
    helper = source[source.index("async function statistics(") : source.index("async function onPeriods(")]
    assert ".filter((row) => row.start < endMs)" in helper


def test_numbers_and_dates_follow_the_card_language():
    """Numbers use the card's language unless the profile chose a number format; dates and times follow the card's language."""
    source = FRONTEND_FILE.read_text(encoding="utf-8")
    fmt = source[source.index("function fmt(") : source.index("function maybeNumber(")]
    assert "numberLocale(hass)" in fmt
    locale = source[source.index("function numberLocale(") : source.index("function fmt(")]
    assert 'format === "system"' in locale and "NUMBER_FORMATS[format]" in locale and "textLocale(hass)" in locale
    for helper in ("function hourLabel(", "function dayLabel("):
        body = source[source.index(helper) : source.index("}", source.index(helper))]
        assert "textLocale(hass)" in body
    assert "hass.locale?.language || undefined" not in source
