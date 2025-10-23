"""Test Coordinator configuration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.csnet_home.coordinator import CSNetHomeCoordinator
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_api():
    """Mock the CSNet API."""
    with patch("custom_components.csnet_home.api.CSNetHomeAPI", autospec=True) as mock:
        yield mock


@pytest.mark.asyncio
async def test_coordinator_initialization(hass: HomeAssistant):
    """Test the initialization of the coordinator."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    assert coordinator.hass == hass
    assert coordinator.entry_id == "test"


@pytest.mark.asyncio
async def test_coordinator_update_success(hass: HomeAssistant):
    """Test a successful data update."""
    mock_api = MagicMock()
    mock_api.async_get_elements_data = AsyncMock(
        return_value={
            "common_data": {"name": "Test Home", "device_status": {}},
            "sensors": [{"device_id": 1, "room_name": "Test Room"}],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(
        return_value={"waterSpeed": 100, "defrost": True}
    )
    mock_api.async_get_installation_alarms = AsyncMock(
        return_value={"alarms": [{"code": 42, "message": "Test alarm"}]}
    )
    mock_api.load_translations = AsyncMock()

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    result = await coordinator._async_update_data()

    assert result is not None
    assert "common_data" in result
    assert "sensors" in result
    assert "installation_devices" in result["common_data"]
    assert result["common_data"]["installation_devices"] == {
        "waterSpeed": 100,
        "defrost": True,
    }
    assert "installation_alarms" in result["common_data"]
    assert result["common_data"]["installation_alarms"] == {
        "alarms": [{"code": 42, "message": "Test alarm"}]
    }
    mock_api.async_get_elements_data.assert_called_once()
    mock_api.async_get_installation_devices_data.assert_called_once()
    mock_api.async_get_installation_alarms.assert_called_once()
    mock_api.load_translations.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_update_elements_data_only(hass: HomeAssistant):
    """Test data update when only elements data is available."""
    mock_api = MagicMock()
    mock_api.async_get_elements_data = AsyncMock(
        return_value={
            "common_data": {"name": "Test Home", "device_status": {}},
            "sensors": [{"device_id": 1, "room_name": "Test Room"}],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)
    mock_api.load_translations = AsyncMock()

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    result = await coordinator._async_update_data()

    assert result is not None
    assert "common_data" in result
    assert "sensors" in result
    assert "installation_devices" not in result["common_data"]
    assert "installation_alarms" not in result["common_data"]


@pytest.mark.asyncio
async def test_coordinator_update_no_api(hass: HomeAssistant):
    """Test data update when no API is available."""
    hass.data["csnet_home"] = {"test": {"api": None}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    result = await coordinator._async_update_data()

    assert result is None


@pytest.mark.asyncio
async def test_coordinator_get_sensors_data(hass: HomeAssistant):
    """Test getting sensors data."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [{"device_id": 1, "room_name": "Test Room"}],
        "common_data": {"name": "Test Home"},
    }

    sensors = coordinator.get_sensors_data()
    assert sensors == [{"device_id": 1, "room_name": "Test Room"}]


@pytest.mark.asyncio
async def test_coordinator_get_common_data(hass: HomeAssistant):
    """Test getting common data."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {"name": "Test Home", "device_status": {}},
    }

    common_data = coordinator.get_common_data()
    assert common_data == {"name": "Test Home", "device_status": {}}


@pytest.mark.asyncio
async def test_coordinator_get_installation_devices_data(hass: HomeAssistant):
    """Test getting installation devices data."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {
            "name": "Test Home",
            "installation_devices": {"waterSpeed": 100, "defrost": True},
        },
    }

    installation_data = coordinator.get_installation_devices_data()
    assert installation_data == {"waterSpeed": 100, "defrost": True}


@pytest.mark.asyncio
async def test_coordinator_get_installation_devices_data_empty(hass: HomeAssistant):
    """Test getting installation devices data when not available."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {"name": "Test Home"},
    }

    installation_data = coordinator.get_installation_devices_data()
    assert installation_data == {}


@pytest.mark.asyncio
async def test_coordinator_get_installation_alarms_data(hass: HomeAssistant):
    """Test getting installation alarms data."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {
            "name": "Test Home",
            "installation_alarms": {"alarms": [{"code": 42, "message": "Test alarm"}]},
        },
    }

    alarms_data = coordinator.get_installation_alarms_data()
    assert alarms_data == {"alarms": [{"code": 42, "message": "Test alarm"}]}


@pytest.mark.asyncio
async def test_coordinator_get_installation_alarms_data_empty(hass: HomeAssistant):
    """Test getting installation alarms data when not available."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {"name": "Test Home"},
    }

    alarms_data = coordinator.get_installation_alarms_data()
    assert alarms_data == {}


@pytest.mark.asyncio
async def test_coordinator_alarm_tracking(hass: HomeAssistant):
    """Test alarm code tracking functionality."""
    mock_api = MagicMock()
    mock_api.load_translations = AsyncMock()
    mock_api.async_get_elements_data = AsyncMock(
        return_value={
            "common_data": {"name": "Test Home"},
            "sensors": [
                {
                    "device_id": 123,
                    "room_id": 456,
                    "zone_id": 789,
                    "device_name": "Test Device",
                    "room_name": "Test Room",
                    "alarm_code": 42,
                    "alarm_message": "Test alarm message",
                }
            ],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")

    # Test that alarm codes are tracked
    await coordinator._async_update_data()

    # Verify alarm code was stored
    assert coordinator._last_alarm_codes["123-456-789"] == 42


@pytest.mark.asyncio
async def test_coordinator_alarm_clearing(hass: HomeAssistant):
    """Test alarm code clearing functionality."""
    mock_api = MagicMock()
    mock_api.load_translations = AsyncMock()
    mock_api.async_get_elements_data = AsyncMock(
        return_value={
            "common_data": {"name": "Test Home"},
            "sensors": [
                {
                    "device_id": 123,
                    "room_id": 456,
                    "zone_id": 789,
                    "device_name": "Test Device",
                    "room_name": "Test Room",
                    "alarm_code": 0,
                    "alarm_message": None,
                }
            ],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")

    # Pre-populate with an alarm
    coordinator._last_alarm_codes["123-456-789"] = 42

    await coordinator._async_update_data()

    # Verify alarm code was cleared from storage
    assert "123-456-789" not in coordinator._last_alarm_codes


@pytest.mark.asyncio
async def test_coordinator_get_holiday_mode_units(hass: HomeAssistant):
    """Test getting holiday mode units."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {
            "installation_devices": {
                "data": [
                    {
                        "id": 100,
                        "name": "Outdoor Unit 1",
                        "indoors": [
                            {
                                "id": 201,
                                "name": "Living Room",
                                "holidayMode": {
                                    "year": 2025,
                                    "month": 12,
                                    "day": 25,
                                    "hour": 14,
                                    "minute": 30,
                                },
                            },
                            {
                                "id": 202,
                                "name": "Bedroom",
                                "holidayMode": {
                                    "year": 2025,
                                    "month": 1,
                                    "day": 10,
                                    "hour": 10,
                                    "minute": 0,
                                },
                            },
                        ],
                    }
                ]
            }
        },
    }

    units = coordinator.get_holiday_mode_units()
    assert len(units) == 2
    assert units[0]["unit_id"] == 201
    assert units[0]["unit_name"] == "Living Room"
    assert units[0]["outdoor_id"] == 100
    assert units[0]["outdoor_name"] == "Outdoor Unit 1"
    assert units[0]["holiday_mode"]["year"] == 2025
    assert units[0]["holiday_mode"]["month"] == 12

    assert units[1]["unit_id"] == 202
    assert units[1]["unit_name"] == "Bedroom"


@pytest.mark.asyncio
async def test_coordinator_get_holiday_mode_units_empty(hass: HomeAssistant):
    """Test getting holiday mode units when no installation devices."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {},
    }

    units = coordinator.get_holiday_mode_units()
    assert units == []


@pytest.mark.asyncio
async def test_coordinator_get_holiday_mode_units_no_data_key(hass: HomeAssistant):
    """Test getting holiday mode units when installation devices has no data key."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {"installation_devices": {"some_other_key": "value"}},
    }

    units = coordinator.get_holiday_mode_units()
    assert units == []


@pytest.mark.asyncio
async def test_coordinator_get_holiday_mode_units_no_holiday_mode(hass: HomeAssistant):
    """Test getting holiday mode units when units have no holiday mode."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    coordinator._device_data = {
        "sensors": [],
        "common_data": {
            "installation_devices": {
                "data": [
                    {
                        "id": 100,
                        "name": "Outdoor Unit 1",
                        "indoors": [
                            {
                                "id": 201,
                                "name": "Living Room",
                                # No holidayMode key
                            }
                        ],
                    }
                ]
            }
        },
    }

    units = coordinator.get_holiday_mode_units()
    assert len(units) == 1
    assert units[0]["unit_id"] == 201
    assert units[0]["holiday_mode"] is None
