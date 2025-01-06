import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.core import HomeAssistant
from custom_components.csnet_home.coordinator import CSNetHomeCoordinator


@pytest.fixture
def mock_api():
    """Mock the CSNet API."""
    with patch("custom_components.csnet_home.api.CSNetHomeAPI", autospec=True) as mock:
        yield mock


@pytest.fixture(name='hass')
async def test_coordinator_initialization(hass: HomeAssistant, mock_api):
    """Test the initialization of the coordinator."""
    coordinator = CSNetHomeCoordinator(hass, "192.168.1.1", "user", "pass")
    assert coordinator.host == "192.168.1.1"
    assert coordinator.username == "user"
    assert coordinator.password == "pass"


@pytest.fixture(name='hass')
async def test_coordinator_update_success(hass: HomeAssistant, mock_api):
    """Test a successful data update."""
    mock_api_instance = mock_api.return_value
    mock_api_instance.get_data = AsyncMock(return_value={"key": "value"})

    coordinator = CSNetHomeCoordinator(hass, "192.168.1.1", "user", "pass")
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data == {"key": "value"}
    mock_api_instance.get_data.assert_called_once()


@pytest.fixture(name='hass')
async def test_coordinator_update_failure(hass: HomeAssistant, mock_api):
    """Test a data update failure."""
    mock_api_instance = mock_api.return_value
    mock_api_instance.get_data = AsyncMock(side_effect=Exception("API error"))

    coordinator = CSNetHomeCoordinator(hass, "192.168.1.1", "user", "pass")

    with pytest.raises(Exception, match="API error"):
        await coordinator._async_update_data()


@pytest.fixture(name='hass')
async def test_coordinator_close(hass: HomeAssistant, mock_api):
    """Test closing the coordinator."""
    mock_api_instance = mock_api.return_value

    coordinator = CSNetHomeCoordinator(hass, "192.168.1.1", "user", "pass")
    await coordinator.async_close()

    mock_api_instance.close.assert_called_once()