"""Pytest configuration and fixtures for CSNet Home tests."""

from unittest.mock import MagicMock

import pytest

from tests.fixtures.conftest_fixtures import load_fixture as _load_fixture


@pytest.fixture
def hass():
    """Fixture to provide a mock Home Assistant instance."""
    hass_mock = MagicMock()
    hass_mock.data = {}
    return hass_mock


@pytest.fixture
def load_fixture():
    """Fixture to load test fixtures from the fixtures directory."""
    return _load_fixture
