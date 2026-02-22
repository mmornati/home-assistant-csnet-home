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
    mock_hass = MagicMock()
    sys.modules["homeassistant"] = mock_hass
    sys.modules["homeassistant.config_entries"] = MagicMock()
    sys.modules["homeassistant.const"] = MagicMock()
    # Mock some constants commonly used
    sys.modules["homeassistant.const"].UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    sys.modules["homeassistant.const"].STATE_ON = "on"
    sys.modules["homeassistant.const"].STATE_OFF = "off"

    sys.modules["homeassistant.util"] = MagicMock()
    sys.modules["homeassistant.util.dt"] = MagicMock()

    sys.modules["homeassistant.core"] = MagicMock()
    sys.modules["homeassistant.helpers"] = MagicMock()

    # Define Mock classes to avoid metaclass conflicts
    class MockEntity:
        pass

    class MockCoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

    mock_entity_mod = MagicMock()
    mock_entity_mod.Entity = MockEntity

    class MockDeviceInfo(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    mock_entity_mod.DeviceInfo = MockDeviceInfo
    sys.modules["homeassistant.helpers.entity"] = mock_entity_mod

    class MockRestoreEntity:
        pass

    mock_restore_state_mod = MagicMock()
    mock_restore_state_mod.RestoreEntity = MockRestoreEntity
    sys.modules["homeassistant.helpers.restore_state"] = mock_restore_state_mod

    mock_dr = MagicMock()
    mock_dr.DeviceInfo = MockDeviceInfo
    sys.modules["homeassistant.helpers.device_registry"] = mock_dr

    mock_coordinator_mod = MagicMock()
    mock_coordinator_mod.CoordinatorEntity = MockCoordinatorEntity
    mock_coordinator_mod.DataUpdateCoordinator = MagicMock
    sys.modules["homeassistant.helpers.update_coordinator"] = mock_coordinator_mod

    sys.modules["homeassistant.components"] = MagicMock()
    sys.modules["homeassistant.components.number"] = MagicMock()
    sys.modules["homeassistant.components.sensor"] = MagicMock()

    sys.modules["homeassistant.components.climate"] = MagicMock()
    sys.modules["homeassistant.components.climate.const"] = MagicMock()
    sys.modules["homeassistant.components.climate.const"].HVACMode = SimpleNamespace(HEAT="heat", COOL="cool", OFF="off", AUTO="auto", HEAT_COOL="heat_cool")

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
    """Mock enable_custom_integrations fixture."""
    yield


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
