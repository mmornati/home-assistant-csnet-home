"""Test CSNet Home number platform."""

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Define distinct mock classes to avoid duplicate base class error
class MockCoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.hass = None

    @property
    def available(self):
        return True

    def async_write_ha_state(self):
        pass

class MockNumberEntity:
    _attr_native_min_value = None
    _attr_native_max_value = None
    _attr_native_step = None
    _attr_native_unit_of_measurement = None
    _attr_mode = None
    _attr_name = None
    _attr_unique_id = None

    @property
    def native_min_value(self):
        return self._attr_native_min_value

    @property
    def native_max_value(self):
        return self._attr_native_max_value

    @property
    def native_step(self):
        return self._attr_native_step

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @property
    def mode(self):
        return self._attr_mode

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def native_value(self):
        return None

    @property
    def device_info(self):
        return None

@pytest.fixture
def mock_deps():
    """Mock dependencies and import module under test."""
    with patch.dict(sys.modules):
        # Ensure we have base mocks from conftest.py or create them if needed
        if "homeassistant" not in sys.modules:
            mock_hass = MagicMock()
            sys.modules["homeassistant"] = mock_hass
            sys.modules["homeassistant.config_entries"] = MagicMock()
            sys.modules["homeassistant.const"] = MagicMock()
            sys.modules["homeassistant.const"].UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
            sys.modules["homeassistant.core"] = MagicMock()
            sys.modules["homeassistant.helpers"] = MagicMock()
            sys.modules["homeassistant.helpers.device_registry"] = MagicMock()
            sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()
            sys.modules["homeassistant.components"] = MagicMock()
            sys.modules["homeassistant.components.number"] = MagicMock()
            sys.modules["aiohttp"] = MagicMock()
            sys.modules["async_timeout"] = MagicMock()

        # Update specific mocks for this test file
        sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = MockCoordinatorEntity
        sys.modules["homeassistant.components.number"].NumberEntity = MockNumberEntity
        sys.modules["homeassistant.components.number"].NumberMode = SimpleNamespace(AUTO="auto")
        # Ensure DeviceInfo is a dict for property testing
        sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = dict
        # Ensure callback is an identity function (decorator)
        sys.modules["homeassistant.core"].callback = lambda x: x

        # Import or reload the module under test
        import custom_components.csnet_home.number
        import custom_components.csnet_home.const

        # Reload to ensure it uses our patched dependencies
        import importlib
        importlib.reload(custom_components.csnet_home.number)

        yield custom_components.csnet_home.number

@pytest.fixture
def mock_coordinator():
    """Mock the coordinator."""
    coordinator = MagicMock()
    coordinator.get_sensors_data.return_value = []
    coordinator.get_installation_devices_data.return_value = {}
    coordinator.get_common_data.return_value = {}
    coordinator.async_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_hass_instance(mock_coordinator):
    """Mock the Home Assistant instance."""
    hass = MagicMock()
    # Need to access DOMAIN constant, assume it's "csnet_home" or import it
    domain = "csnet_home"
    hass.data = {
        domain: {
            "entry_id": {
                "coordinator": mock_coordinator,
                "api": MagicMock(),
            }
        }
    }
    return hass


@pytest.fixture
def mock_entry():
    """Mock the config entry."""
    entry = MagicMock()
    entry.entry_id = "entry_id"
    return entry


def test_setup_no_coordinator(mock_deps, mock_hass_instance, mock_entry):
    """Test setup without coordinator."""
    async def run_test():
        # DOMAIN constant needs to be imported from module or mocked
        domain = mock_deps.DOMAIN
        mock_hass_instance.data[domain][mock_entry.entry_id]["coordinator"] = None
        assert await mock_deps.async_setup_entry(mock_hass_instance, mock_entry, MagicMock()) is None
    asyncio.run(run_test())


def test_setup_no_installation_data(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test setup without installation data."""
    async def run_test():
        mock_coordinator.get_installation_devices_data.return_value = None
        assert await mock_deps.async_setup_entry(mock_hass_instance, mock_entry, MagicMock()) is None
    asyncio.run(run_test())


def test_setup_no_heating_status(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test setup without heating status."""
    async def run_test():
        mock_coordinator.get_installation_devices_data.return_value = {
            "data": [{"indoors": [{}]}]
        }
        assert await mock_deps.async_setup_entry(mock_hass_instance, mock_entry, MagicMock()) is None
    asyncio.run(run_test())


def test_setup_heating_mode_c1(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test setup for C1 in heating mode (FIX type)."""
    async def run_test():
        # Mock installation data
        mock_coordinator.get_installation_devices_data.return_value = {
            "data": [
                {
                    "indoors": [
                        {
                            "heatingStatus": {
                                "otcTypeHeatC1": mock_deps.OTC_HEATING_TYPE_FIX,
                            },
                            "heatingSetting": {
                                "fixTempHeatC1": 45,
                            },
                        }
                    ]
                }
            ]
        }

        # Mock sensor data (C1_AIR = 1, C1_WATER = 5)
        mock_coordinator.get_sensors_data.return_value = [
            {"zone_id": 1, "device_id": 123, "room_name": "Living Room", "parent_id": 100},
        ]

        # Mock common data
        mock_coordinator.get_common_data.return_value = {
            "device_status": {123: {"firmware": "1.0"}}
        }

        async_add_entities = MagicMock()
        await mock_deps.async_setup_entry(mock_hass_instance, mock_entry, async_add_entities)

        assert async_add_entities.called
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], mock_deps.CSNetHomeFixedWaterTemperatureNumber)
        assert entities[0]._circuit == 1
        assert entities[0]._mode == 1  # Heating
    asyncio.run(run_test())


def test_setup_cooling_mode_c2(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test setup for C2 in cooling mode (FIX type)."""
    async def run_test():
        # Mock installation data
        mock_coordinator.get_installation_devices_data.return_value = {
            "data": [
                {
                    "indoors": [
                        {
                            "heatingStatus": {
                                "otcTypeCoolC2": mock_deps.OTC_COOLING_TYPE_FIX,
                            },
                            "heatingSetting": {
                                "fixTempCoolC2": 20,
                            },
                        }
                    ]
                }
            ]
        }

        # Mock sensor data (C2_AIR = 2, C2_WATER = 6)
        # Using water zone fallback if air zone missing
        mock_coordinator.get_sensors_data.return_value = [
            {"zone_id": 6, "device_id": 456, "room_name": "Bedroom", "parent_id": 200},
        ]

        async_add_entities = MagicMock()
        await mock_deps.async_setup_entry(mock_hass_instance, mock_entry, async_add_entities)

        assert async_add_entities.called
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], mock_deps.CSNetHomeFixedWaterTemperatureNumber)
        assert entities[0]._circuit == 2
        assert entities[0]._mode == 0  # Cooling
    asyncio.run(run_test())


def test_setup_no_fix_type(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test setup when no circuit is in FIX mode."""
    async def run_test():
        import custom_components.csnet_home.const as csnet_const

        # Mock installation data with GRADIENT type
        mock_coordinator.get_installation_devices_data.return_value = {
            "data": [
                {
                    "indoors": [
                        {
                            "heatingStatus": {
                                "otcTypeHeatC1": csnet_const.OTC_HEATING_TYPE_GRADIENT,
                            },
                            "heatingSetting": {},
                        }
                    ]
                }
            ]
        }

        async_add_entities = MagicMock()
        await mock_deps.async_setup_entry(mock_hass_instance, mock_entry, async_add_entities)

        assert not async_add_entities.called
    asyncio.run(run_test())


def test_number_entity_properties(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test properties of the number entity."""
    sensor_data = {
        "zone_id": 1,
        "device_id": 123,
        "room_name": "Living Room",
        "device_name": "Controller",
        "parent_id": 100
    }
    common_data = {
        "name": "House",
        "firmware": "1.0",
        "device_status": {123: {"firmware": "2.0"}}
    }

    entity = mock_deps.CSNetHomeFixedWaterTemperatureNumber(
        mock_coordinator,
        sensor_data,
        common_data,
        circuit=1,
        mode=1,  # Heating
        entry=mock_entry
    )
    entity.hass = mock_hass_instance

    # Verify static properties
    assert entity.native_min_value == mock_deps.WATER_CIRCUIT_MIN_HEAT
    assert entity.native_max_value == mock_deps.WATER_CIRCUIT_MAX_HEAT
    assert entity.native_step == 1.0
    from homeassistant.const import UnitOfTemperature
    assert entity.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    from homeassistant.components.number import NumberMode
    assert entity.mode == NumberMode.AUTO
    assert entity.name == "Living Room Fixed Water Temperature Heating C1"
    assert entity.unique_id == f"{mock_deps.DOMAIN}-fixed-water-temp-c1-heating-123"

    # Verify device_info
    info = entity.device_info
    assert info["manufacturer"] == "Hitachi"
    assert info["name"] == "Controller-Living Room"
    assert info["sw_version"] == "1.0"


def test_number_native_value(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test native_value property."""
    sensor_data = {"zone_id": 1, "device_id": 123, "room_name": "Living Room"}
    entity = mock_deps.CSNetHomeFixedWaterTemperatureNumber(
        mock_coordinator, sensor_data, {}, circuit=1, mode=1, entry=mock_entry
    )

    # Mock installation data with value
    mock_coordinator.get_installation_devices_data.return_value = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingSetting": {
                            "fixTempHeatC1": 42
                        }
                    }
                ]
            }
        ]
    }

    assert entity.native_value == 42.0

    # Test missing data
    mock_coordinator.get_installation_devices_data.return_value = None
    assert entity.native_value is None


def test_number_available(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test available property."""
    sensor_data = {"zone_id": 1, "device_id": 123, "room_name": "Living Room"}
    entity = mock_deps.CSNetHomeFixedWaterTemperatureNumber(
        mock_coordinator, sensor_data, {}, circuit=1, mode=1, entry=mock_entry
    )
    entity.hass = mock_hass_instance

    api = mock_hass_instance.data[mock_deps.DOMAIN][mock_entry.entry_id]["api"]

    # Mock available = True
    mock_coordinator.get_installation_devices_data.return_value = {"some": "data"}
    api.is_fixed_water_temperature_editable.return_value = True
    assert entity.available is True
    api.is_fixed_water_temperature_editable.assert_called_with(1, 1, {"some": "data"})

    # Mock available = False
    api.is_fixed_water_temperature_editable.return_value = False
    assert entity.available is False

    # Mock no data
    mock_coordinator.get_installation_devices_data.return_value = None
    assert entity.available is False


def test_set_native_value(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test setting native value."""
    async def run_test():
        sensor_data = {
            "zone_id": 1,
            "device_id": 123,
            "room_name": "Living Room",
            "parent_id": 100
        }
        entity = mock_deps.CSNetHomeFixedWaterTemperatureNumber(
            mock_coordinator, sensor_data, {}, circuit=1, mode=1, entry=mock_entry
        )
        entity.hass = mock_hass_instance

        api = mock_hass_instance.data[mock_deps.DOMAIN][mock_entry.entry_id]["api"]
        api.async_set_fixed_water_temperature = AsyncMock(return_value=True)

        # Set value
        with patch("asyncio.sleep", return_value=None):  # Skip sleep
            await entity.async_set_native_value(45.0)

        api.async_set_fixed_water_temperature.assert_called_with(1, 100, 1, 45.0)
        mock_coordinator.async_refresh.assert_called_once()
    asyncio.run(run_test())


def test_set_native_value_failure(mock_deps, mock_hass_instance, mock_entry, mock_coordinator):
    """Test setting native value failure."""
    async def run_test():
        sensor_data = {
            "zone_id": 1,
            "device_id": 123,
            "room_name": "Living Room",
            "parent_id": 100
        }
        entity = mock_deps.CSNetHomeFixedWaterTemperatureNumber(
            mock_coordinator, sensor_data, {}, circuit=1, mode=1, entry=mock_entry
        )
        entity.hass = mock_hass_instance

        api = mock_hass_instance.data[mock_deps.DOMAIN][mock_entry.entry_id]["api"]
        # Simulate API failure (returns False)
        api.async_set_fixed_water_temperature = AsyncMock(return_value=False)

        # Set value
        with patch("asyncio.sleep", return_value=None):  # Skip sleep
            await entity.async_set_native_value(45.0)

        api.async_set_fixed_water_temperature.assert_called_with(1, 100, 1, 45.0)
        # Verify coordinator refresh is NOT called on failure
        mock_coordinator.async_refresh.assert_not_called()
    asyncio.run(run_test())


def test_handle_coordinator_update(mock_deps, mock_entry, mock_coordinator):
    """Test handling coordinator update."""
    sensor_data = {"zone_id": 1, "device_id": 123, "room_name": "Living Room"}
    entity = mock_deps.CSNetHomeFixedWaterTemperatureNumber(
        mock_coordinator, sensor_data, {}, circuit=1, mode=1, entry=mock_entry
    )
    entity.async_write_ha_state = MagicMock()

    # Update sensor data in coordinator
    new_sensor_data = sensor_data.copy()
    new_sensor_data["new_prop"] = "value"
    mock_coordinator.get_sensors_data.return_value = [new_sensor_data]

    entity._handle_coordinator_update()

    assert entity._coordinator == mock_coordinator
    mock_coordinator.get_sensors_data.assert_called()

    assert entity._sensor_data == new_sensor_data
    entity.async_write_ha_state.assert_called_once()
