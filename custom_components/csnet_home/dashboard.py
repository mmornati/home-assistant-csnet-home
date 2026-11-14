"""Dashboard cards shipped with the integration.

The cards are plain JavaScript web components in ``frontend/``: no build step
and no third-party card is needed. Home Assistant serves the file and loads it
in every browser, so the cards appear in the dashboard "Add card" picker.

The cards do not guess entity ids (users rename them, and they depend on the
language). They ask the ``csnet_home/dashboard`` websocket command, which
answers which entity plays which role, found by the entities' unique ids.
"""

from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import CONF_ENERGY_METER, DOMAIN

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = f"/{DOMAIN}_frontend"
CARDS_FILE = "csnet-home-cards.js"
FRONTEND_DIR = Path(__file__).parent / "frontend"
_REGISTERED = f"{DOMAIN}_dashboard_registered"

# Zone ids of CSNet elements
CIRCUIT_ZONES = {1: (1, 5), 2: (2, 6)}
DHW_ZONE = 3
POOL_ZONE = 4

# role -> unique id, for the unit as a whole
UNIT_ROLES = {
    # power and energy, estimated from the unit's readings
    "power": f"{DOMAIN}-installation-instant_consumption",
    "heat_power": f"{DOMAIN}-installation-heating_power",
    "cop_now": f"{DOMAIN}-installation-instant_cop",
    "energy_today": f"{DOMAIN}-installation-daily_consumption",
    "heat_today": f"{DOMAIN}-installation-daily_heating",
    "cop_today_estimated": f"{DOMAIN}-installation-daily_cop_hvac",
    # energy the CSNet server recorded, and the COP from the user's own meter
    "server_heat_today": f"{DOMAIN}-server_heat_today",
    "server_heat_yesterday": f"{DOMAIN}-server_heat_yesterday",
    "server_heat_month": f"{DOMAIN}-server_heat_month",
    "server_electricity_today": f"{DOMAIN}-server_electricity_today",
    "server_electricity_yesterday": f"{DOMAIN}-server_electricity_yesterday",
    "server_electricity_month": f"{DOMAIN}-server_electricity_month",
    "cop_today": f"{DOMAIN}-metered_cop_today",
    "cop_yesterday": f"{DOMAIN}-metered_cop_yesterday",
    "cop_month": f"{DOMAIN}-metered_cop_month",
    "cop_last_month": f"{DOMAIN}-metered_cop_last_month",
    # water side
    "water_out": f"{DOMAIN}-installation-out_water_temperature",
    "water_in": f"{DOMAIN}-installation-in_water_temperature",
    "water_target": f"{DOMAIN}-installation-set_water_temperature",
    "water_c2": f"{DOMAIN}-installation-c2_water_temperature",
    "water_flow": f"{DOMAIN}-installation-water_flow",
    "water_pressure": f"{DOMAIN}-installation-water_pressure",
    "mix_valve": f"{DOMAIN}-installation-mix_valve_position",
    "pump_speed": f"{DOMAIN}-installation-pump_speed",
    "outdoor": f"{DOMAIN}-installation-external_temperature",
    "outdoor_average": f"{DOMAIN}-installation-mean_external_temperature",
    # what runs
    "operation_status": f"{DOMAIN}-compressor-operation_status",
    "compressor": f"{DOMAIN}-binary-compressor",
    "defrost": f"{DOMAIN}-binary-defrost",
    "pump_1": f"{DOMAIN}-binary-water_pump_1",
    "pump_2": f"{DOMAIN}-binary-water_pump_2",
    "pump_3": f"{DOMAIN}-binary-water_pump_3",
    "backup_heater": f"{DOMAIN}-binary-backup_heater",
    "boiler": f"{DOMAIN}-binary-boiler",
    # refrigerant circuit
    "compressor_frequency": f"{DOMAIN}-compressor-compressor_frequency",
    "compressor_current": f"{DOMAIN}-compressor-compressor_current",
    "discharge_temperature": f"{DOMAIN}-compressor-discharge_temperature",
    "evaporator_temperature": f"{DOMAIN}-compressor-evaporator_temperature",
    "discharge_pressure": f"{DOMAIN}-compressor-discharge_pressure",
    "suction_pressure": f"{DOMAIN}-compressor-suction_pressure",
    "expansion_valve": f"{DOMAIN}-compressor-expansion_valve_opening",
    "outdoor_fan_rpm": f"{DOMAIN}-compressor-outdoor_fan_rpm",
    "gas_temperature": f"{DOMAIN}-installation-gas_temperature",
    "liquid_temperature": f"{DOMAIN}-installation-liquid_temperature",
    # health
    "active_alarms": f"{DOMAIN}-active_alarm_count",
    "alarm_history": f"{DOMAIN}-installation-alarm-history",
    "central_control": f"{DOMAIN}-installation-central_control_enabled",
    "lcd_software": f"{DOMAIN}-installation-lcd_software_version",
    "indoor_board_software": f"{DOMAIN}-unit-indoor_board_software",
}

# role -> unique id, per circuit ("{n}" is the circuit number)
CIRCUIT_ROLES = {
    "demand": f"{DOMAIN}-binary-circuit_{{n}}_demand",
    "curve": f"{DOMAIN}-unit-c{{n}}_heating_curve_water_temperature",
    "curve_type": f"{DOMAIN}-installation-otc_heating_type_c{{n}}",
    "eco_offset": f"{DOMAIN}-unit-c{{n}}_eco_offset_heating",
}

# role -> unique id, for the hot water tank
DHW_ROLES = {
    "heating": f"{DOMAIN}-binary-dhw_heater",
    "mode": f"{DOMAIN}-unit-dhw_mode",
    "anti_legionella": f"{DOMAIN}-binary-dhw_anti_legionella",
}

# role -> zone sensor key, for the zone of the first circuit (the gateway is the same for all)
GATEWAY_ROLES = {"connectivity": "connectivity", "last_communication": "last_communication", "wifi_signal": "wifi_signal"}


def _zone_of(unique_id: str, prefix: str) -> tuple[str, int] | None:
    """Return (zone key, zone id) from a unique id built as ``{prefix}{device}-{room}-{zone}``."""
    if not unique_id.startswith(prefix):
        return None
    zone_key = unique_id[len(prefix) :]
    try:
        return zone_key, int(zone_key.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return None


def _meter_roles(hass: HomeAssistant, registry: er.EntityRegistry) -> dict[str, str]:
    """Return the electricity meter the user chose in the settings, and the power sensor of the same device.

    Meters (a smart plug, a DIN-rail meter) report energy and power side by side:
    the power sensor whose entity id shares the most words with the meter's
    ("total_active_energy" / "total_active_power") measures the same thing.
    """
    entries = hass.config_entries.async_entries(DOMAIN)
    meter = entries[0].data.get(CONF_ENERGY_METER) if entries else None
    if not meter:
        return {}
    roles = {"meter_energy": meter}
    meter_entry = registry.async_get(meter)
    if not meter_entry or not meter_entry.device_id:
        return roles

    meter_words = set(meter.split(".", 1)[-1].split("_"))

    def likeness(entity_id: str) -> tuple[int, int]:
        """Words shared with the meter's entity id, then the length of the shared start."""
        words = set(entity_id.split(".", 1)[-1].split("_"))
        start = 0
        for a, b in zip(entity_id, meter):
            if a != b:
                break
            start += 1
        return len(words & meter_words), start

    candidates = [
        entry.entity_id
        for entry in registry.entities.values()
        if entry.device_id == meter_entry.device_id
        and entry.domain == "sensor"
        and entry.disabled_by is None
        and (entry.device_class or entry.original_device_class) == "power"
    ]
    if candidates:
        roles["meter_power"] = max(candidates, key=lambda entity_id: (*likeness(entity_id), entity_id))
    return roles


@callback
def dashboard_entities(hass: HomeAssistant) -> dict:
    """Return which entity plays which role, for the cards. Disabled entities are left out."""
    registry = er.async_get(hass)
    by_unique_id = {entry.unique_id: entry.entity_id for entry in registry.entities.values() if entry.platform == DOMAIN and entry.disabled_by is None}

    def found(roles: dict[str, str], **fmt) -> dict[str, str]:
        result = {}
        for role, unique_id in roles.items():
            entity_id = by_unique_id.get(unique_id.format(**fmt) if fmt else unique_id)
            if entity_id:
                result[role] = entity_id
        return result

    zones: dict[int, tuple[str, str]] = {}  # zone id -> (zone key, climate entity id)
    water_heaters: dict[int, str] = {}
    for unique_id, entity_id in by_unique_id.items():
        zone = _zone_of(unique_id, f"{DOMAIN}-climate-")
        if zone:
            zones.setdefault(zone[1], (zone[0], entity_id))
            continue
        for kind, zone_id in (("water-heater", DHW_ZONE), ("swimming-pool", POOL_ZONE)):
            zone = _zone_of(unique_id, f"{DOMAIN}-{kind}-")
            if zone and zone[1] == zone_id:
                water_heaters.setdefault(zone_id, entity_id)

    circuits = []
    for circuit, zone_ids in CIRCUIT_ZONES.items():
        zone_id = next((z for z in zone_ids if z in zones), None)
        if zone_id is None:
            continue
        zone_key, climate = zones[zone_id]
        circuits.append(
            {
                "circuit": circuit,
                "zone_id": zone_id,
                # 5/6: the circuit is controlled on its water temperature, not on a room
                "water_control": zone_id in (5, 6),
                "climate": climate,
                "current_temperature": by_unique_id.get(f"{DOMAIN}-zone-{zone_key}-current_temperature"),
                **found(CIRCUIT_ROLES, n=circuit),
            }
        )

    gateway = {}
    for zone_key, _ in zones.values():
        gateway = {
            role: by_unique_id[f"{DOMAIN}-zone-{zone_key}-{key}"] for role, key in GATEWAY_ROLES.items() if f"{DOMAIN}-zone-{zone_key}-{key}" in by_unique_id
        }
        if gateway:
            break

    dhw = None
    if DHW_ZONE in water_heaters:
        dhw = {"water_heater": water_heaters[DHW_ZONE], **found(DHW_ROLES)}

    return {
        "unit": {**found(UNIT_ROLES), **_meter_roles(hass, registry)},
        "circuits": circuits,
        "dhw": dhw,
        "pool": {"water_heater": water_heaters[POOL_ZONE]} if POOL_ZONE in water_heaters else None,
        "gateway": gateway,
    }


async def async_register_dashboard(hass: HomeAssistant, version: str) -> None:
    """Serve the cards, load them in the browsers and register the websocket command; once per start."""
    if hass.data.get(_REGISTERED):
        return
    hass.data[_REGISTERED] = True

    # imported here: these components are only needed when the frontend runs
    from homeassistant.components import websocket_api  # pylint: disable=import-outside-toplevel

    @websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/dashboard"})
    @callback
    def ws_dashboard(hass: HomeAssistant, connection, msg) -> None:
        connection.send_result(msg["id"], dashboard_entities(hass))

    websocket_api.async_register_command(hass, ws_dashboard)

    if "frontend" not in hass.config.components or not hasattr(hass, "http") or hass.http is None:
        _LOGGER.debug("No frontend: the dashboard cards are not served")
        return
    from homeassistant.components.frontend import add_extra_js_url  # pylint: disable=import-outside-toplevel
    from homeassistant.components.http import StaticPathConfig  # pylint: disable=import-outside-toplevel

    await hass.http.async_register_static_paths([StaticPathConfig(FRONTEND_URL, str(FRONTEND_DIR), True)])
    # the version makes browsers fetch the new file after an update
    add_extra_js_url(hass, f"{FRONTEND_URL}/{CARDS_FILE}?v={version}")
