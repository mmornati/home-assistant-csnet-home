import aiohttp
import logging
from homeassistant.core import HomeAssistant
from .const import API_URL, LOGIN_PATH, ELEMENTS_PATH, LOGIN_CSRF_TOKEN, ACTIONS_CSRF_TOKEN, COMMON_API_HEADERS, DEFAULT_API_TIMEOUT, SET_TEMPERATURE_PATH
from homeassistant.exceptions import PlatformNotReady
import async_timeout
import asyncio

_LOGGER = logging.getLogger(__name__)

class CSNetHomeAPI:
    """Handles communication with the cloud service API."""

    def __init__(self, hass: HomeAssistant, username: str, password: str, base_url=API_URL, login_csrf_token=LOGIN_CSRF_TOKEN, actions_csrf_token=ACTIONS_CSRF_TOKEN):
        """Initialize the CloudServiceAPI class with username and password."""
        self.hass = hass
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        self.cookies = None
        self.login_csrf_token = login_csrf_token
        self.actions_csrf_token = actions_csrf_token

    async def async_login(self):
        """Log in to the cloud service and return a session cookie."""
        login_url = f"{self.base_url}/{LOGIN_PATH}"
        
        headers = COMMON_API_HEADERS |  {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
        }

        cookies = {
            'XSRF-TOKEN': self.login_csrf_token,  # CSRF token
            'acceptedCookies': 'yes',
        }

        form_data = {
            '_csrf': self.login_csrf_token,
            'token': '',
            'username': self.username,
            'password_unsanitized': self.password,
            'password': self.password
        }

        try:
            self.session = aiohttp.ClientSession()
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(login_url, headers=headers, cookies=cookies, data=form_data) as response:
                    if response.status == 200:
                        _LOGGER.info("Login successful")
                        return True
                    else:
                        _LOGGER.error(f"Failed to login. Status code: {response.status}")
                        return False
        except Exception as e:
            _LOGGER.error(f"Error during login: {e}")
            return False

    async def async_get_sensor_data(self):
        """Get sensor data from the cloud service."""
        sensor_data_url = f"{self.base_url}{ELEMENTS_PATH}"

        if not self.session:
            _LOGGER.warning("No active session found.")
            await self.async_login()
            #return None
        
        headers = COMMON_API_HEADERS | {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'x-requested-with': 'XMLHttpRequest',
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.get(sensor_data_url, headers=headers, cookies=self.cookies) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "success":
                            _LOGGER.debug(f"Sensor data retrieved: {data['data']}")

                            # Parse the sensor data from the API response
                            elements = data.get("data", {}).get("elements", [])
                            sensors = []

                            for element in elements:
                                sensor = {
                                    "device_name": element.get("deviceName"),
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
                            return sensors
                        else:
                            _LOGGER.error("Error in API response, status not 'success'")
                            return None
                    else:
                        _LOGGER.error(f"Failed to get sensor data. Status code: {response.status}")
                        return None
        except Exception as e:
            _LOGGER.error(f"Error during sensor data retrieval: {e}")
            return None
        
    async def async_set_temperature(self, zone_id, parent_id, **kwargs):
        """Set the target temperature for a room."""
        set_temperature_url = f"{self.base_url}{SET_TEMPERATURE_PATH}"

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
            "_csrf": self.actions_csrf_token
        }

        cookies = {
            'XSRF-TOKEN': self.actions_csrf_token,
            'acceptedCookies': 'yes',
        }

        _LOGGER.debug(f"Headers: {headers}")
        _LOGGER.debug(f"Data: {data}")

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(set_temperature_url, headers=headers, cookies=cookies, data=data) as response:
                    response.raise_for_status()
                    _LOGGER.debug("Temperature set to %s for %s", temperature, zone_id)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting temperature for %s: %s", zone_id, err)


    async def close(self):
        """Close the session after usage."""
        if self.session:
            await self.session.close()
