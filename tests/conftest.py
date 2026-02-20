"""Pytest configuration and fixtures for CSNet Home tests."""

import pytest
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

from tests.fixtures.conftest_fixtures import load_fixture as _load_fixture

# Mock external dependencies if not available
try:
    import homeassistant
except ImportError:
    mock_hass = MagicMock()
    sys.modules["homeassistant"] = mock_hass
    sys.modules["homeassistant.config_entries"] = MagicMock()
    sys.modules["homeassistant.const"] = MagicMock()
    # Mock some constants commonly used
    sys.modules["homeassistant.const"].UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    sys.modules["homeassistant.const"].STATE_ON = "on"
    sys.modules["homeassistant.const"].STATE_OFF = "off"

    sys.modules["homeassistant.core"] = MagicMock()
    sys.modules["homeassistant.helpers"] = MagicMock()
    sys.modules["homeassistant.helpers.device_registry"] = MagicMock()
    sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()

    sys.modules["homeassistant.components"] = MagicMock()
    sys.modules["homeassistant.components.number"] = MagicMock()
    sys.modules["homeassistant.components.sensor"] = MagicMock()

    sys.modules["homeassistant.components.climate"] = MagicMock()
    sys.modules["homeassistant.components.climate.const"] = MagicMock()
    sys.modules["homeassistant.components.climate.const"].HVACMode = SimpleNamespace(
        HEAT="heat", COOL="cool", OFF="off", AUTO="auto", HEAT_COOL="heat_cool"
    )

try:
    import aiohttp
except ImportError:
    sys.modules["aiohttp"] = MagicMock()

try:
    import async_timeout
except ImportError:
    sys.modules["async_timeout"] = MagicMock()


@pytest.fixture
def load_fixture():
    """Fixture to load test fixtures from the fixtures directory."""
    return _load_fixture


@pytest.fixture
def enable_custom_integrations():
    """Mock fixture for enabling custom integrations."""
    yield


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
