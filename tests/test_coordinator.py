"""Test Coordinator configuration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.csnet_home.coordinator import CSNetHomeCoordinator


@pytest.fixture(autouse=True)
def mock_integration_frame():
    """Mock integration frame to prevent RuntimeError in DataUpdateCoordinator."""
    with patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        yield


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
    mock_api.async_get_installation_devices_data = AsyncMock(return_value={"waterSpeed": 100, "defrost": True})
    mock_api.async_get_installation_alarms = AsyncMock(return_value={"alarms": [{"code": 42, "message": "Test alarm"}]})
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
    assert result["common_data"]["installation_alarms"] == {"alarms": [{"code": 42, "message": "Test alarm"}]}
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
async def test_coordinator_alarm_notification(hass: HomeAssistant):
    """Test alarm notification is sent when a new alarm is detected."""
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
                    "alarm_code_formatted": "E42",
                    "alarm_message": "Test alarm message",
                    "unit_type": "standard",
                    "alarm_origin": "Unit",
                }
            ],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")

    # Trigger update with new alarm
    # Patch ServiceRegistry.async_call as it's typically read-only on the instance
    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_async_call:
        await coordinator._async_update_data()

        # Verify alarm code was stored
        assert coordinator._last_alarm_codes["123-456-789"] == 42

        # Verify notification service was called
        mock_async_call.assert_called_once()
        args, kwargs = mock_async_call.call_args
        # Depending on how the mock is bound, domain might be at index 0 or 1
        # In the previous failure, 'create' (arg[2]) matched 'persistent_notification' (arg[1]) failure message
        # Wait, the failure said: AssertionError: assert 'create' == 'persistent_notification'
        # which means I asserted call_args[0][1] == "persistent_notification" and it was 'create'.
        # So arg[0] was "persistent_notification" and arg[1] was "create".
        # This confirms arg[0] is DOMAIN, NOT SELF.
        # So the class-level patch on ServiceRegistry.async_call DOES NOT receive self in call_args when called on instance?
        # That's unusual but possible if HA/pytest-asyncio wraps it.

        assert args[0] == "persistent_notification"
        assert args[1] == "create"

        payload = args[2]
        assert payload["title"] == "Hitachi Device Alarm"
        assert "Device: Test Device | Room: Test Room" in payload["message"]
        assert "Code: E42 (raw: 42)" in payload["message"]
        assert "Message: Test alarm message" in payload["message"]
        assert "Origin: Unit" in payload["message"]
        assert payload["notification_id"] == "csnet_home_alarm_123-456-789"


@pytest.mark.asyncio
async def test_coordinator_dhw_temperature_issue(hass: HomeAssistant):
    """Test the DHW temperature enrichment issue (GH#141)."""
    mock_api = MagicMock()

    # Mock elements data returning correct temperature 48.0
    mock_api.async_get_elements_data = AsyncMock(
        return_value={
            "common_data": {"name": "Test Home", "device_status": {}},
            "sensors": [
                {
                    "device_id": 5684,
                    "zone_id": 3,
                    "current_temperature": 48.0,
                    "room_name": "ballon",
                }
            ],
        }
    )

    # Mock installation devices data returning weird tempDHW -67
    mock_api.async_get_installation_devices_data = AsyncMock(return_value={"data": [{"indoors": [{"heatingStatus": {"tempDHW": -67}}]}]})

    # Mock get_heating_status_from_installation_devices to return the dict directly
    mock_api.get_heating_status_from_installation_devices = MagicMock(return_value={"tempDHW": -67})

    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)
    mock_api.load_translations = AsyncMock()

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")

    # We need to make sure _is_valid_temperature is called
    result = await coordinator._async_update_data()

    # Verify that the temperature was NOT overwritten with -67, but kept as 48.0
    sensors = result["sensors"]
    assert len(sensors) == 1
    assert sensors[0]["current_temperature"] == 48.0


@pytest.mark.asyncio
async def test_coordinator_get_sensor_data_by_id(hass: HomeAssistant):
    """Test getting sensor data by unique ID."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")
    sensor_1 = {"device_id": 1, "room_id": 10, "zone_id": 1, "name": "Sensor 1"}
    sensor_2 = {"device_id": 2, "room_id": 20, "zone_id": 2, "name": "Sensor 2"}

    coordinator._device_data = {
        "sensors": [sensor_1, sensor_2],
        "common_data": {"name": "Test Home"},
    }

    # Manually populate the lookup dictionary since we're bypassing _async_update_data
    coordinator._sensors_by_id = {(s["device_id"], s["room_id"], s["zone_id"]): s for s in coordinator._device_data["sensors"]}

    assert coordinator.get_sensor_data_by_id(1, 10, 1) == sensor_1
    assert coordinator.get_sensor_data_by_id(2, 20, 2) == sensor_2
    assert coordinator.get_sensor_data_by_id(3, 30, 3) is None


@pytest.mark.asyncio
async def test_coordinator_filtered_alarm_code_skipped(hass: HomeAssistant):
    """Test that filtered alarm codes (default: -1) are skipped from notifications."""
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
                    "alarm_code": -1,
                    "alarm_message": "System/Communication Error",
                    "unit_type": "standard",
                }
            ],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    # Default: filtered_alarm_codes = "-1" which should filter out alarm_code -1
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")

    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_async_call:
        await coordinator._async_update_data()

        # Verify alarm code was stored (tracking still happens)
        assert coordinator._last_alarm_codes["123-456-789"] == -1

        # Verify NO notification was sent (filtered)
        mock_async_call.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_filtered_alarm_codes_custom(hass: HomeAssistant):
    """Test that custom filtered alarm codes are respected."""
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
                    "alarm_code": -5,
                    "alarm_message": "Communication Error",
                    "unit_type": "standard",
                }
            ],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    # Custom filtered codes: -5 should be filtered
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test", filtered_alarm_codes="-5,-10")

    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_async_call:
        await coordinator._async_update_data()

        # Verify NO notification was sent (filtered)
        mock_async_call.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_disabled_alarm_notifications(hass: HomeAssistant):
    """Test that disabled alarm notifications suppress all notifications."""
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
                    "alarm_code_formatted": "E42",
                    "alarm_message": "Real Alarm",
                    "unit_type": "standard",
                }
            ],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(return_value=None)

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    # Disable all alarm notifications
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test", enable_alarm_notifications=False)

    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_async_call:
        await coordinator._async_update_data()

        # Verify NO notification was sent (disabled)
        mock_async_call.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_parse_filtered_alarm_codes(hass: HomeAssistant):
    """Test parsing of comma-separated alarm codes."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test", filtered_alarm_codes="-1,-2,10,20")

    assert coordinator._filtered_alarm_codes == {-1, -2, 10, 20}


@pytest.mark.asyncio
async def test_coordinator_parse_filtered_alarm_codes_empty(hass: HomeAssistant):
    """Test parsing empty alarm codes string."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test", filtered_alarm_codes="")

    assert coordinator._filtered_alarm_codes == set()


@pytest.mark.asyncio
async def test_coordinator_parse_filtered_alarm_codes_invalid(hass: HomeAssistant):
    """Test parsing invalid alarm codes string."""
    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test", filtered_alarm_codes="abc,def")

    assert coordinator._filtered_alarm_codes == set()


@pytest.mark.asyncio
async def test_coordinator_installation_alarm_filtered(hass: HomeAssistant):
    """Test that installation alarms with filtered codes are suppressed."""
    mock_api = MagicMock()
    mock_api.load_translations = AsyncMock()
    mock_api.async_get_elements_data = AsyncMock(
        return_value={
            "common_data": {"name": "Test Home"},
            "sensors": [],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(
        return_value={
            "data": [
                {
                    "id": 123,
                    "code": -1,
                    "unitId": 456,
                    "recoveredAtString": "1980-01-01 00:00:00",
                }
            ]
        }
    )

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")

    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_async_call:
        await coordinator._async_update_data()

        # Verify NO notification was sent (filtered)
        mock_async_call.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_installation_alarm_not_filtered(hass: HomeAssistant):
    """Test that installation alarms not in filter list are sent."""
    mock_api = MagicMock()
    mock_api.load_translations = AsyncMock()
    mock_api.async_get_elements_data = AsyncMock(
        return_value={
            "common_data": {"name": "Test Home"},
            "sensors": [],
        }
    )
    mock_api.async_get_installation_devices_data = AsyncMock(return_value=None)
    mock_api.async_get_installation_alarms = AsyncMock(
        return_value={
            "data": [
                {
                    "id": 123,
                    "code": 42,
                    "unitId": 456,
                    "recoveredAtString": "1980-01-01 00:00:00",
                }
            ]
        }
    )
    mock_api.translate_alarm = MagicMock(return_value="Test Alarm")

    hass.data["csnet_home"] = {"test": {"api": mock_api}}

    coordinator = CSNetHomeCoordinator(hass=hass, update_interval=30, entry_id="test")

    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_async_call:
        await coordinator._async_update_data()

        # Verify notification WAS sent (not filtered)
        mock_async_call.assert_called_once()
        args, kwargs = mock_async_call.call_args
        assert args[0] == "persistent_notification"
        assert args[1] == "create"
        assert "123" in args[2]["notification_id"]
