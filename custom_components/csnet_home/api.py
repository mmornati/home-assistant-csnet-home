import aiohttp
import logging
from homeassistant.core import HomeAssistant
from .const import API_URL, LOGIN_PATH, ELEMENTS_PATH, COMMON_API_HEADERS, DEFAULT_API_TIMEOUT, HEAT_SETTINGS_PATH
from homeassistant.components.climate import HVACMode
import datetime
import async_timeout
import asyncio
import json

_LOGGER = logging.getLogger(__name__)

class CSNetHomeAPI:
    """Handles communication with the cloud service API."""

    def __init__(self, hass: HomeAssistant, username: str, password: str, base_url=API_URL):
        """Initialize the CloudServiceAPI class with username and password."""
        self.hass = hass
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        self.cookies = None
        self.logged_in = False

    async def async_login(self):
        """Log in to the cloud service and return a session cookie."""
        login_url = f"{self.base_url}/{LOGIN_PATH}"
        
        headers = COMMON_API_HEADERS |  {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
        }

        cookies = {
            'XSRF-TOKEN': "be186598-c4d0-4d16-80f0-dc2ab35aad23", 
            'acceptedCookies': 'yes',
        }

        form_data = {
            '_csrf': "be186598-c4d0-4d16-80f0-dc2ab35aad23",
            'token': '',
            'username': self.username,
            'password_unsanitized': self.password,
            'password': self.password
        }

        try:
            self.session = aiohttp.ClientSession()
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(login_url, headers=headers, cookies=cookies, data=form_data) as response:
                    if await self.check_logged_in(response):
                        _LOGGER.info("Login successful")
                        return True
                    else:
                        _LOGGER.error(f"Failed to login. Status code: {response.status}")
                        return False
        except Exception as e:
            _LOGGER.error(f"Error during login: {e}")
            return False

    async def async_get_elements_data(self):
        """Get sensor data from the cloud service."""
        sensor_data_url = f"{self.base_url}{ELEMENTS_PATH}"

        if not self.session or not self.logged_in:
            _LOGGER.warning("No active session found.")
            await self.async_login()
        
        headers = COMMON_API_HEADERS | {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'x-requested-with': 'XMLHttpRequest',
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.get(sensor_data_url, headers=headers, cookies=self.cookies) as response:
                    data = await self.check_api_response(response)
                    if data != None and data.get("status") == "success":
                        _LOGGER.debug(f"Sensor data retrieved: {data['data']}")

                        # Parse the sensor data from the API response
                        elements = data.get("data", {}).get("elements", [])
                        sensors = []
                        common_data = {
                            "name": data.get("data", {}).get("name"),
                            "latitude": data.get("data", {}).get("latitude"),
                            "longitude": data.get("data", {}).get("longitude"),
                            "weather_temperature": data.get("data", {}).get("weatherTemperature"),
                            "device_status": {
                                device.get("id"): {
                                "name": device.get("name"),
                                "status": device.get("status"),
                                "firmware": device.get("firmware"),
                            } for device in data.get("data", {}).get("device_status", [])},
                        }
                        for element in elements:
                            sensor = {
                                "device_name": element.get("deviceName"),
                                "device_id": element.get("deviceId"),
                                "room_name": element.get("parentName"),
                                "parent_id": element.get("parentId"),
                                "room_id": element.get("roomId"),
                                "operation_status": element.get("operationStatus"),
                                "mode": element.get("mode"),
                                "real_mode": element.get("realMode"),
                                "on_off": element.get("onOff"), #0 = Off, 1 = On
                                "timer_running": element.get("timerRunning"),
                                "alarm_code": element.get("alarmCode"),
                                "c1_demand": element.get("c1Demand"),
                                "c2_demand": element.get("c2Demand"),
                                "ecocomfort": element.get("ecocomfort"), #0 = Eco, 1 = Comfort
                                "current_temperature": element.get("currentTemperature"),
                                "setting_temperature": element.get("settingTemperature"),
                                "mode": element.get("mode"),
                                "zone_id": element.get("elementType"),
                            }
                            sensors.append(sensor)
                        _LOGGER.debug(f"Retrieved Sensors: {sensors}")
                        data_elements = {"common_data": common_data, "sensors": sensors}
                        _LOGGER.debug(f"Retrieved Data Elements: {data_elements}")
                        return data_elements
                    else:
                        _LOGGER.error("Error in API response, status not 'success'")
                        return None
        except Exception as e:
            _LOGGER.error(f"Error during sensor data retrieval: {e}")
            self.logged_in = False
            return None
        
    async def async_set_temperature(self, zone_id, parent_id, **kwargs):
        """Set the target temperature for a room."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"

        temperature = kwargs.get("temperature")

        headers = COMMON_API_HEADERS | {
            'accept': '*/*',
            'x-requested-with': 'XMLHttpRequest',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': self.base_url
        }

        data = {
            "orderStatus": "PENDING",
            f"settingTempRoomZ{zone_id}": str(int(temperature * 10)),
            "indoorId": parent_id,
            "_csrf": "9d63b828-f229-402f-899c-19dc40b5e447"
        }

        cookies = {
            'XSRF-TOKEN': "9d63b828-f229-402f-899c-19dc40b5e447",
            'acceptedCookies': 'yes',
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(settings_url, headers=headers, cookies=cookies, data=data) as response:
                    response.raise_for_status()
                    _LOGGER.debug("Temperature set to %s for %s", temperature, zone_id)
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting temperature for %s: %s", zone_id, err)
            return False
    
    async def async_on_off(self, zone_id, parent_id, hvac_mode):
        """Set the target temperature for a room."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"

        status = 1 if hvac_mode == HVACMode.HEAT else 0

        headers = COMMON_API_HEADERS | {
            'accept': '*/*',
            'x-requested-with': 'XMLHttpRequest',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': self.base_url
        }

        data = {
            "orderStatus": "PENDING",
            f"runStopC{zone_id}Air": status,
            "indoorId": parent_id,
            "_csrf": "c93a2274-f19b-4453-b920-8888abd914f8"
        }

        cookies = {
            'XSRF-TOKEN': "c93a2274-f19b-4453-b920-8888abd914f8",
            'acceptedCookies': 'yes',
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(settings_url, headers=headers, cookies=cookies, data=data) as response:
                    response.raise_for_status()
                    _LOGGER.debug("Changing status %s for %s", status, zone_id)
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting temperature for %s: %s", zone_id, err)
            return False


    async def close(self):
        """Close the session after usage."""
        if self.session:
            await self.session.close()

    async def check_logged_in(self, response):
        page_content = await response.text()
        if response.status == 200 and "loadContent(\"login\")" not in page_content:
            _LOGGER.info("Login successful")
            self.logged_in = True
            return True
        else:
            _LOGGER.error(f"Failed to login. Status code: {response.status}")
            self.logged_in = False
            return False
        
    async def check_api_response(self, response):
        if response.status == 200:
            try: 
                data = await response.json()
                return data
            except json.JSONDecodeError as e:
                _LOGGER.error(f"API Response error: {e}")
                self.logged_in = False
                return None
