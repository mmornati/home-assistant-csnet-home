"""Binary sensors for what the unit is running."""

from types import SimpleNamespace

import pytest
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockEntityPlatform

from custom_components.csnet_home.binary_sensor import BINARY_SENSOR_DESCRIPTIONS, CSNetHomeBinarySensor, _read, async_setup_entry
from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.sensor import SYSTEM_STATUS_FLAG_BITS

# The maintainer's unit while heating both circuits: pumps 1 to 3, compressor, both demands
LIVE_FLAGS = 24636
BY_KEY = {description.key: description for description in BINARY_SENSOR_DESCRIPTIONS}


def _coordinator(heating_status, zone_ids=(1, 2)):
    """Return a coordinator double for one indoor unit with the given status."""
    data = {"status": heating_status}
    return SimpleNamespace(
        data=data,
        get_installation_devices_data=lambda: {"data": [{"indoors": [{"id": 1706, "heatingStatus": data["status"]}]}]} if data["status"] is not None else {},
        get_sensors_data=lambda: [{"zone_id": zone_id} for zone_id in zone_ids],
        get_common_data=lambda: {"firmware": "1.2.3"},
        async_add_listener=lambda *args, **kwargs: lambda: None,
        last_update_success=True,
    )


async def _setup(coordinator, listeners=None):
    """Run the platform setup and return the entities it creates, by key."""
    created = []
    if listeners is not None:
        coordinator.async_add_listener = lambda listener, *args: listeners.append(listener) or (lambda: None)
    entry = SimpleNamespace(runtime_data=SimpleNamespace(coordinator=coordinator), async_on_unload=lambda unsubscribe: None)
    await async_setup_entry(None, entry, created.extend)
    if listeners is not None:
        listeners.append(created)
    return {entity.entity_description.key: entity for entity in created}


def test_every_flag_sensor_uses_a_known_bit():
    """A typo in a flag name would only fail when the sensor is read."""
    for description in BINARY_SENSOR_DESCRIPTIONS:
        assert (description.flag is None) != (description.status_key is None), description.key
        if description.flag is not None:
            assert description.flag in SYSTEM_STATUS_FLAG_BITS, description.key
    assert len(BY_KEY) == len(BINARY_SENSOR_DESCRIPTIONS)


def test_live_flags_decode_as_on_the_unit():
    """24636 = pumps 1 to 3, compressor, circuit 1 and 2 demand; nothing else."""
    status = {"systemStatus2Flags": LIVE_FLAGS, "defrosting": 0}
    on = {key for key, description in BY_KEY.items() if _read(status, description)}
    assert on == {"compressor", "water_pump_1", "water_pump_2", "water_pump_3", "circuit_1_demand", "circuit_2_demand"}


@pytest.mark.parametrize(
    ("bit", "key"),
    [(2, "water_pump_1"), (3, "water_pump_2"), (4, "water_pump_3"), (5, "compressor"), (6, "boiler"), (7, "dhw_heater"), (8, "backup_heater")]
    + [(9, "smart_function_input"), (10, "forced_off"), (11, "dhw_recirculation"), (13, "circuit_1_demand"), (14, "circuit_2_demand")],
)
def test_each_bit_turns_on_exactly_its_sensor(bit, key):
    """Bit numbers are the CSNet web app's."""
    status = {"systemStatus2Flags": 1 << bit, "defrosting": 0}
    assert {k for k, description in BY_KEY.items() if _read(status, description)} == {key}


@pytest.mark.parametrize(("value", "expected"), [(1, True), (2, True), (0, False), (None, None), (-1, None), ("1", None), (True, None)])
def test_defrost_reads_the_defrosting_field(value, expected):
    """Above 0 is defrosting (as the web app reads it), 0 is not, anything else is not a reading."""
    assert _read({"systemStatus2Flags": 0, "defrosting": value}, BY_KEY["defrost"]) is expected


@pytest.mark.parametrize("status", [None, "text", {}, {"systemStatus2Flags": None}, {"systemStatus2Flags": -1}, {"systemStatus2Flags": "24636"}])
def test_missing_or_odd_flags_are_unknown_not_off(status):
    """Without a usable value the sensor is unknown instead of claiming 'off'."""
    assert _read(status, BY_KEY["compressor"]) is None


async def test_setup_on_a_unit_with_two_circuits_and_no_hot_water():
    """The maintainer's unit: no hot water entities; installer equipment is there but disabled."""
    entities = await _setup(_coordinator({"systemStatus2Flags": LIVE_FLAGS, "defrosting": 0}))

    assert set(entities) == {
        "compressor",
        "defrost",
        "water_pump_1",
        "water_pump_2",
        "water_pump_3",
        "circuit_1_demand",
        "circuit_2_demand",
        "backup_heater",
        "boiler",
        "smart_function_input",
        "forced_off",
    }
    disabled = {key for key, entity in entities.items() if not entity.entity_registry_enabled_default}
    assert disabled == {"backup_heater", "boiler", "smart_function_input", "forced_off"}
    assert entities["compressor"].is_on is True
    assert entities["defrost"].is_on is False


@pytest.mark.parametrize(
    ("zone_ids", "present", "absent"),
    [
        ((1,), {"circuit_1_demand"}, {"circuit_2_demand", "dhw_heater", "dhw_recirculation"}),
        ((5, 6), {"circuit_1_demand", "circuit_2_demand"}, {"dhw_heater"}),
        ((1, 3), {"circuit_1_demand", "dhw_heater", "dhw_recirculation"}, {"circuit_2_demand"}),
        ((3,), {"dhw_heater", "dhw_recirculation"}, {"circuit_1_demand", "circuit_2_demand"}),
    ],
)
async def test_circuit_and_hot_water_sensors_follow_the_zones(zone_ids, present, absent):
    """A unit gets the sensors of the circuits and the tank it has."""
    entities = await _setup(_coordinator({"systemStatus2Flags": 0, "defrosting": 0}, zone_ids))
    assert present <= set(entities)
    assert not absent & set(entities)


@pytest.mark.parametrize("status", [None, {}, {"defrosting": 0}])
async def test_nothing_is_created_for_values_the_unit_does_not_report(status):
    """No unit status: nothing. No flags: only what is reported."""
    entities = await _setup(_coordinator(status))
    assert set(entities) == ({"defrost"} if status == {"defrosting": 0} else set())  # no hot water zone: no anti-legionella


async def test_entities_follow_the_polls_and_share_the_units_device(hass):
    """Through a real entity platform: state, ids, disabled defaults and the device."""
    coordinator = _coordinator({"systemStatus2Flags": LIVE_FLAGS, "defrosting": 0, "unitModel": 0})
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    platform = MockEntityPlatform(hass, domain="binary_sensor", platform_name=DOMAIN)
    platform.config_entry = entry
    entities = [CSNetHomeBinarySensor(coordinator, description) for description in BINARY_SENSOR_DESCRIPTIONS]
    await platform.async_add_entities(entities)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.system_controller_compressor").state == "on"
    assert hass.states.get("binary_sensor.system_controller_defrost").state == "off"
    assert hass.states.get("binary_sensor.system_controller_circuit_2_demand").state == "on"
    assert hass.states.get("binary_sensor.system_controller_boiler") is None  # disabled by default

    registry = er.async_get(hass)
    compressor = registry.async_get("binary_sensor.system_controller_compressor")
    assert compressor.unique_id == f"{DOMAIN}-binary-compressor"
    assert registry.async_get("binary_sensor.system_controller_boiler").disabled_by is er.RegistryEntryDisabler.INTEGRATION

    device = dr.async_get(hass).async_get(compressor.device_id)
    assert device.identifiers == {(DOMAIN, "System-Controller")}
    assert device.model == "Yutaki S"
    assert device.sw_version == "1.2.3"

    # the compressor stops: the next poll shows it
    coordinator.data["status"] = {"systemStatus2Flags": 0, "defrosting": 1, "unitModel": 0}
    for entity in entities:
        if entity.enabled:
            entity.async_write_ha_state()
    assert hass.states.get("binary_sensor.system_controller_compressor").state == "off"
    assert hass.states.get("binary_sensor.system_controller_defrost").state == "on"


async def test_sensors_appear_when_the_unit_status_arrives_after_setup():
    """A request that failed during setup does not leave the sensors out until a reload."""
    coordinator = _coordinator(None)
    listeners = []
    assert await _setup(coordinator, listeners) == {}
    listener, created = listeners

    coordinator.data["status"] = {"systemStatus2Flags": LIVE_FLAGS, "defrosting": 0}
    listener()
    assert {entity.entity_description.key for entity in created} >= {"compressor", "defrost", "circuit_1_demand"}

    # later polls add nothing twice
    count = len(created)
    listener()
    listener()
    assert len(created) == count


@pytest.mark.parametrize(("value", "expected"), [(1, True), (2, True), (0, False), (-1, None), (None, None)])
def test_anti_legionella_follows_the_units_status(value, expected):
    """The tank's anti-legionella cycle is running when the unit says so."""
    assert _read({"antiLegionellaStatusDHW": value}, BY_KEY["dhw_anti_legionella"]) is expected


async def test_anti_legionella_only_on_units_with_a_tank():
    """A unit without a hot water zone reports the field too, and gets no entity for it."""
    status = {"systemStatus2Flags": 0, "defrosting": 0, "antiLegionellaStatusDHW": 0}
    assert "dhw_anti_legionella" not in await _setup(_coordinator(status, (1, 2)))
    assert "dhw_anti_legionella" in await _setup(_coordinator(status, (1, 3)))
