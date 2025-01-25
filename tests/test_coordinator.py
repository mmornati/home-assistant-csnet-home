"""Test Coordinator configuration."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.csnet_home.coordinator import CSNetHomeCoordinator
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_api():
    """Mock the CSNet API."""
    with patch("custom_components.csnet_home.api.CSNetHomeAPI", autospec=True) as mock:
        yield mock


@pytest.fixture(name="hass")
async def test_coordinator_initialization(hass: HomeAssistant, mock_api):
    """Test the initialization of the coordinator."""
    coordinator = CSNetHomeCoordinator(hass=hass)
    assert coordinator.hass == hass


@pytest.fixture(name="hass")
async def test_coordinator_update_success(hass: HomeAssistant, mock_api):
    """Test a successful data update."""
    mock_api_instance = mock_api.return_value
    mock_api_instance.get_data = AsyncMock(return_value={"key": "value"})

    coordinator = CSNetHomeCoordinator(hass=hass)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data == {"key": "value"}
    mock_api_instance.get_data.assert_called_once()


@pytest.fixture(name="hass")
async def test_coordinator_update_failure(hass: HomeAssistant, mock_api):
    """Test a data update failure."""
    mock_api_instance = mock_api.return_value
    mock_api_instance.get_data = AsyncMock(side_effect=Exception("API error"))

    coordinator = CSNetHomeCoordinator(hass=hass)

    with pytest.raises(Exception, match="API error"):
        await coordinator._async_update_data()
