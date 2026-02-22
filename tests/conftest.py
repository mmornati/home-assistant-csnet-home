"""Pytest configuration and fixtures for CSNet Home tests."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.fixtures.conftest_fixtures import load_fixture as _load_fixture

# Mock external dependencies if not available
try:
    import homeassistant  # noqa: F401
except ImportError:
    mock_hass_obj = MagicMock()
    # Important: Set __path__ to empty list to treat as a package
    mock_hass_obj.__path__ = []
    sys.modules["homeassistant"] = mock_hass_obj
    sys.modules["homeassistant.config_entries"] = MagicMock()
    sys.modules["homeassistant.const"] = MagicMock()
    # Mock some constants commonly used
    sys.modules["homeassistant.const"].UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    sys.modules["homeassistant.const"].UnitOfPressure = SimpleNamespace(BAR="bar")
    sys.modules["homeassistant.const"].UnitOfPower = SimpleNamespace(WATT="W")
    sys.modules["homeassistant.const"].UnitOfEnergy = SimpleNamespace(KILO_WATT_HOUR="kWh")
    sys.modules["homeassistant.const"].UnitOfVolumeFlowRate = SimpleNamespace(CUBIC_METERS_PER_HOUR="m³/h")

    sys.modules["homeassistant.const"].STATE_ON = "on"
    sys.modules["homeassistant.const"].STATE_OFF = "off"
    sys.modules["homeassistant.const"].SIGNAL_STRENGTH_DECIBELS_MILLIWATT = "dBm"

    sys.modules["homeassistant.core"] = MagicMock()

    # Callback mock must return the function itself when used as a decorator
    def callback(func):
        return func
    sys.modules["homeassistant.core"].callback = callback

    sys.modules["homeassistant.helpers"] = MagicMock()
    sys.modules["homeassistant.helpers"].__path__ = []

    # Mock device_registry and DeviceInfo
    mock_device_registry = MagicMock()
    # DeviceInfo is a TypedDict, so we can mock it as a dict
    mock_device_registry.DeviceInfo = dict
    sys.modules["homeassistant.helpers.device_registry"] = mock_device_registry

    # Define dummy base classes to avoid metaclass conflict
    class MockEntity:
        def __init__(self, *args, **kwargs):
            pass
        def async_write_ha_state(self):
            pass

    class MockCoordinatorEntity(MockEntity):
        def __init__(self, coordinator):
            self.coordinator = coordinator

    class MockRestoreEntity(MockEntity):
        async def async_get_last_state(self):
            return None

    class MockDataUpdateCoordinator:
        def __init__(self, hass, logger, name, update_interval=None, update_method=None, request_refresh_debouncer=None):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.update_method = update_method
            self._listeners = []

        def async_add_listener(self, update_callback):
            self._listeners.append(update_callback)
            return lambda: self._listeners.remove(update_callback)

        async def async_request_refresh(self):
            if self.update_method:
                await self.update_method()

    # Mock CoordinatorEntity
    mock_update_coordinator = MagicMock()
    mock_update_coordinator.CoordinatorEntity = MockCoordinatorEntity
    mock_update_coordinator.DataUpdateCoordinator = MockDataUpdateCoordinator
    sys.modules["homeassistant.helpers.update_coordinator"] = mock_update_coordinator

    # Mock Entity and RestoreEntity
    mock_entity = MagicMock()
    sys.modules["homeassistant.helpers.entity"] = mock_entity
    sys.modules["homeassistant.helpers.entity"].Entity = MockEntity

    mock_restore_state = MagicMock()
    sys.modules["homeassistant.helpers.restore_state"] = mock_restore_state
    sys.modules["homeassistant.helpers.restore_state"].RestoreEntity = MockRestoreEntity

    sys.modules["homeassistant.components"] = MagicMock()
    sys.modules["homeassistant.components"].__path__ = []

    sys.modules["homeassistant.components.number"] = MagicMock()
    sys.modules["homeassistant.components.sensor"] = MagicMock()

    # Mock SensorDeviceClass and SensorStateClass
    sys.modules["homeassistant.components.sensor"].SensorDeviceClass = SimpleNamespace(
        SIGNAL_STRENGTH="signal_strength",
        TIMESTAMP="timestamp",
        POWER="power",
        ENERGY="energy",
    )
    sys.modules["homeassistant.components.sensor"].SensorStateClass = SimpleNamespace(
        MEASUREMENT="measurement",
        TOTAL_INCREASING="total_increasing",
    )

    sys.modules["homeassistant.components.climate"] = MagicMock()
    sys.modules["homeassistant.components.climate"].__path__ = []
    sys.modules["homeassistant.components.climate.const"] = MagicMock()
    sys.modules["homeassistant.components.climate.const"].HVACMode = SimpleNamespace(HEAT="heat", COOL="cool", OFF="off", AUTO="auto", HEAT_COOL="heat_cool")

    sys.modules["homeassistant.util"] = MagicMock()
    sys.modules["homeassistant.util"].__path__ = []
    sys.modules["homeassistant.util.dt"] = MagicMock()
    # Mock now() to return a predictable time if needed, or just MagicMock
    sys.modules["homeassistant.util.dt"].now = MagicMock(return_value=MagicMock())

try:
    import aiohttp  # noqa: F401
except ImportError:
    sys.modules["aiohttp"] = MagicMock()

try:
    import async_timeout  # noqa: F401
except ImportError:
    sys.modules["async_timeout"] = MagicMock()


@pytest.fixture
def load_fixture():
    """Fixture to load test fixtures from the fixtures directory."""
    return _load_fixture

@pytest.fixture
def enable_custom_integrations():
    """Enable custom integrations."""
    return True

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield

@pytest.fixture
def hass():
    """Mock the HomeAssistant object."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    return mock_hass
