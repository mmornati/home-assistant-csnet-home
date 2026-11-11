"""Compressor sensors the outdoor unit has no hardware for are not created."""

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.sensor import COMPRESSOR_SENSOR_DESCRIPTIONS, _remove_unsupported_compressor_entities, unsupported_compressor_sensor_keys

SECONDARY_KEYS = {d.key for d in COMPRESSOR_SENSOR_DESCRIPTIONS if d.key.startswith("secondary_")}


def _installation(heating_status, second_cycle):
    return {"data": [{"indoors": [{"heatingStatus": heating_status, "secondCycle": second_cycle}]}]}


# Captured from a Yutaki S (unitModel 0) with no suction pressure sensor
YUTAKI_S = _installation(
    {"unitModel": 0, "ouSuctionPress": 128, "ouDischargePress": 18},
    {"dischargeTemp": 0, "suctionTemp": 87, "dischargePressure": 127, "suctionPressure": 127, "teSH": 24},
)


def test_yutaki_s_hides_suction_pressure_and_second_cycle():
    """Placeholder suction pressure and the absent R134a cycle are dropped."""
    assert unsupported_compressor_sensor_keys(YUTAKI_S) == SECONDARY_KEYS | {"suction_pressure", "suction_pressure_correction"}


def test_yutaki_s80_keeps_second_cycle():
    """The S80 has a second refrigerant cycle: its sensors stay."""
    data = _installation({"unitModel": 2, "ouSuctionPress": 9}, {"dischargePressure": 127})
    assert unsupported_compressor_sensor_keys(data) == set()


def test_real_second_cycle_pressure_keeps_second_cycle():
    """A real second-cycle pressure is enough, whatever the unit model code."""
    data = _installation({"unitModel": 0, "ouSuctionPress": 9}, {"dischargePressure": 14})
    assert unsupported_compressor_sensor_keys(data) == set()


def test_real_suction_pressure_is_kept():
    """A unit with a suction sensor keeps it."""
    data = _installation({"unitModel": 0, "ouSuctionPress": 9}, {"dischargePressure": 127})
    assert unsupported_compressor_sensor_keys(data) == SECONDARY_KEYS


async def test_removes_entities_created_by_earlier_versions(hass):
    """Registry entries for unsupported sensors are removed, others kept."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    stale = registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}-compressor-secondary_superheat", config_entry=entry)
    kept = registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}-compressor-discharge_pressure", config_entry=entry)

    _remove_unsupported_compressor_entities(hass, {"secondary_superheat", "suction_pressure"})

    assert registry.async_get(stale.entity_id) is None
    assert registry.async_get(kept.entity_id) is not None
