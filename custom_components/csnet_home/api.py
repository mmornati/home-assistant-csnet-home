"""API Module to connect to CSNet Home."""

import asyncio
import json
import logging
import time

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant

from custom_components.csnet_home.const import (
    API_URL,
    COMMON_API_HEADERS,
    DEFAULT_API_TIMEOUT,
    ELEMENTS_PATH,
    INSTALLATION_DEVICES_PATH,
    INSTALLATION_ALARMS_PATH,
    HEAT_SETTINGS_PATH,
    LOGIN_PATH,
    LANGUAGE_FILES,
)

_LOGGER = logging.getLogger(__name__)


class CSNetHomeAPI:
    """Handles communication with the cloud service API."""

    def __init__(
        self, hass: HomeAssistant, username: str, password: str, base_url=API_URL
    ):
        """Initialize the CloudServiceAPI class with username and password."""
        self.hass = hass
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        self.cookies = None
        self.logged_in = False
        self.xsrf_token = None
        self.translations = {}
        self.installation_id = None

    async def get_xsrf_token(self):
        """Get the XSRF token from the cloud service."""
        login_url = f"{self.base_url}{LOGIN_PATH}"

        headers = COMMON_API_HEADERS | {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
        }

        cookies = {
            "acceptedCookies": "yes",
        }

        async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
            async with self.session.get(
                login_url, headers=headers, cookies=cookies, data={}
            ) as response:
                if response.status == 200:
                    _LOGGER.debug("Login page called...")
                    self.xsrf_token = self.extract_cookie_value(
                        self.session.cookie_jar, "XSRF-TOKEN"
                    )
                    return True
                _LOGGER.error(
                    "Failed to display login page. Status code: %s", response.status
                )
                return False

    async def async_login(self):
        """Log in to the cloud service and return a session cookie."""
        self.session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())
        if not await self.get_xsrf_token():
            _LOGGER.error("Failed to get XSRF token.")
            return False

        login_url = f"{self.base_url}{LOGIN_PATH}"

        headers = COMMON_API_HEADERS | {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
        }

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        form_data = {
            "_csrf": self.xsrf_token,
            "token": "",
            "username": self.username,
            "password_unsanitized": self.password,
            "password": self.password,
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    login_url, headers=headers, cookies=cookies, data=form_data
                ) as response:
                    if await self.check_logged_in(response):
                        _LOGGER.info("Login successful")
                        return True
                    _LOGGER.error("Failed to login. Status code: %s", response.status)
                    return False
        except Exception as e:
            _LOGGER.error("Error during login: %s", e)
            return False

    async def async_get_elements_data(self):
        """Get sensor data from the cloud service."""
        sensor_data_url = f"{self.base_url}{ELEMENTS_PATH}"

        if not self.session or not self.logged_in:
            _LOGGER.warning("No active session found.")
            await self.async_login()

        headers = COMMON_API_HEADERS | {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.get(
                    sensor_data_url, headers=headers, cookies=self.cookies
                ) as response:
                    data = await self.check_api_response(response)
                    if data is not None and data.get("status") == "success":
                        _LOGGER.debug("Sensor data retrieved: %s", data["data"])

                        # Parse the sensor data from the API response
                        elements = data.get("data", {}).get("elements", [])
                        sensors = []

                        # Store installation ID for alarm API calls
                        self.installation_id = data.get("data", {}).get("installation")

                        common_data = {
                            "name": data.get("data", {}).get("name"),
                            "latitude": data.get("data", {}).get("latitude"),
                            "longitude": data.get("data", {}).get("longitude"),
                            "weather_temperature": data.get("data", {}).get(
                                "weatherTemperature"
                            ),
                            "device_status": {
                                device.get("id"): {
                                    "name": device.get("name"),
                                    "status": device.get("status"),
                                    "firmware": device.get("firmware"),
                                }
                                for device in data.get("data", {}).get(
                                    "device_status", []
                                )
                            },
                        }
                        for index, element in enumerate(elements):
                            sensor = {
                                "device_name": element.get("deviceName") or "Remote",
                                "device_id": element.get("deviceId"),
                                "room_name": element.get("parentName")
                                or f"Room-{element.get('parentId')}-{index}",
                                "parent_id": element.get("parentId"),
                                "room_id": element.get("roomId"),
                                "operation_status": element.get("operationStatus"),
                                "mode": element.get(
                                    "mode"
                                ),  # 0 = cool, 1 = heat, 2 = auto
                                "real_mode": element.get("realMode"),
                                "on_off": element.get("onOff"),  # 0 = Off, 1 = On
                                "timer_running": element.get("timerRunning"),
                                "alarm_code": element.get("alarmCode"),
                                "alarm_message": self.translate_alarm(
                                    element.get("alarmCode")
                                ),
                                "c1_demand": element.get("c1Demand"),
                                "c2_demand": element.get("c2Demand"),
                                "ecocomfort": element.get(
                                    "ecocomfort"
                                ),  # 0 = Eco, 1 = Comfort, -1 = No available mode
                                "doingBoost": element.get("doingBoost"),
                                "silent_mode": element.get(
                                    "silentMode"
                                ),  # 0 = Off, 1 = On
                                "current_temperature": element.get(
                                    "currentTemperature"
                                ),
                                "setting_temperature": self.get_current_temperature(
                                    element
                                ),
                                "zone_id": element.get("elementType"),
                            }
                            sensors.append(sensor)
                        _LOGGER.debug("Retrieved Sensors: %s", sensors)
                        data_elements = {"common_data": common_data, "sensors": sensors}
                        _LOGGER.debug("Retrieved Data Elements: %s", data_elements)
                        return data_elements

                    _LOGGER.error("Error in API response, status not 'success'")
                    return None
        except Exception as e:
            _LOGGER.error("Error during sensor data retrieval: %s", e)
            self.logged_in = False
            return None

    async def async_get_installation_devices_data(self):
        """Get installation devices data from the cloud service."""
        installation_devices_url = (
            f"{self.base_url}{INSTALLATION_DEVICES_PATH}?installationId=-1"
        )

        if not self.session or not self.logged_in:
            _LOGGER.warning("No active session found.")
            await self.async_login()

        headers = COMMON_API_HEADERS | {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.get(
                    installation_devices_url, headers=headers, cookies=self.cookies
                ) as response:
                    data = await self.check_api_response(response)
                    if data is not None:
                        _LOGGER.debug("Installation devices data retrieved: %s", data)
                        return data
                    _LOGGER.error("Error in installation devices API response")
                    return None
        except Exception as e:
            _LOGGER.error("Error during installation devices data retrieval: %s", e)
            self.logged_in = False
            return None

    async def async_get_installation_alarms(self):
        """Get installation alarms data from the cloud service."""
        if not self.installation_id:
            _LOGGER.debug("No installation ID available, skipping alarm fetch")
            return None

        installation_alarms_url = (
            f"{self.base_url}{INSTALLATION_ALARMS_PATH}"
            f"?installationId={self.installation_id}&_csrf={self.xsrf_token}"
        )

        if not self.session or not self.logged_in:
            _LOGGER.warning("No active session found.")
            await self.async_login()

        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.get(
                    installation_alarms_url, headers=headers, cookies=self.cookies
                ) as response:
                    data = await self.check_api_response(response)
                    if data is not None:
                        _LOGGER.debug("Installation alarms data retrieved: %s", data)
                        return data
                    _LOGGER.error("Error in installation alarms API response")
                    return None
        except Exception as e:
            _LOGGER.error("Error during installation alarms data retrieval: %s", e)
            self.logged_in = False
            return None

    def get_current_temperature(self, element):
        """Return target/setting temperature normalized per element type.

        For elementType 5 the server encodes temperature in whole degrees
        but expects a value multiplied by 10; other types use raw value.
        """
        etype = element.get("elementType")
        if etype == 5:
            return element.get("settingTemperature") * 10
        return element.get("settingTemperature")

    def get_temperature_limits(self, zone_id, mode, installation_devices_data):
        """Extract temperature limits from installation devices data.

        Args:
            zone_id: The zone/element type (1, 2, 5, etc.)
            mode: The HVAC mode (0=cool, 1=heat, 2=auto)
            installation_devices_data: The installation devices API response

        Returns:
            Tuple of (min_temp, max_temp) or (None, None) if not available
        """
        if not installation_devices_data:
            return (None, None)

        heating_status = installation_devices_data.get("heatingStatus", {})
        if not heating_status:
            return (None, None)

        # Determine if we're in heating or cooling mode
        is_heating = mode == 1  # mode 1 is heat, mode 0 is cool

        # Zone mapping based on JavaScript code analysis:
        # zone_id 1, 2, 4 = air circuits (C1_AIR, C2_AIR)
        # zone_id 5 = water circuit (C1_WATER)
        # zone_id 3 = DHW (water heater)

        min_temp = None
        max_temp = None

        if zone_id == 1:  # Air circuit 1
            if is_heating:
                min_temp = heating_status.get("heatAirMinC1")
                max_temp = heating_status.get("heatAirMaxC1")
            else:
                min_temp = heating_status.get("coolAirMinC1")
                max_temp = heating_status.get("coolAirMaxC1")
        elif zone_id == 2:  # Air circuit 2
            if is_heating:
                min_temp = heating_status.get("heatAirMinC2")
                max_temp = heating_status.get("heatAirMaxC2")
            else:
                min_temp = heating_status.get("coolAirMinC2")
                max_temp = heating_status.get("coolAirMaxC2")
        elif zone_id == 5:  # Water circuit 1 (fixed temperature)
            if is_heating:
                min_temp = heating_status.get("heatMinC1")
                max_temp = heating_status.get("heatMaxC1")
            else:
                min_temp = heating_status.get("coolMinC1")
                max_temp = heating_status.get("coolMaxC1")
        elif zone_id == 3:  # DHW (water heater)
            # DHW typically only has a max limit, min is constant
            max_temp = heating_status.get("dhwMax")
            # Min is typically 30 for DHW

        return (min_temp, max_temp)

    async def async_set_temperature(self, zone_id, parent_id, mode, **kwargs):
        """Set the target temperature for a room."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"

        temperature = kwargs.get("temperature")

        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
        }

        data = {
            "orderStatus": "PENDING",
            "indoorId": parent_id,
            "_csrf": self.xsrf_token,
        }
        if zone_id == 3:
            data["settingTempDHW"] = str(int(temperature))
        elif zone_id == 5:
            if mode == 0:
                data["fixTempCoolC1"] = str(int(temperature))
            else:
                data["fixTempHeatC1"] = str(int(temperature))
        else:
            data[f"settingTempRoomZ{zone_id}"] = str(int(temperature * 10))

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    settings_url, headers=headers, cookies=cookies, data=data
                ) as response:
                    response.raise_for_status()
                    _LOGGER.debug("Temperature set to %s for %s", temperature, zone_id)
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting temperature for %s: %s", zone_id, err)
            return False

    async def set_water_heater_status(self, zone_id, parent_id, status):
        """Change the water heater forcing status."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"

        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
        }

        data = {
            "orderStatus": "PENDING",
            "indoorId": parent_id,
            "boostDHW": status,
            "_csrf": self.xsrf_token,
        }

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    settings_url, headers=headers, cookies=cookies, data=data
                ) as response:
                    response.raise_for_status()
                    _LOGGER.debug(
                        "Force water heater status to %s for %s", status, zone_id
                    )
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error(
                "Error forcing the water heater status for %s: %s", zone_id, err
            )
            return False

    async def async_set_hvac_mode(self, zone_id, parent_id, hvac_mode: str):
        """Set HVAC mode: HEAT, COOL, or OFF."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"

        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
        }

        # Mapping from HA mode to CSNet parameters
        hvac_mode_lower = hvac_mode.lower()
        data = {
            "id": f"{parent_id}{zone_id}",  # device id + zone id
            "updatedOn": str(int(time.time() * 1000)),  # current timestamp in ms
            "orderStatus": "PENDING",
            "indoorId": parent_id,
            "_csrf": self.xsrf_token,
        }

        # For zone_id 5 (fixed temp circuit), use C1 in parameter names
        circuit_id = 1 if zone_id == 5 else zone_id

        # Determine if this is a water circuit or air circuit
        # Zone 5 is fixed temperature water circuit, zones 1,2,4 are typically air/room thermostats
        is_water_circuit = zone_id == 5

        if hvac_mode_lower == "heat":
            data["mode"] = "1"
            if is_water_circuit:
                # Water circuits: only set runStopC{X}, not Air
                data[f"runStopC{circuit_id}"] = "1"
            else:
                # Air circuits: only set runStopC{X}Air, not water
                data[f"runStopC{circuit_id}Air"] = "1"
        elif hvac_mode_lower == "cool":
            data["mode"] = "0"
            if is_water_circuit:
                # Water circuits: only set runStopC{X}, not Air
                data[f"runStopC{circuit_id}"] = "1"
            else:
                # Air circuits: only set runStopC{X}Air, not water
                data[f"runStopC{circuit_id}Air"] = "1"
        elif hvac_mode_lower == "heat_cool":
            data["mode"] = "2"
            if is_water_circuit:
                # Water circuits: only set runStopC{X}, not Air
                data[f"runStopC{circuit_id}"] = "1"
            else:
                # Air circuits: only set runStopC{X}Air, not water
                data[f"runStopC{circuit_id}Air"] = "1"
        elif hvac_mode_lower == "off":
            # only stop — do not send "mode" to preserve last setting
            if is_water_circuit:
                # Water circuits: only set runStopC{X}, not Air
                data[f"runStopC{circuit_id}"] = "0"
            else:
                # Air circuits: only set runStopC{X}Air, not water
                data[f"runStopC{circuit_id}Air"] = "0"
        else:
            _LOGGER.warning("Unsupported hvac_mode=%s ignored", hvac_mode)
            return True

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    settings_url, headers=headers, cookies=cookies, data=data
                ) as response:
                    response_text = await response.text()
                    _LOGGER.debug(
                        "Set hvac_mode=%s with payload=%s, status=%s, response=%s",
                        hvac_mode,
                        data,
                        response.status,
                        response_text,
                    )
                    if response.status != 200:
                        _LOGGER.warning(
                            "HTTP %s for hvac_mode=%s: %s",
                            response.status,
                            hvac_mode,
                            response_text,
                        )
                        return False
                    response.raise_for_status()
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting hvac_mode=%s: %s", hvac_mode, err)
            return False

    async def set_preset_modes(
        self, zone_id, parent_id, preset_mode, current_mode=None, on_off=None
    ):
        """Set the eco/comfort mode for a zone."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"

        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
        }

        data = {
            "id": f"{parent_id}{zone_id}",  # device id + zone id
            "updatedOn": str(int(time.time() * 1000)),  # current timestamp in ms
            "orderStatus": "PENDING",
            "indoorId": parent_id,
            "_csrf": self.xsrf_token,
        }

        # For zone_id 5 (fixed temp circuit), use C1 in parameter names
        circuit_id = 1 if zone_id == 5 else zone_id

        # Determine if this is a water circuit or air circuit
        # Zone 5 is fixed temperature water circuit, zones 1,2,4 are typically air/room thermostats
        is_water_circuit = zone_id == 5

        # Include current HVAC mode and run/stop status if provided
        if current_mode is not None:
            data["mode"] = str(current_mode)
        if on_off is not None:
            if is_water_circuit:
                # Water circuits: only set runStopC{X}, not Air
                data[f"runStopC{circuit_id}"] = str(on_off)
            else:
                # Air circuits: only set runStopC{X}Air, not water
                data[f"runStopC{circuit_id}Air"] = str(on_off)

        # Set the eco/comfort mode
        if preset_mode == "eco":
            data[f"ecoModeC{circuit_id}"] = "0"
        else:
            data[f"ecoModeC{circuit_id}"] = "1"

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    settings_url, headers=headers, cookies=cookies, data=data
                ) as response:
                    response_text = await response.text()
                    _LOGGER.debug(
                        "Set preset_mode=%s for zone=%s with payload=%s, status=%s, response=%s",
                        preset_mode,
                        zone_id,
                        data,
                        response.status,
                        response_text,
                    )
                    if response.status != 200:
                        _LOGGER.warning(
                            "HTTP %s for preset_mode=%s: %s",
                            response.status,
                            preset_mode,
                            response_text,
                        )
                        return False
                    response.raise_for_status()
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting preset_mode for %s: %s", zone_id, err)
            return False

    async def set_water_heater_mode(self, zone_id, parent_id, preset_mode):
        """Set the off/eco/performance demand mode for water_heater."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"
        _LOGGER.debug("URL %s et mode %s", settings_url, preset_mode)

        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
        }

        data = {
            "orderStatus": "PENDING",
            "indoorId": parent_id,
            "_csrf": self.xsrf_token,
        }
        if preset_mode == "performance":
            data["boostDHW"] = 1
            data["runStopDHW"] = 1
        if preset_mode == "eco":
            data["boostDHW"] = 0
            data["runStopDHW"] = 1
        if preset_mode == "off":
            data["runStopDHW"] = 0
        if preset_mode == "on":
            data["runStopDHW"] = 1

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        _LOGGER.debug("Sending data (%s): ", data)

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    settings_url, headers=headers, cookies=cookies, data=data
                ) as response:
                    response.raise_for_status()
                    response_text = (
                        await response.text()
                    )  # Récupère la réponse en texte
                    _LOGGER.debug(
                        "Réponse API (%s): %s", response.status, response_text
                    )
                    _LOGGER.debug("Set preset_mode to %s for %s", preset_mode, zone_id)
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting preset_mode for %s: %s", zone_id, err)
            return False

    async def async_set_silent_mode(self, zone_id, parent_id, silent_mode: bool):
        """Set silent/quiet mode for a zone."""
        settings_url = f"{self.base_url}{HEAT_SETTINGS_PATH}"

        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": self.base_url,
        }

        # For zone_id 5 (fixed temp circuit), use C1 in parameter names
        circuit_id = 1 if zone_id == 5 else zone_id

        data = {
            "id": f"{parent_id}{zone_id}",  # device id + zone id
            "updatedOn": str(int(time.time() * 1000)),  # current timestamp in ms
            "orderStatus": "PENDING",
            "indoorId": parent_id,
            f"silentModeC{circuit_id}": "1" if silent_mode else "0",
            "_csrf": self.xsrf_token,
        }

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    settings_url, headers=headers, cookies=cookies, data=data
                ) as response:
                    response_text = await response.text()
                    _LOGGER.debug(
                        "Set silent_mode=%s for zone=%s with payload=%s, status=%s, response=%s",
                        silent_mode,
                        zone_id,
                        data,
                        response.status,
                        response_text,
                    )
                    if response.status != 200:
                        _LOGGER.warning(
                            "HTTP %s for silent_mode=%s: %s",
                            response.status,
                            silent_mode,
                            response_text,
                        )
                        return False
                    response.raise_for_status()
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error setting silent_mode for %s: %s", zone_id, err)
            return False

    async def close(self):
        """Close the session after usage."""
        if self.session:
            await self.session.close()

    async def check_logged_in(self, response):
        """Check if the login was successful.

        Args:
            response (aiohttp.ClientResponse): Response from the login request.

        Returns:
            bool: True if the login was successful, False otherwise.
        """
        page_content = await response.text()
        if response.status == 200 and 'loadContent("login")' not in page_content:
            _LOGGER.info("Login successful")
            self.logged_in = True
            return True
        _LOGGER.error("Failed to login. Status code: %s", response.status)
        self.logged_in = False
        return False

    async def check_api_response(self, response):
        """Check the API response status and return the JSON content.

        If the status is not 200, log an error and return None.
        If the response is not JSON, log an error and return None.
        If the response is JSON, return the content.
        """
        if response.status == 200:
            try:
                data = await response.json()
                return data
            except json.JSONDecodeError as e:
                _LOGGER.error("API Response error: %s", e)
                self.logged_in = False
                return None

    def extract_cookie_value(self, cookies, cookie_name):
        """Extract a cookie value from a cookie jar.

        Args:
            cookies (aiohttp.cookiejar.CookieJar): The cookie jar to extract the value from.
            cookie_name (str): The name of the cookie to extract the value from.

        Returns:
            str or None: The value of the cookie, or None if the cookie is not found.
        """
        for cookie in cookies:
            if cookie.key == cookie_name:
                _LOGGER.debug(
                    "Found cookie %s with value %s", cookie_name, cookie.value
                )
                return cookie.value
        return None

    async def load_translations(self):
        """Load translations dictionaries for alarm messages (lazy)."""
        if self.translations:
            return
        # load preferred language first, then fallback
        endpoints = []
        preferred = getattr(self, "preferred_language", None)
        if preferred and preferred in LANGUAGE_FILES:
            endpoints.append(LANGUAGE_FILES[preferred])
        # ensure both are loaded to maximize hit rate
        for key, file in LANGUAGE_FILES.items():
            if file not in endpoints:
                _LOGGER.debug("Adding language file for %s", key)
                endpoints.append(file)
        headers = COMMON_API_HEADERS | {
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
        }
        for ep in endpoints:
            url = f"{self.base_url}/translations/{ep}"
            try:
                async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            # merge/overwrite keeping last language wins for same key
                            self.translations.update(data or {})
            except Exception as e:
                _LOGGER.debug("Translation load failed for %s: %s", ep, e)

    def translate_alarm(self, code):
        """Return localized alarm message for a numeric code if available."""
        if not code:
            return None
        # Keys observed on website are like 'alarm_XX' or 'alarm_XXX'
        # Provide multiple candidates; first match wins
        key_candidates = [
            f"alarm_{code}",
            f"alarm_{int(code):02d}",
            f"alarm_{int(code):03d}",
        ]
        for key in key_candidates:
            if key in self.translations:
                return self.translations[key]
        return None
