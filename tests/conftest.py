"""Pytest configuration and fixtures for CSNet Home tests."""

import pytest

from tests.fixtures.conftest_fixtures import load_fixture as _load_fixture


@pytest.fixture
def load_fixture():
    """Fixture to load test fixtures from the fixtures directory."""
    return _load_fixture


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
