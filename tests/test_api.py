"""Test API module to check contracts."""

from unittest.mock import ANY, AsyncMock, patch

import pytest
from aiohttp import CookieJar

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


def test_get_current_temperature_scaling(hass):
    """Scale or return settingTemperature according to elementType."""
    api = CSNetHomeAPI(hass, "u", "p")
    # type 5 multiplies by 10
    assert (
        api.get_current_temperature({"elementType": 5, "settingTemperature": 25}) == 250
    )
    # other types return raw value
    assert (
        api.get_current_temperature({"elementType": 1, "settingTemperature": 19.5})
        == 19.5
    )


@pytest.mark.asyncio
async def test_login_success(mock_aiohttp_client, hass):
    """Test a successful get_data call."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

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
            "_csrf": ANY,
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

    mock_login_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

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
            "_csrf": ANY,
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
                "doingBoost": False,
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
                "alarm_message": None,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 19.5,
                "setting_temperature": 19.0,
                "zone_id": 1,
            },
            {
                "device_name": "Hitachi PAC",
                "doingBoost": False,
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
                "alarm_message": None,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 17.5,
                "setting_temperature": 19.0,
                "zone_id": 2,
            },
        ],
    }
    mock_client_instance.get.assert_called_with(
        "https://www.csnetmanager.com/data/elements", headers=ANY, cookies=ANY
    )


@pytest.mark.asyncio
async def test_api_get_elements_data_empty_names(mock_aiohttp_client, hass):
    """Test a successful get_data call when room name and device name are empty."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

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
                "doingBoost": False,
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
                "alarm_message": None,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 19.5,
                "setting_temperature": 19.0,
                "zone_id": 1,
            },
            {
                "device_name": "ATW-IOT-01",
                "doingBoost": False,
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
                "alarm_message": None,
                "c1_demand": True,
                "c2_demand": True,
                "ecocomfort": 1,
                "current_temperature": 17.5,
                "setting_temperature": 19.0,
                "zone_id": 2,
            },
        ],
    }
    mock_client_instance.get.assert_called_with(
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


@pytest.mark.asyncio
async def test_api_get_installation_devices_data_success(mock_aiohttp_client, hass):
    """Test a successful get installation devices data call."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "waterSpeed": 100,
            "waterDebit": 3.9,
            "inWaterTemperature": 20,
            "outWaterTemperature": 20,
            "setWaterTemperatureTTWO": 23,
            "waterPressure": 4.48,
            "outExchangerWaterTemperature": 20,
            "defrost": True,
            "mixValvePosition": 100,
            "externalTemperature": 14,
            "meanExternalTemperature": 15,
            "workingElectricHeater": "Stopped",
        }
    )

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance
    api.logged_in = True
    api.cookies = {"test": "cookie"}

    data = await api.async_get_installation_devices_data()

    assert data == {
        "waterSpeed": 100,
        "waterDebit": 3.9,
        "inWaterTemperature": 20,
        "outWaterTemperature": 20,
        "setWaterTemperatureTTWO": 23,
        "waterPressure": 4.48,
        "outExchangerWaterTemperature": 20,
        "defrost": True,
        "mixValvePosition": 100,
        "externalTemperature": 14,
        "meanExternalTemperature": 15,
        "workingElectricHeater": "Stopped",
    }
    mock_client_instance.get.assert_called_with(
        "https://www.csnetmanager.com/data/installationdevices?installationId=-1",
        headers=ANY,
        cookies=ANY,
    )


@pytest.mark.asyncio
async def test_api_translate_alarm_code_found(mock_aiohttp_client, hass):
    """Test alarm code translation when code is found."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.translations = {
        "alarm_42": "Test alarm message",
        "alarm_042": "Test alarm message formatted",
    }

    result = api.translate_alarm(42)
    assert result == "Test alarm message"

    result = api.translate_alarm(42)
    assert result == "Test alarm message"


@pytest.mark.asyncio
async def test_api_translate_alarm_code_not_found(mock_aiohttp_client, hass):
    """Test alarm code translation when code is not found."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.translations = {
        "alarm_42": "Test alarm message",
    }

    result = api.translate_alarm(99)
    assert result is None


@pytest.mark.asyncio
async def test_api_translate_alarm_no_translations(mock_aiohttp_client, hass):
    """Test alarm code translation when no translations are loaded."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.translations = {}

    result = api.translate_alarm(42)
    assert result is None


@pytest.mark.asyncio
async def test_api_extract_cookie_value_found(mock_aiohttp_client, hass):
    """Test cookie value extraction when cookie is found."""
    api = CSNetHomeAPI(hass, "user", "pass")

    # Create a mock cookie jar with a test cookie
    jar = CookieJar()
    jar.update_cookies({"test_cookie": "test_value"})

    result = api.extract_cookie_value(jar, "test_cookie")
    assert result == "test_value"


@pytest.mark.asyncio
async def test_api_extract_cookie_value_not_found(mock_aiohttp_client, hass):
    """Test cookie value extraction when cookie is not found."""
    api = CSNetHomeAPI(hass, "user", "pass")

    # Create an empty cookie jar
    jar = CookieJar()

    result = api.extract_cookie_value(jar, "nonexistent_cookie")
    assert result is None


@pytest.mark.asyncio
async def test_api_get_installation_devices_data_failure(mock_aiohttp_client, hass):
    """Test installation devices data retrieval failure."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=None)

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance
    api.logged_in = True
    api.cookies = {"test": "cookie"}

    data = await api.async_get_installation_devices_data()

    assert data is None


@pytest.mark.asyncio
async def test_api_get_installation_devices_data_exception(mock_aiohttp_client, hass):
    """Test installation devices data retrieval with exception."""
    mock_client_instance = mock_aiohttp_client.return_value

    # Mock the login process to succeed
    mock_login_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

    # Mock the installation devices call to raise exception
    def side_effect(*args, **kwargs):
        url = args[0] if args else kwargs.get("url", "")
        if "installationdevices" in url:
            raise ConnectionError("Network error")
        # For login calls, return a normal response
        return mock_client_instance.get.return_value.__aenter__.return_value

    mock_client_instance.get.side_effect = side_effect

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance
    api.logged_in = False  # Start as not logged in

    data = await api.async_get_installation_devices_data()

    assert data is None
    assert api.logged_in is False


@pytest.mark.asyncio
async def test_api_get_installation_devices_data_not_logged_in(
    mock_aiohttp_client, hass
):
    """Test installation devices data retrieval when not logged in."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_login_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_login_response.status = 200
    mock_login_response.text = AsyncMock(return_value="xxx xxx xxx")

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"test": "data"})

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance
    api.logged_in = False

    data = await api.async_get_installation_devices_data()

    # Should call login first, then get the data
    assert data == {"test": "data"}
    mock_client_instance.post.assert_called()  # Login was called
    mock_client_instance.get.assert_called()  # Data retrieval was called


@pytest.mark.asyncio
async def test_api_get_installation_alarms_success(mock_aiohttp_client, hass):
    """Test a successful installation alarms data call."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "alarms": [
                {
                    "id": 123,
                    "code": 42,
                    "message": "Test alarm",
                    "deviceId": 1234,
                    "timestamp": 1234567890,
                }
            ]
        }
    )

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance
    api.logged_in = True
    api.cookies = {"test": "cookie"}
    api.installation_id = 4529
    api.xsrf_token = "test-token"

    data = await api.async_get_installation_alarms()

    assert data == {
        "alarms": [
            {
                "id": 123,
                "code": 42,
                "message": "Test alarm",
                "deviceId": 1234,
                "timestamp": 1234567890,
            }
        ]
    }
    mock_client_instance.get.assert_called_with(
        "https://www.csnetmanager.com/data/installationalarms?installationId=4529&_csrf=test-token",
        headers=ANY,
        cookies=ANY,
    )


@pytest.mark.asyncio
async def test_api_get_installation_alarms_no_installation_id(
    mock_aiohttp_client, hass
):
    """Test installation alarms retrieval when no installation ID is available."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.installation_id = None

    data = await api.async_get_installation_alarms()

    assert data is None


@pytest.mark.asyncio
async def test_api_get_installation_alarms_failure(mock_aiohttp_client, hass):
    """Test installation alarms data retrieval failure."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=None)

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance
    api.logged_in = True
    api.cookies = {"test": "cookie"}
    api.installation_id = 4529
    api.xsrf_token = "test-token"

    data = await api.async_get_installation_alarms()

    assert data is None
