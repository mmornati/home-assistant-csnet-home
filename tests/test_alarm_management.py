"""Test alarm notifications and sensor logic."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant

from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.coordinator import CSNetHomeCoordinator
from custom_components.csnet_home.sensor import CSNetHomeAlarmHistorySensor

# Mock data from user report
MOCK_ALARMS_RESPONSE = {
    "status": "success",
    "data": [
        {
            "id": 138670,
            "installationId": 4529,
            "unitId": 6996,
            "code": -1,
            "createdAt": 1761914386000,
            "recoveredAt": 315532800000,
            "hiddenToUsers": 0,
            "notifiedStatus": 0,
            "notifiedAt": 1761914386000,
            "createdAtString": "2025-10-31 12:39:46",
            "recoveredAtString": "1980-01-01 00:00:00",
        },
        {
            "id": 138669,
            "installationId": 4529,
            "unitId": 6995,
            "code": -1,
            "createdAt": 1761914386000,
            "recoveredAt": 315532800000,
            "hiddenToUsers": 0,
            "notifiedStatus": 0,
            "notifiedAt": 1761914386000,
            "createdAtString": "2025-10-31 12:39:46",
            "recoveredAtString": "1980-01-01 00:00:00",
        },
    ],
    "timestamp": 1771770630059,
}


@pytest.fixture
def mock_api(hass):
    """Mock the CSNetHomeAPI."""
    api = MagicMock(spec=CSNetHomeAPI)
    api.hass = hass
    # Ensure common_data is not empty so the coordinator processes alarms
    api.async_get_elements_data = AsyncMock(return_value={"sensors": [], "common_data": {"name": "Test Home"}})
    api.async_get_installation_devices_data = AsyncMock(return_value={})
    api.async_get_installation_alarms = AsyncMock(return_value=MOCK_ALARMS_RESPONSE)
    api.load_translations = AsyncMock()
    api.translate_alarm = MagicMock(side_effect=lambda x: f"Alarm {x}" if x != -1 else None)
    api.get_heating_status_from_installation_devices = MagicMock(return_value={})
    return api


@pytest.mark.asyncio
async def test_alarm_history_sensor(hass, mock_api):
    """Test that the alarm history sensor correctly counts alarms from 'data' key."""
    # Setup coordinator
    coordinator = CSNetHomeCoordinator(hass, 60, "test_entry")
    hass.data[DOMAIN] = {"test_entry": {"api": mock_api, "coordinator": coordinator}}

    # Make async_call awaitable (mocking it for the coordinator init/update)
    hass.services.async_call = AsyncMock()

    # Trigger update
    await coordinator._async_update_data()

    # Initialize sensor
    sensor = CSNetHomeAlarmHistorySensor(coordinator, {})

    # Verify state (count of alarms)
    assert sensor.state == 2

    # Verify attributes
    attrs = sensor.extra_state_attributes
    assert attrs["total_alarms"] == 2
    assert len(attrs["recent_alarms"]) == 2
    assert attrs["recent_alarms"][0]["id"] == 138670
    assert attrs["recent_alarms"][0]["code"] == -1
    assert attrs["recent_alarms"][0]["description"] == "System/Communication Error"
    assert attrs["recent_alarms"][0]["recovered"] == "1980-01-01 00:00:00"


@pytest.mark.asyncio
async def test_coordinator_alarm_notifications(hass, mock_api):
    """Test that coordinator triggers notifications for active alarms."""
    # Setup coordinator
    coordinator = CSNetHomeCoordinator(hass, 60, "test_entry")
    hass.data[DOMAIN] = {"test_entry": {"api": mock_api, "coordinator": coordinator}}

    # Use AsyncMock for async_call
    mock_call = AsyncMock()
    hass.services.async_call = mock_call

    # Trigger update
    await coordinator._async_update_data()

    # Should call persistent_notification.create twice (for 2 active alarms)
    assert mock_call.call_count == 2

    # Verify call arguments
    call_args_list = mock_call.call_args_list

    messages = []
    for args, kwargs in call_args_list:
        if len(args) >= 3:
            service_data = args[2]
        else:
            service_data = kwargs.get("service_data", {})
        messages.append(service_data.get("message", ""))

    # Verify first alarm notification is present
    assert any("Installation Alarm ID: 138670" in msg for msg in messages)
    assert any("Code: -1" in msg for msg in messages)
    assert any("Unit ID: 6996" in msg for msg in messages)

    # Verify second alarm notification is present
    assert any("Installation Alarm ID: 138669" in msg for msg in messages)

    # Verify tracked notified IDs
    assert 138670 in coordinator._notified_installation_alarm_ids
    assert 138669 in coordinator._notified_installation_alarm_ids

    # Reset mock and update again - should NOT trigger notifications again
    mock_call.reset_mock()
    await coordinator._async_update_data()
    mock_call.assert_not_called()


@pytest.mark.asyncio
async def test_api_delete_alarm(hass):
    """Test async_delete_alarm method."""
    from custom_components.csnet_home.api import CSNetHomeAPI
    from custom_components.csnet_home.const import DELETESPECIFICALARM_PATH

    api = CSNetHomeAPI(hass, "user", "pass")

    with patch("aiohttp.ClientSession") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        api.session = mock_session
        api.xsrf_token = "token"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "success"
        mock_session.post.return_value.__aenter__.return_value = mock_response

        result = await api.async_delete_alarm(12345, 67890)

        assert result is True

        # Verify API call
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args
        assert args[0].endswith(DELETESPECIFICALARM_PATH)
        assert kwargs["data"]["installationId"] == 12345
        assert kwargs["data"]["alarmId"] == 67890
        assert kwargs["data"]["_csrf"] == "token"
