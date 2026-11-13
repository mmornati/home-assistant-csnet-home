"""How sensors and the unit's device are presented: diagnostic category, model name."""

from types import SimpleNamespace

import pytest
from homeassistant.const import EntityCategory

from custom_components.csnet_home import sensor as sensor_module
from custom_components.csnet_home.sensor import (
    COMPRESSOR_SENSOR_DESCRIPTIONS,
    DEVICE_SENSOR_DESCRIPTIONS,
    DIAGNOSTIC_SENSOR_KEYS,
    INSTALLATION_SENSOR_DESCRIPTIONS,
    UNIT_MODEL_NAMES,
    ZONE_SENSOR_DESCRIPTIONS,
    CSNetHomeInstallationSensor,
    _apply_description_attrs,
)

ALL_DESCRIPTIONS = (
    *ZONE_SENSOR_DESCRIPTIONS,
    *DEVICE_SENSOR_DESCRIPTIONS,
    *INSTALLATION_SENSOR_DESCRIPTIONS,
    *COMPRESSOR_SENSOR_DESCRIPTIONS,
    *sensor_module.CALCULATED_SENSOR_DESCRIPTIONS.values(),
    *sensor_module.DAILY_SENSOR_DESCRIPTIONS.values(),
)

# What a user watches or automates on: these must never be filed under "Diagnostic"
MEASUREMENTS = {
    "current_temperature",
    "setting_temperature",
    "mode",
    "on_off",
    "alarm_code",
    "alarm_active",
    "alarm_message",
    "water_flow",
    "water_pressure",
    "in_water_temperature",
    "out_water_temperature",
    "external_temperature",
    "defrost",
    "compressor_frequency",
    "compressor_current",
    "operation_status",
    "instant_consumption",
    "heating_power",
    "instant_cop",
    "daily_consumption",
    "daily_heating",
    "daily_cop_hvac",
    "daily_cop_dhw",
}


def test_every_diagnostic_key_is_a_real_sensor():
    """A typo in the list would silently leave a sensor uncategorised."""
    assert DIAGNOSTIC_SENSOR_KEYS <= {description.key for description in ALL_DESCRIPTIONS}


def test_measurements_are_not_diagnostic():
    """Temperatures, power, energy, COP, state and alarms stay ordinary sensors."""
    assert not DIAGNOSTIC_SENSOR_KEYS & MEASUREMENTS


@pytest.mark.parametrize("description", ALL_DESCRIPTIONS, ids=lambda description: description.key)
def test_category_is_applied_from_the_list(description):
    """Every sensor class applies its description through the same helper."""
    entity = SimpleNamespace()
    _apply_description_attrs(entity, description)

    if description.key in DIAGNOSTIC_SENSOR_KEYS:
        assert entity._attr_entity_category is EntityCategory.DIAGNOSTIC
    else:
        assert not hasattr(entity, "_attr_entity_category")


def _installation_sensor(heating_status):
    """Build an installation sensor on a unit with the given status."""
    installation = {"data": [{"indoors": [{"id": 1706, "heatingStatus": heating_status}]}]} if heating_status is not None else {}
    coordinator = SimpleNamespace(
        get_installation_devices_data=lambda: installation,
        get_common_data=lambda: {"firmware": "1.0"},
        async_add_listener=lambda *args, **kwargs: lambda: None,
        last_update_success=True,
    )
    description = next(d for d in INSTALLATION_SENSOR_DESCRIPTIONS if d.key == "unit_model")
    device_data = {"device_name": "System", "room_name": "Controller", "device_id": 1, "room_id": 2}
    return CSNetHomeInstallationSensor(coordinator, device_data, {"firmware": "1.0"}, description)


@pytest.mark.parametrize(("code", "name"), sorted(UNIT_MODEL_NAMES.items()))
def test_unit_device_shows_the_commercial_model(code, name):
    """The device of the unit carries the same name the unit model sensor shows."""
    entity = _installation_sensor({"unitModel": code})
    assert entity.device_info["model"] == name
    assert entity.native_value == name


@pytest.mark.parametrize("heating_status", [None, {}, {"unitModel": 99}, {"unitModel": None}])
def test_unit_device_keeps_the_generic_model_when_the_unit_is_unknown(heating_status):
    """Without a known model the device is described as before."""
    assert _installation_sensor(heating_status).device_info["model"] == "HVAC System"
