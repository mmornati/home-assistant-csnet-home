"""Test API module to check contracts."""

import asyncio
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
                        "silentMode": 0,
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
                        "silentMode": 1,
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
                "silent_mode": 0,
                "current_temperature": 19.5,
                "setting_temperature": 19.0,
                "zone_id": 1,
                "fan1_speed": None,
                "fan2_speed": None,
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
                "silent_mode": 1,
                "current_temperature": 17.5,
                "setting_temperature": 19.0,
                "zone_id": 2,
                "fan1_speed": None,
                "fan2_speed": None,
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
                        "silentMode": 0,
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
                        "silentMode": 0,
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
                "device_name": "Remote",
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
                "silent_mode": 0,
                "current_temperature": 19.5,
                "setting_temperature": 19.0,
                "zone_id": 1,
                "fan1_speed": None,
                "fan2_speed": None,
            },
            {
                "device_name": "Remote",
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
                "silent_mode": 0,
                "current_temperature": 17.5,
                "setting_temperature": 19.0,
                "zone_id": 2,
                "fan1_speed": None,
                "fan2_speed": None,
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
async def test_api_set_hvac_mode_zone5_uses_circuit1(mock_aiohttp_client, hass):
    """Test that zone_id 5 uses C1 in runStop parameter names."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 5 turning on heat
    result = await api.async_set_hvac_mode(5, 2486, "heat")

    assert result is True
    # Check that the call was made with C1 water parameters (zone 5 is a water circuit)
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # Zone 5 is water circuit, should only have runStopC1, not runStopC1Air
    assert "runStopC1" in data_sent
    assert data_sent["runStopC1"] == "1"
    # Should NOT have Air parameter for water circuits
    assert "runStopC1Air" not in data_sent
    # Should not have C5 parameters
    assert "runStopC5" not in data_sent
    assert "runStopC5Air" not in data_sent


@pytest.mark.asyncio
async def test_api_set_hvac_mode_zone1_uses_circuit1(mock_aiohttp_client, hass):
    """Test that zone_id 1 uses C1 in runStop parameter names (normal case)."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 turning on heat (zone 1 is typically an air circuit)
    result = await api.async_set_hvac_mode(1, 1706, "heat")

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # Zone 1 is air circuit, should only have runStopC1Air, not runStopC1
    assert "runStopC1Air" in data_sent
    assert data_sent["runStopC1Air"] == "1"
    # Should NOT have water parameter for air circuits
    assert "runStopC1" not in data_sent


@pytest.mark.asyncio
async def test_api_set_hvac_mode_auto_zone1_air(mock_aiohttp_client, hass):
    """Test setting AUTO mode (heat_cool) for zone 1 (air circuit)."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 setting AUTO mode
    result = await api.async_set_hvac_mode(1, 1706, "heat_cool")

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # AUTO mode should set mode to "2"
    assert data_sent["mode"] == "2"
    # Zone 1 is air circuit, should only have runStopC1Air, not runStopC1
    assert "runStopC1Air" in data_sent
    assert data_sent["runStopC1Air"] == "1"
    # Should NOT have water parameter for air circuits
    assert "runStopC1" not in data_sent


@pytest.mark.asyncio
async def test_api_set_hvac_mode_auto_zone5_water(mock_aiohttp_client, hass):
    """Test setting AUTO mode (heat_cool) for zone 5 (water circuit)."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 5 setting AUTO mode
    result = await api.async_set_hvac_mode(5, 2486, "heat_cool")

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # AUTO mode should set mode to "2"
    assert data_sent["mode"] == "2"
    # Zone 5 is water circuit, should only have runStopC1, not runStopC1Air
    assert "runStopC1" in data_sent
    assert data_sent["runStopC1"] == "1"
    # Should NOT have Air parameter for water circuits
    assert "runStopC1Air" not in data_sent


@pytest.mark.asyncio
async def test_api_set_preset_mode_zone5_uses_circuit1(mock_aiohttp_client, hass):
    """Test that zone_id 5 uses C1 in preset mode parameter names."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 5 setting eco mode (zone 5 is a water circuit)
    result = await api.set_preset_modes(5, 2486, "eco", current_mode=1, on_off=1)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "ecoModeC1" in data_sent
    # Zone 5 is water circuit, should only have runStopC1, not runStopC1Air
    assert "runStopC1" in data_sent
    assert data_sent["runStopC1"] == "1"
    # Should NOT have Air parameter for water circuits
    assert "runStopC1Air" not in data_sent
    # Should not have C5 parameters
    assert "ecoModeC5" not in data_sent


@pytest.mark.asyncio
async def test_api_set_hvac_mode_zone2_uses_circuit2_air(mock_aiohttp_client, hass):
    """Test that zone_id 2 uses C2Air parameters (air circuit)."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 2 turning on cool (zone 2 is air circuit)
    result = await api.async_set_hvac_mode(2, 1706, "cool")

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # Zone 2 is air circuit, should only have runStopC2Air, not runStopC2
    assert "runStopC2Air" in data_sent
    assert data_sent["runStopC2Air"] == "1"
    assert data_sent["mode"] == "0"  # cool mode
    # Should NOT have water parameter for air circuits
    assert "runStopC2" not in data_sent


@pytest.mark.asyncio
async def test_api_set_hvac_mode_off_zone5_water(mock_aiohttp_client, hass):
    """Test turning OFF zone 5 (water circuit)."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 5 turning off
    result = await api.async_set_hvac_mode(5, 2486, "off")

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # Zone 5 is water circuit, should only have runStopC1=0, not runStopC1Air
    assert "runStopC1" in data_sent
    assert data_sent["runStopC1"] == "0"
    # Should NOT have Air parameter for water circuits
    assert "runStopC1Air" not in data_sent
    # Should not send mode when turning off
    assert "mode" not in data_sent


@pytest.mark.asyncio
async def test_api_set_hvac_mode_off_zone1_air(mock_aiohttp_client, hass):
    """Test turning OFF zone 1 (air circuit)."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 turning off
    result = await api.async_set_hvac_mode(1, 1706, "off")

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # Zone 1 is air circuit, should only have runStopC1Air=0, not runStopC1
    assert "runStopC1Air" in data_sent
    assert data_sent["runStopC1Air"] == "0"
    # Should NOT have water parameter for air circuits
    assert "runStopC1" not in data_sent
    # Should not send mode when turning off
    assert "mode" not in data_sent


@pytest.mark.asyncio
async def test_api_set_preset_mode_zone1_air(mock_aiohttp_client, hass):
    """Test setting preset mode for zone 1 (air circuit)."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 setting comfort mode
    result = await api.set_preset_modes(1, 1706, "comfort", current_mode=1, on_off=1)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "ecoModeC1" in data_sent
    assert data_sent["ecoModeC1"] == "1"  # 1 = comfort
    # Zone 1 is air circuit, should only have runStopC1Air, not runStopC1
    assert "runStopC1Air" in data_sent
    assert data_sent["runStopC1Air"] == "1"
    # Should NOT have water parameter for air circuits
    assert "runStopC1" not in data_sent


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


@pytest.mark.asyncio
async def test_api_set_silent_mode_on(mock_aiohttp_client, hass):
    """Test setting silent mode on for a zone."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 turning silent mode on
    result = await api.async_set_silent_mode(1, 1706, True)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "silentModeC1" in data_sent
    assert data_sent["silentModeC1"] == "1"
    assert data_sent["indoorId"] == 1706
    assert data_sent["orderStatus"] == "PENDING"


@pytest.mark.asyncio
async def test_api_set_silent_mode_off(mock_aiohttp_client, hass):
    """Test setting silent mode off for a zone."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 turning silent mode off
    result = await api.async_set_silent_mode(1, 1706, False)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "silentModeC1" in data_sent
    assert data_sent["silentModeC1"] == "0"


@pytest.mark.asyncio
async def test_api_set_silent_mode_zone5_uses_circuit1(mock_aiohttp_client, hass):
    """Test that zone_id 5 uses C1 in silent mode parameter names."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 5 setting silent mode
    result = await api.async_set_silent_mode(5, 2486, True)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    # Zone 5 should use C1 parameters
    assert "silentModeC1" in data_sent
    assert data_sent["silentModeC1"] == "1"
    # Should not have C5 parameters
    assert "silentModeC5" not in data_sent


@pytest.mark.asyncio
async def test_api_set_silent_mode_zone2_uses_circuit2(mock_aiohttp_client, hass):
    """Test that zone_id 2 uses C2 in silent mode parameter names."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 2 setting silent mode
    result = await api.async_set_silent_mode(2, 1706, True)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "silentModeC2" in data_sent
    assert data_sent["silentModeC2"] == "1"


@pytest.mark.asyncio
async def test_api_set_silent_mode_http_error(mock_aiohttp_client, hass):
    """Test silent mode API call with HTTP error."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value='{"error":"Internal server error"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 - should fail
    result = await api.async_set_silent_mode(1, 1706, True)

    assert result is False


@pytest.mark.asyncio
async def test_api_set_silent_mode_timeout_error(mock_aiohttp_client, hass):
    """Test silent mode API call with timeout error."""
    mock_client_instance = mock_aiohttp_client.return_value

    # Mock post to raise TimeoutError
    mock_client_instance.post.return_value.__aenter__.side_effect = asyncio.TimeoutError

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 - should fail
    result = await api.async_set_silent_mode(1, 1706, True)

    assert result is False


def test_get_temperature_limits_zone1_heating(hass):
    """Test temperature limits extraction for zone 1 in heating mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "heatAirMinC1": 11,
            "heatAirMaxC1": 30,
            "coolAirMinC1": 16,
            "coolAirMaxC1": 30,
        }
    }

    # Zone 1, heating mode (mode=1)
    min_temp, max_temp = api.get_temperature_limits(1, 1, installation_devices_data)

    assert min_temp == 11
    assert max_temp == 30


def test_get_temperature_limits_zone1_cooling(hass):
    """Test temperature limits extraction for zone 1 in cooling mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "heatAirMinC1": 11,
            "heatAirMaxC1": 30,
            "coolAirMinC1": 16,
            "coolAirMaxC1": 30,
        }
    }

    # Zone 1, cooling mode (mode=0)
    min_temp, max_temp = api.get_temperature_limits(1, 0, installation_devices_data)

    assert min_temp == 16
    assert max_temp == 30


def test_get_temperature_limits_zone2_heating(hass):
    """Test temperature limits extraction for zone 2 in heating mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "heatAirMinC2": 12,
            "heatAirMaxC2": 28,
            "coolAirMinC2": 18,
            "coolAirMaxC2": 26,
        }
    }

    # Zone 2, heating mode (mode=1)
    min_temp, max_temp = api.get_temperature_limits(2, 1, installation_devices_data)

    assert min_temp == 12
    assert max_temp == 28


def test_get_temperature_limits_zone2_cooling(hass):
    """Test temperature limits extraction for zone 2 in cooling mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "heatAirMinC2": 12,
            "heatAirMaxC2": 28,
            "coolAirMinC2": 18,
            "coolAirMaxC2": 26,
        }
    }

    # Zone 2, cooling mode (mode=0)
    min_temp, max_temp = api.get_temperature_limits(2, 0, installation_devices_data)

    assert min_temp == 18
    assert max_temp == 26


def test_get_temperature_limits_zone5_heating(hass):
    """Test temperature limits extraction for zone 5 (water circuit) in heating mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "heatMinC1": 25,
            "heatMaxC1": 55,
            "coolMinC1": 15,
            "coolMaxC1": 22,
        }
    }

    # Zone 5, heating mode (mode=1)
    min_temp, max_temp = api.get_temperature_limits(5, 1, installation_devices_data)

    assert min_temp == 25
    assert max_temp == 55


def test_get_temperature_limits_zone5_cooling(hass):
    """Test temperature limits extraction for zone 5 (water circuit) in cooling mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "heatMinC1": 25,
            "heatMaxC1": 55,
            "coolMinC1": 15,
            "coolMaxC1": 22,
        }
    }

    # Zone 5, cooling mode (mode=0)
    min_temp, max_temp = api.get_temperature_limits(5, 0, installation_devices_data)

    assert min_temp == 15
    assert max_temp == 22


def test_get_temperature_limits_zone3_dhw(hass):
    """Test temperature limits extraction for zone 3 (DHW/water heater)."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "dhwMax": 60,
        }
    }

    # Zone 3 (DHW), heating mode (mode=1)
    min_temp, max_temp = api.get_temperature_limits(3, 1, installation_devices_data)

    assert min_temp is None  # DHW min is not provided by API
    assert max_temp == 60


def test_get_temperature_limits_no_data(hass):
    """Test temperature limits extraction when no installation devices data is available."""
    api = CSNetHomeAPI(hass, "user", "pass")

    # No installation devices data
    min_temp, max_temp = api.get_temperature_limits(1, 1, None)

    assert min_temp is None
    assert max_temp is None


def test_get_temperature_limits_no_heating_status(hass):
    """Test temperature limits extraction when heatingStatus is missing."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {"otherData": "value"}

    # Missing heatingStatus
    min_temp, max_temp = api.get_temperature_limits(1, 1, installation_devices_data)

    assert min_temp is None
    assert max_temp is None


def test_get_temperature_limits_partial_data(hass):
    """Test temperature limits extraction when only some limits are available."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_devices_data = {
        "heatingStatus": {
            "heatAirMinC1": 11,
            # heatAirMaxC1 is missing
        }
    }

    # Zone 1, heating mode (mode=1)
    min_temp, max_temp = api.get_temperature_limits(1, 1, installation_devices_data)

    assert min_temp == 11
    assert max_temp is None  # Max not available


# Fan Speed Control Tests
@pytest.mark.asyncio
async def test_api_set_fan_speed_c1_low(mock_aiohttp_client, hass):
    """Test setting fan speed to low for circuit 1."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1, circuit 1, fan speed low (1)
    result = await api.async_set_fan_speed(1, 1706, 1, 1)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "fan1Speed" in data_sent
    assert data_sent["fan1Speed"] == "1"
    assert data_sent["indoorId"] == 1706
    assert data_sent["orderStatus"] == "PENDING"


@pytest.mark.asyncio
async def test_api_set_fan_speed_c2_medium(mock_aiohttp_client, hass):
    """Test setting fan speed to medium for circuit 2."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 2, circuit 2, fan speed medium (2)
    result = await api.async_set_fan_speed(2, 1706, 2, 2)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "fan2Speed" in data_sent
    assert data_sent["fan2Speed"] == "2"


@pytest.mark.asyncio
async def test_api_set_fan_speed_auto(mock_aiohttp_client, hass):
    """Test setting fan speed to auto."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with fan speed auto (3)
    result = await api.async_set_fan_speed(1, 1706, 3, 1)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "fan1Speed" in data_sent
    assert data_sent["fan1Speed"] == "3"


@pytest.mark.asyncio
async def test_api_set_fan_speed_off(mock_aiohttp_client, hass):
    """Test setting fan speed to off."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"status":"success"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with fan speed off (0)
    result = await api.async_set_fan_speed(1, 1706, 0, 1)

    assert result is True
    call_args = mock_client_instance.post.call_args
    assert call_args is not None
    data_sent = call_args[1]["data"]
    assert "fan1Speed" in data_sent
    assert data_sent["fan1Speed"] == "0"


@pytest.mark.asyncio
async def test_api_set_fan_speed_http_error(mock_aiohttp_client, hass):
    """Test fan speed API call with HTTP error."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.post.return_value.__aenter__.return_value
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value='{"error":"Internal server error"}')
    mock_response.raise_for_status = AsyncMock()

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 - should fail
    result = await api.async_set_fan_speed(1, 1706, 1, 1)

    assert result is False


@pytest.mark.asyncio
async def test_api_set_fan_speed_timeout_error(mock_aiohttp_client, hass):
    """Test fan speed API call with timeout error."""
    mock_client_instance = mock_aiohttp_client.return_value

    # Mock post to raise TimeoutError
    mock_client_instance.post.return_value.__aenter__.side_effect = asyncio.TimeoutError

    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = mock_client_instance
    api.logged_in = True
    api.xsrf_token = "test-token"
    api.cookies = {"test": "cookie"}

    # Test with zone_id 1 - should fail
    result = await api.async_set_fan_speed(1, 1706, 1, 1)

    assert result is False


def test_is_fan_coil_compatible_true(hass):
    """Test fan coil compatibility check when systemConfigBits has 0x2000 bit set."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_data = {
        "heatingStatus": {"systemConfigBits": 0x2000}  # Fan coil compatible
    }

    assert api.is_fan_coil_compatible(installation_data) is True


def test_is_fan_coil_compatible_false(hass):
    """Test fan coil compatibility check when systemConfigBits does not have 0x2000 bit."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_data = {
        "heatingStatus": {"systemConfigBits": 0x1000}  # Not fan coil compatible
    }

    assert api.is_fan_coil_compatible(installation_data) is False


def test_is_fan_coil_compatible_missing_data(hass):
    """Test fan coil compatibility check with missing data."""
    api = CSNetHomeAPI(hass, "user", "pass")

    # Test with None
    assert api.is_fan_coil_compatible(None) is False

    # Test with empty dict
    assert api.is_fan_coil_compatible({}) is False

    # Test with missing heatingStatus
    assert api.is_fan_coil_compatible({"other": "data"}) is False


def test_get_fan_control_availability_c1_heat_mode(hass):
    """Test fan control availability for C1 in heat mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_data = {
        "heatingStatus": {
            "systemConfigBits": 0x2000,  # Fan coil compatible
            "fan1ControlledOnLCD": 1,  # Heating only
        }
    }

    # Heat mode (1) should be available
    assert api.get_fan_control_availability(1, 1, installation_data) is True

    # Cool mode (0) should not be available
    assert api.get_fan_control_availability(1, 0, installation_data) is False

    # Auto mode (2) should not be available
    assert api.get_fan_control_availability(1, 2, installation_data) is False


def test_get_fan_control_availability_c1_cool_mode(hass):
    """Test fan control availability for C1 in cool mode."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_data = {
        "heatingStatus": {
            "systemConfigBits": 0x2000,  # Fan coil compatible
            "fan1ControlledOnLCD": 2,  # Cooling only
        }
    }

    # Heat mode (1) should not be available
    assert api.get_fan_control_availability(1, 1, installation_data) is False

    # Cool mode (0) should be available
    assert api.get_fan_control_availability(1, 0, installation_data) is True

    # Auto mode (2) should not be available
    assert api.get_fan_control_availability(1, 2, installation_data) is False


def test_get_fan_control_availability_c1_both_modes(hass):
    """Test fan control availability for C1 in both heat and cool modes."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_data = {
        "heatingStatus": {
            "systemConfigBits": 0x2000,  # Fan coil compatible
            "fan1ControlledOnLCD": 3,  # Heating + Cooling
        }
    }

    # Heat mode (1) should be available
    assert api.get_fan_control_availability(1, 1, installation_data) is True

    # Cool mode (0) should be available
    assert api.get_fan_control_availability(1, 0, installation_data) is True

    # Auto mode (2) should be available
    assert api.get_fan_control_availability(1, 2, installation_data) is True


def test_get_fan_control_availability_c2(hass):
    """Test fan control availability for C2."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_data = {
        "heatingStatus": {
            "systemConfigBits": 0x2000,  # Fan coil compatible
            "fan2ControlledOnLCD": 3,  # Heating + Cooling
        }
    }

    # Circuit 2 with heat mode
    assert api.get_fan_control_availability(2, 1, installation_data) is True

    # Circuit 2 with cool mode
    assert api.get_fan_control_availability(2, 0, installation_data) is True


def test_get_fan_control_availability_not_compatible(hass):
    """Test fan control availability when system is not fan coil compatible."""
    api = CSNetHomeAPI(hass, "user", "pass")

    installation_data = {
        "heatingStatus": {
            "systemConfigBits": 0x1000,  # Not fan coil compatible
            "fan1ControlledOnLCD": 3,
        }
    }

    # Should return False even though fan1ControlledOnLCD is set
    assert api.get_fan_control_availability(1, 1, installation_data) is False


def test_get_fan_control_availability_missing_data(hass):
    """Test fan control availability with missing data."""
    api = CSNetHomeAPI(hass, "user", "pass")

    # Test with None
    assert api.get_fan_control_availability(1, 1, None) is False

    # Test with empty dict
    assert api.get_fan_control_availability(1, 1, {}) is False

    # Test with missing heatingStatus
    assert api.get_fan_control_availability(1, 1, {"other": "data"}) is False


@pytest.mark.asyncio
async def test_api_get_elements_data_with_fan_speeds(mock_aiohttp_client, hass):
    """Test that fan speeds are extracted from elements data."""
    mock_client_instance = mock_aiohttp_client.return_value

    mock_response = mock_client_instance.get.return_value.__aenter__.return_value
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "status": "success",
            "data": {
                "device_status": [
                    {
                        "id": 1709,
                        "name": "Hitachi PAC",
                        "status": 1,
                        "firmware": "1234",
                    }
                ],
                "weatherTemperature": 9,
                "latitude": "50.123456",
                "longitude": "3.12",
                "installation": 1234,
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
                        "deviceId": 1234,
                        "deviceName": "Hitachi PAC",
                        "roomId": 395,
                        "ecocomfort": 1,
                        "operationStatus": 5,
                        "c1Demand": True,
                        "c2Demand": True,
                        "doingBoost": False,
                        "timerRunning": False,
                        "silentMode": 0,
                        "alarmCode": 0,
                        "fan1Speed": 2,  # Medium speed
                        "fan2Speed": 1,  # Low speed
                    },
                ],
                "name": "My Home",
            },
        }
    )

    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client_instance

    data = await api.async_get_elements_data()

    assert data is not None
    assert len(data["sensors"]) == 1
    assert data["sensors"][0]["fan1_speed"] == 2
    assert data["sensors"][0]["fan2_speed"] == 1
