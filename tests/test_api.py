"""Test API module to check contracts."""

from unittest.mock import ANY, AsyncMock, patch

import pytest

from custom_components.csnet_home.api import CSNetHomeAPI


@pytest.fixture
def mock_aiohttp_client():
    """Mock the aiohttp ClientSession."""
    with patch("aiohttp.ClientSession", autospec=True) as mock:
        yield mock


@pytest.mark.asyncio
async def test_api_initialization(hass):
    """Test initializing the CSNetHomeAPI."""
    api = CSNetHomeAPI(hass, "user", "pass")
    assert api.username == "user"
    assert api.password == "pass"
    assert api.session is None


@pytest.mark.asyncio
async def test_login_success(mock_aiohttp_client, hass):
    """Test a successful get_data call."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance

    data = await api.async_login()

    assert data is True
    assert api.logged_in is True
    mock_client_instance.post.assert_called_once_with(
        "https://www.csnetmanager.com/login",
        headers=ANY,
        cookies=ANY,
        data={
            "_csrf": "be186598-c4d0-4d16-80f0-dc2ab35aad23",
            "token": "",
            "username": "user",
            "password_unsanitized": "pass",
            "password": "pass",
        },
    )


@pytest.mark.asyncio
async def test_login_error(mock_aiohttp_client, hass):
    """Test a successful get_data call."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.post.return_value.__aenter__.return_value
    # The Website is always returning 200 with a wrong login. It just display the login page again
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value='xxx loadContent("login") xxx')

    api = CSNetHomeAPI(hass, "user", "pass_wrong")
    api._session = mock_client_instance

    data = await api.async_login()

    assert data is False
    assert api.logged_in is False
    mock_client_instance.post.assert_called_once_with(
        "https://www.csnetmanager.com/login",
        headers=ANY,
        cookies=ANY,
        data={
            "_csrf": "be186598-c4d0-4d16-80f0-dc2ab35aad23",
            "token": "",
            "username": "user",
            "password_unsanitized": "pass_wrong",
            "password": "pass_wrong",
        },
    )


@pytest.mark.asyncio
async def test_api_get_elements_data_success(mock_aiohttp_client, hass):
    """Test a successful get_data call."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "status": "success",
            "data": {
                "device_status": [
                    {
                        "id": 1709,
                        "disabled": False,
                        "ownerId": 123,
                        "name": "Hitachi PAC",
                        "lastComm": 1736193442000,
                        "type": 0,
                        "status": 1,
                        "hash": "",
                        "firmware": "1234",
                        "key": "111111",
                        "currentTime": 20250106205719,
                        "currentTimeMillis": 1736193448768,
                        "rssi": -70,
                    }
                ],
                "rooms": [
                    {
                        "id": 394,
                        "installation_id": 1234,
                        "name": "1st Floor",
                        "disabled": False,
                    },
                    {
                        "id": 395,
                        "installation_id": 1234,
                        "name": "2nd Floor",
                        "disabled": False,
                    },
                ],
                "weatherTemperature": 9,
                "latitude": "50.123456",
                "iu_qty": 1,
                "weatherForecastIcon": "10d",
                "administrator": "admin",
                "holidays": [
                    {
                        "indoorId": 1706,
                        "year": 0,
                        "month": 0,
                        "day": 0,
                        "hour": -1,
                        "minute": -1,
                        "c1AirSetting": 17,
                        "c2AirSetting": 17,
                        "c1Affected": True,
                        "c2Affected": True,
                        "dhwAffected": True,
                        "swpAffected": True,
                        "pacAffected": False,
                        "iot_time": 20250106205719,
                        "dhwSetting": 30,
                        "swpSetting": 28,
                        "compatibleWithDHWSWPSettings": True,
                        "zones": [],
                    }
                ],
                "installation": 1234,
                "avOuTemp": 4.0,
                "elements": [
                    {
                        "parentId": 1234,
                        "elementType": 1,
                        "parentName": "Room1",
                        "mode": 1,
                        "realMode": 1,
                        "onOff": 1,
                        "settingTemperature": 19.0,
                        "currentTemperature": 19.5,
                        "yutaki": True,
                        "modelCode": 0,
                        "alarmCode": 0,
                        "deviceId": 1234,
                        "deviceName": "Hitachi PAC",
                        "ouAddress": 0,
                        "iuAddress": 0,
                        "roomId": 395,
                        "ecocomfort": 1,
                        "fanSpeed": -1,
                        "operationStatus": 5,
                        "hasCooling": False,
                        "hasAuto": False,
                        "hasBoost": False,
                        "c1Demand": True,
                        "c2Demand": True,
                        "doingBoost": False,
                        "timerRunning": False,
                        "fixAvailable": False,
                    },
                    {
                        "parentId": 1234,
                        "elementType": 2,
                        "parentName": "Room 2",
                        "mode": 1,
                        "realMode": 1,
                        "onOff": 1,
                        "settingTemperature": 19.0,
                        "currentTemperature": 17.5,
                        "yutaki": True,
                        "modelCode": 0,
                        "alarmCode": 0,
                        "deviceId": 1234,
                        "deviceName": "Hitachi PAC",
                        "ouAddress": 0,
                        "iuAddress": 0,
                        "roomId": 394,
                        "ecocomfort": 1,
                        "fanSpeed": -1,
                        "operationStatus": 5,
                        "hasCooling": False,
                        "hasAuto": False,
                        "hasBoost": False,
                        "c1Demand": True,
                        "c2Demand": True,
                        "doingBoost": False,
                        "timerRunning": False,
                        "fixAvailable": False,
                    },
                ],
                "name": "My Home",
                "weatherForecastUpdate": 1736066133704,
                "user_dispayableName": "Myself",
                "longitude": "3.12",
            },
        }
    )

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance

    data = await api.async_get_elements_data()

    assert data == {
        "common_data": {
            "name": "My Home",
            "latitude": "50.123456",
            "longitude": "3.12",
            "weather_temperature": 9,
            "device_status": {
                1709: {"name": "Hitachi PAC", "status": 1, "firmware": "1234"}
            },
        },
        "sensors": [
            {
                "device_name": "Hitachi PAC",
                "device_id": 1234,
                "room_name": "Room1",
                "parent_id": 1234,
                "room_id": 395,
                "operation_status": 5,
                "mode": 1,
                "real_mode": 1,
                "on_off": 1,
                "timer_running": False,
                "alarm_code": 0,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 19.5,
                "setting_temperature": 19.0,
                "zone_id": 1,
            },
            {
                "device_name": "Hitachi PAC",
                "device_id": 1234,
                "room_name": "Room 2",
                "parent_id": 1234,
                "room_id": 394,
                "operation_status": 5,
                "mode": 1,
                "real_mode": 1,
                "on_off": 1,
                "timer_running": False,
                "alarm_code": 0,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 17.5,
                "setting_temperature": 19.0,
                "zone_id": 2,
            },
        ],
    }
    mock_client_instance.get.assert_called_once_with(
        "https://www.csnetmanager.com/data/elements", headers=ANY, cookies=ANY
    )


@pytest.mark.asyncio
async def test_api_get_elements_data_empty_names(mock_aiohttp_client, hass):
    """Test a successful get_data call when room name and device name are empty."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "status": "success",
            "data": {
                "device_status": [
                    {
                        "id": 1709,
                        "disabled": False,
                        "ownerId": 123,
                        "name": "Hitachi PAC",
                        "lastComm": 1736193442000,
                        "type": 0,
                        "status": 1,
                        "hash": "",
                        "firmware": "1234",
                        "key": "111111",
                        "currentTime": 20250106205719,
                        "currentTimeMillis": 1736193448768,
                        "rssi": -70,
                    }
                ],
                "rooms": [],
                "weatherTemperature": 9,
                "latitude": "50.123456",
                "iu_qty": 1,
                "weatherForecastIcon": "10d",
                "administrator": "admin",
                "holidays": [],
                "installation": 1234,
                "avOuTemp": 4.0,
                "elements": [
                    {
                        "parentId": 1234,
                        "elementType": 1,
                        "parentName": "",
                        "mode": 1,
                        "realMode": 1,
                        "onOff": 1,
                        "settingTemperature": 19.0,
                        "currentTemperature": 19.5,
                        "yutaki": True,
                        "modelCode": 0,
                        "alarmCode": 0,
                        "deviceId": 9876,
                        "deviceName": "",
                        "ouAddress": 0,
                        "iuAddress": 0,
                        "roomId": -1,
                        "ecocomfort": 1,
                        "fanSpeed": -1,
                        "operationStatus": 5,
                        "hasCooling": False,
                        "hasAuto": False,
                        "hasBoost": False,
                        "c1Demand": True,
                        "c2Demand": True,
                        "doingBoost": False,
                        "timerRunning": False,
                        "fixAvailable": False,
                    },
                    {
                        "parentId": 1234,
                        "elementType": 2,
                        "parentName": "",
                        "mode": 1,
                        "realMode": 1,
                        "onOff": 1,
                        "settingTemperature": 19.0,
                        "currentTemperature": 17.5,
                        "yutaki": True,
                        "modelCode": 0,
                        "alarmCode": 0,
                        "deviceId": 9876,
                        "deviceName": "",
                        "ouAddress": 0,
                        "iuAddress": 0,
                        "roomId": -1,
                        "ecocomfort": 1,
                        "fanSpeed": -1,
                        "operationStatus": 5,
                        "hasCooling": False,
                        "hasAuto": False,
                        "hasBoost": False,
                        "c1Demand": True,
                        "c2Demand": True,
                        "doingBoost": False,
                        "timerRunning": False,
                        "fixAvailable": False,
                    },
                ],
                "name": "My Home",
                "weatherForecastUpdate": 1736066133704,
                "user_dispayableName": "Myself",
                "longitude": "3.12",
            },
        }
    )

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance

    data = await api.async_get_elements_data()

    assert data == {
        "common_data": {
            "name": "My Home",
            "latitude": "50.123456",
            "longitude": "3.12",
            "weather_temperature": 9,
            "device_status": {
                1709: {"name": "Hitachi PAC", "status": 1, "firmware": "1234"}
            },
        },
        "sensors": [
            {
                "device_name": "ATW-IOT-01",
                "device_id": 9876,
                "room_name": "Room-1234-0",
                "parent_id": 1234,
                "room_id": -1,
                "operation_status": 5,
                "mode": 1,
                "real_mode": 1,
                "on_off": 1,
                "timer_running": False,
                "alarm_code": 0,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 19.5,
                "setting_temperature": 19.0,
                "zone_id": 1,
            },
            {
                "device_name": "ATW-IOT-01",
                "device_id": 9876,
                "room_name": "Room-1234-1",
                "parent_id": 1234,
                "room_id": -1,
                "operation_status": 5,
                "mode": 1,
                "real_mode": 1,
                "on_off": 1,
                "timer_running": False,
                "alarm_code": 0,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 17.5,
                "setting_temperature": 19.0,
                "zone_id": 2,
            },
        ],
    }
    mock_client_instance.get.assert_called_once_with(
        "https://www.csnetmanager.com/data/elements", headers=ANY, cookies=ANY
    )


@pytest.mark.asyncio
async def test_api_get_data_failure(mock_aiohttp_client, hass):
    """Test a failed get_data call."""
    mock_client_instance = mock_aiohttp_client.return_value
    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 500

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance

    data = await api.async_get_elements_data()

    assert data is None


@pytest.mark.asyncio
async def test_api_close_session(mock_aiohttp_client, hass):
    """Test closing the API session."""
    mock_client_instance = mock_aiohttp_client.return_value

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance

    await api.close()
    mock_client_instance.close.assert_called_once()
