"""Pytest configuration and fixtures for CSNet Home tests."""

import pytest
from homeassistant.core import HomeAssistant
from tests.fixtures.conftest_fixtures import load_fixture as _load_fixture


@pytest.fixture
def hass():
    """Fixture to provide a mock Home Assistant instance."""
    return HomeAssistant("/test/config")


@pytest.fixture
def load_fixture():
    """Fixture to load test fixtures from the fixtures directory."""
    return _load_fixture
