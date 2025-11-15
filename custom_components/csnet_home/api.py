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
from .helpers import (
    extract_heating_setting,
    extract_heating_status,
    has_fan_coil_support,
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
                                    "lastComm": device.get("lastComm"),
                                    "rssi": device.get("rssi"),
                                    "currentTimeMillis": device.get(
                                        "currentTimeMillis"
                                    ),
                                }
                                for device in data.get("data", {}).get(
                                    "device_status", []
                                )
                            },
                        }
                        for index, element in enumerate(elements):
                            alarm_code = element.get("alarmCode")
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
                                "alarm_code": alarm_code,
                                "alarm_message": self.translate_alarm(alarm_code),
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
                                "fan1_speed": element.get(
                                    "fan1Speed"
                                ),  # Fan speed for C1 circuit
                                "fan2_speed": element.get(
                                    "fan2Speed"
                                ),  # Fan speed for C2 circuit
                            }

                            # Add enhanced alarm fields
                            # Note: installation_devices_data is not available here,
                            # but coordinator can enrich with this data later if needed
                            sensor["unit_type"] = self.get_unit_type(sensor, None)
                            sensor["alarm_code_formatted"] = (
                                self.get_alarm_code_formatted(alarm_code)
                            )
                            sensor["alarm_origin"] = self.get_alarm_origin(
                                alarm_code, sensor["unit_type"], None
                            )

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

    def get_heating_status_from_installation_devices(self, installation_devices_data):
        """Extract heatingStatus from installation devices data structure.

        Navigates through: data[0].indoors[0].heatingStatus

        Args:
            installation_devices_data: The installation devices API response

        Returns:
            dict or None: heatingStatus dictionary, or None if not found
        """
        return extract_heating_status(installation_devices_data)

    def get_heating_setting_from_installation_devices(self, installation_devices_data):
        """Extract heatingSetting from installation devices data structure.

        Navigates through: data[0].indoors[0].heatingSetting

        Args:
            installation_devices_data: The installation devices API response

        Returns:
            dict or None: heatingSetting dictionary, or None if not found
        """
        return extract_heating_setting(installation_devices_data)

    def get_temperature_limits(self, zone_id, mode, installation_devices_data):
        """Extract temperature limits from installation devices data.

        Args:
            zone_id: The zone/element type (1, 2, 5, 6, 3)
            mode: The HVAC mode (0=cool, 1=heat, 2=auto)
            installation_devices_data: The installation devices API response

        Returns:
            Tuple of (min_temp, max_temp) or (None, None) if not available

        Zone mapping based on JavaScript code:
        - zone_id 1 = C1_AIR (air circuit 1) - max 35°C (RTU_MAX)
        - zone_id 2 = C2_AIR (air circuit 2) - max 35°C (RTU_MAX)
        - zone_id 5 = C1_WATER (water circuit 1) - max 80°C (C1_MAX_HEAT)
        - zone_id 6 = C2_WATER (water circuit 2) - max 80°C (C2_MAX_HEAT)
        - zone_id 3 = DHW (water heater) - max 80°C (DHW_MAX)
        """
        if not installation_devices_data:
            return (None, None)

        heating_status = self.get_heating_status_from_installation_devices(
            installation_devices_data
        )
        if not heating_status:
            return (None, None)

        # Determine if we're in heating or cooling mode
        is_heating = mode == 1  # mode 1 is heat, mode 0 is cool

        min_temp = None
        max_temp = None

        if zone_id == 1:  # Air circuit 1 (C1_AIR)
            if is_heating:
                min_temp = heating_status.get("heatAirMinC1")
                max_temp = heating_status.get("heatAirMaxC1")
            else:
                min_temp = heating_status.get("coolAirMinC1")
                max_temp = heating_status.get("coolAirMaxC1")
        elif zone_id == 2:  # Air circuit 2 (C2_AIR)
            if is_heating:
                min_temp = heating_status.get("heatAirMinC2")
                max_temp = heating_status.get("heatAirMaxC2")
            else:
                min_temp = heating_status.get("coolAirMinC2")
                max_temp = heating_status.get("coolAirMaxC2")
        elif zone_id == 5:  # Water circuit 1 (C1_WATER)
            if is_heating:
                min_temp = heating_status.get("heatMinC1")
                max_temp = heating_status.get("heatMaxC1")
            else:
                min_temp = heating_status.get("coolMinC1")
                max_temp = heating_status.get("coolMaxC1")
        elif zone_id == 6:  # Water circuit 2 (C2_WATER)
            if is_heating:
                min_temp = heating_status.get("heatMinC2")
                max_temp = heating_status.get("heatMaxC2")
            else:
                min_temp = heating_status.get("coolMinC2")
                max_temp = heating_status.get("coolMaxC2")
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
        elif zone_id == 5:  # C1_WATER
            if mode == 0:  # Cooling mode
                data["fixTempCoolC1"] = str(int(temperature))
            else:  # Heating mode
                data["fixTempHeatC1"] = str(int(temperature))
        elif zone_id == 6:  # C2_WATER
            if mode == 0:  # Cooling mode
                data["fixTempCoolC2"] = str(int(temperature))
            else:  # Heating mode
                data["fixTempHeatC2"] = str(int(temperature))
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

    async def async_set_fixed_water_temperature(
        self, circuit: int, parent_id: int, mode: int, temperature: float
    ):
        """Set fixed water temperature for a circuit.

        This is only valid when OTC type is "FIX" (Fixed mode).
        For water circuits (C1_WATER, C2_WATER), this sets the fixed water temperature
        that is used when OTC type is set to Fixed mode.

        Args:
            circuit: Circuit number (1 for C1, 2 for C2)
            parent_id: Parent device ID (indoor unit ID)
            mode: HVAC mode (0=cool, 1=heat, 2=auto)
            temperature: Temperature value to set

        Returns:
            bool: True if successful, False otherwise
        """
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
            "_csrf": self.xsrf_token,
        }

        # Set the appropriate fixed temperature field based on circuit and mode
        if mode == 1:  # Heating mode
            data[f"fixTempHeatC{circuit}"] = str(int(temperature))
        elif mode == 0:  # Cooling mode
            data[f"fixTempCoolC{circuit}"] = str(int(temperature))
        elif mode == 2:  # Auto mode - set both heating and cooling
            data[f"fixTempHeatC{circuit}"] = str(int(temperature))
            data[f"fixTempCoolC{circuit}"] = str(int(temperature))
        else:
            _LOGGER.warning("Invalid mode %s for fixed water temperature", mode)
            return False

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
                        "Fixed water temperature set to %s for circuit %s (mode %s)",
                        temperature,
                        circuit,
                        mode,
                    )
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error(
                "Error setting fixed water temperature for circuit %s: %s", circuit, err
            )
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

    async def async_set_fan_speed(
        self, zone_id, parent_id, fan_speed: int, circuit: int = 1
    ):
        """Set fan speed for a fan coil circuit.

        Args:
            zone_id: The zone/element type
            parent_id: The parent device ID
            fan_speed: Fan speed value (0=off, 1=low, 2=medium, 3=auto)
            circuit: Circuit number (1 for C1, 2 for C2)
        """
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
            f"fan{circuit}Speed": str(fan_speed),
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
                        "Set fan_speed=%s for zone=%s circuit=%s with payload=%s, status=%s, response=%s",
                        fan_speed,
                        zone_id,
                        circuit,
                        data,
                        response.status,
                        response_text,
                    )
                    if response.status != 200:
                        _LOGGER.warning(
                            "HTTP %s for fan_speed=%s: %s",
                            response.status,
                            fan_speed,
                            response_text,
                        )
                        return False
                    response.raise_for_status()
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error(
                "Error setting fan_speed for %s circuit %s: %s", zone_id, circuit, err
            )
            return False

    def is_fan_coil_compatible(self, installation_devices_data):
        """Check if the system supports fan coil control.

        Args:
            installation_devices_data: The installation devices API response

        Returns:
            bool: True if fan coil compatible (systemConfigBits & 0x2000)
        """
        if not installation_devices_data:
            return False

        heating_status = self.get_heating_status_from_installation_devices(
            installation_devices_data
        )
        heating_setting = self.get_heating_setting_from_installation_devices(
            installation_devices_data
        )
        return has_fan_coil_support(heating_status, heating_setting)

    def get_fan_control_availability(
        self, circuit: int, mode: int, installation_devices_data
    ):
        """Check if fan control is available for a specific circuit and mode.

        Args:
            circuit: Circuit number (1 for C1, 2 for C2)
            mode: HVAC mode (0=cool, 1=heat, 2=auto)
            installation_devices_data: The installation devices API response

        Returns:
            bool: True if fan control is available
        """
        if not installation_devices_data:
            return False

        heating_status = self.get_heating_status_from_installation_devices(
            installation_devices_data
        )
        heating_setting = self.get_heating_setting_from_installation_devices(
            installation_devices_data
        )

        if not has_fan_coil_support(heating_status, heating_setting):
            return False

        if not isinstance(heating_status, dict):
            return False

        # Get the fan control flag for the circuit
        fan_control_key = f"fan{circuit}ControlledOnLCD"
        fan_controlled = heating_status.get(fan_control_key, 0)

        # Check if fan speed field exists in heatingSetting (fallback for older units)
        # If it exists, allow control even if LCD flags are 0
        fan_speed_key = f"fan{circuit}Speed"
        has_fan_speed_field = (
            isinstance(heating_setting, dict)
            and fan_speed_key in heating_setting
            and isinstance(heating_setting[fan_speed_key], int)
            and heating_setting[fan_speed_key] >= 0
        )

        # If fan speed field exists but LCD flag is 0, allow control (older firmware)
        if has_fan_speed_field and fan_controlled == 0:
            return True

        # fanXControlledOnLCD values: 0=No, 1=Heating, 2=Cooling, 3=Heating+Cooling
        if mode == 1:  # Heat mode
            return fan_controlled in [1, 3]
        if mode == 0:  # Cool mode
            return fan_controlled in [2, 3]
        if mode == 2:  # Auto mode
            return fan_controlled == 3

        return False

    def is_fixed_water_temperature_editable(
        self, circuit: int, mode: int, installation_devices_data
    ):
        """Check if fixed water temperature is editable for a circuit.

        Fixed water temperature is only editable when OTC (Outdoor Temperature
        Compensation) type is set to "FIX" (Fixed mode). When using law/curve/gradient
        OTC types, the temperature is automatically calculated and cannot be set manually.

        Args:
            circuit: Circuit number (1 for C1, 2 for C2)
            mode: HVAC mode (0=cool, 1=heat, 2=auto)
            installation_devices_data: The installation devices API response

        Returns:
            bool: True if fixed water temperature can be edited, False otherwise
        """
        if not installation_devices_data:
            return False

        heating_status = self.get_heating_status_from_installation_devices(
            installation_devices_data
        )
        if not heating_status:
            return False

        # For heating mode (1), check if otcTypeHeatC{X} == OTC_HEATING_TYPE_FIX (3)
        # For cooling mode (0), check if otcTypeCoolC{X} == OTC_COOLING_TYPE_FIX (2)
        if mode == 1:  # Heating mode
            otc_key = f"otcTypeHeatC{circuit}"
            otc_type = heating_status.get(otc_key, 0)
            # OTC_HEATING_TYPE_FIX = 3
            return otc_type == 3
        if mode == 0:  # Cooling mode
            otc_key = f"otcTypeCoolC{circuit}"
            otc_type = heating_status.get(otc_key, 0)
            # OTC_COOLING_TYPE_FIX = 2
            return otc_type == 2
        if mode == 2:  # Auto mode - check both heating and cooling
            otc_heat_key = f"otcTypeHeatC{circuit}"
            otc_cool_key = f"otcTypeCoolC{circuit}"
            otc_heat_type = heating_status.get(otc_heat_key, 0)
            otc_cool_type = heating_status.get(otc_cool_key, 0)
            # In auto mode, editable if either heating or cooling is FIX
            return otc_heat_type == 3 or otc_cool_type == 2

        return False

    def get_fixed_water_temperature(
        self, circuit: int, mode: int, installation_devices_data
    ):
        """Get the current fixed water temperature for a circuit.

        Args:
            circuit: Circuit number (1 for C1, 2 for C2)
            mode: HVAC mode (0=cool, 1=heat, 2=auto)
            installation_devices_data: The installation devices API response

        Returns:
            float or None: Fixed water temperature value, or None if not available
        """
        if not installation_devices_data:
            return None

        heating_setting = self.get_heating_setting_from_installation_devices(
            installation_devices_data
        )
        if not heating_setting:
            return None

        # For heating mode, get fixTempHeatC{X}
        # For cooling mode, get fixTempCoolC{X}
        if mode == 1:  # Heating mode
            temp_key = f"fixTempHeatC{circuit}"
            return heating_setting.get(temp_key)
        if mode == 0:  # Cooling mode
            temp_key = f"fixTempCoolC{circuit}"
            return heating_setting.get(temp_key)
        # For auto mode, prefer heating temperature if available
        if mode == 2:  # Auto mode
            temp_heat_key = f"fixTempHeatC{circuit}"
            temp_cool_key = f"fixTempCoolC{circuit}"
            # Return heating temp if available, otherwise cooling temp
            temp = heating_setting.get(temp_heat_key)
            if temp is not None:
                return temp
            return heating_setting.get(temp_cool_key)

        return None

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

    def has_alarm_letter(self, alarm_code: int) -> bool:
        """Check if alarm code has letter format (BCD encoded)."""
        if alarm_code is None:
            return False
        return (alarm_code & 0xFF00) > 0

    def reverse_bcd(self, val: int) -> int:
        """Reverse BCD conversion for alarm codes."""
        aux1 = (val // 10) - 1
        aux2 = (val % 10) + 10
        return (aux1 * 16) + aux2

    def get_alarm_code_formatted(self, alarm_code: int) -> str:
        """Format alarm code as hex (if BCD) or decimal."""
        if alarm_code is None or alarm_code == 0:
            return "0"

        if self.has_alarm_letter(alarm_code):
            # Extract low byte and convert it to hex directly (BCD format)
            code_parsed = alarm_code & 0x00FF
            return format(code_parsed, "X")
        return str(alarm_code)

    def get_correct_rad_hex_error_code(self, alarm_code: int) -> int:
        """Apply RAD unit alarm code correction."""
        if alarm_code is None:
            return 0
        if alarm_code in (61, 63):
            return alarm_code
        if alarm_code <= 0:
            return alarm_code
        if alarm_code < 113:
            return alarm_code - 0x0A
        if alarm_code < 130:
            return alarm_code - 0x70
        return alarm_code - 0x1C

    def get_unit_type(
        self, sensor_data: dict, installation_devices_data: dict = None
    ) -> str:
        """Detect unit type based on sensor data and installation configuration."""
        zone_id = sensor_data.get("zone_id")

        # Zone 3 is typically DHW (water heater)
        if zone_id == 3:
            return "water_heater"

        # Zone 5 is typically water circuit (Yutaki/Hydro)
        if zone_id == 5:
            return "yutaki"

        # Check installation_devices_data for more specific type detection
        if installation_devices_data:
            heating_status = installation_devices_data.get("heatingStatus", {})
            system_config_bits = heating_status.get("systemConfigBits", 0)

            # Check for fan coil system (bit 0x2000)
            if (system_config_bits & 0x2000) > 0:
                return "fan_coil"

        # Default to standard air unit
        return "standard"

    def is_yutaki(
        self, sensor_data: dict, installation_devices_data: dict = None
    ) -> bool:
        """Check if unit is a Yutaki (water module) system."""
        unit_type = self.get_unit_type(sensor_data, installation_devices_data)
        return unit_type in ["yutaki", "water_heater"]

    def get_alarm_origin(
        self, alarm_code: int, unit_type: str, installation_devices_data: dict = None
    ) -> str:
        """Get alarm origin description based on code and unit type."""
        # Only provide origin for Yutaki/water systems
        if unit_type not in ["yutaki", "water_heater"]:
            return ""

        if alarm_code is None or alarm_code == 0:
            return ""

        is_bcd = self.has_alarm_letter(alarm_code)

        # Extract the raw byte value first (before reversing)
        raw_value = (alarm_code & 0x00FF) if is_bcd else alarm_code

        # Note: R290 and mirror unit detection would be done here if
        # installation_devices_data is expanded in the future

        # Map alarm codes to origin keys based on JavaScript implementation
        origin_key = None

        # BCD-specific origins (check raw value BEFORE reversing)
        # Note: raw_value is the hex byte value (e.g., 0x62 = 98 decimal)
        if is_bcd:
            if raw_value == 0x62:
                origin_key = "STR_ORIGIN_INVERTER"
            elif raw_value in [0x5B, 0x5C]:  # 91, 92 in hex
                origin_key = "STR_ORIGIN_OUTDOOR_FAN"
            elif raw_value == 0xEE:  # 238 in hex
                origin_key = "STR_ORIGIN_COMPRESSOR"

        # If we found a BCD-specific origin, return it
        if origin_key and origin_key in self.translations:
            return self.translations[origin_key]

        # Now reverse the value for standard lookup
        if is_bcd:
            value = self.reverse_bcd(raw_value)
        else:
            value = alarm_code

        # Standard alarm code origins
        if not origin_key:
            origin_map = {
                2: "STR_REFRIGERANT_CYCLE",
                3: "STR_ORIGIN_TRANSMISSION",
                4: "STR_ORIGIN_TRANSMISSION",
                5: "STR_ORIGIN_POWER_SUPPLY",
                6: "STR_ORIGIN_VOLTAGE",
                7: "STR_REFRIGERANT_CYCLE",
                8: "STR_REFRIGERANT_CYCLE",
                10: "STR_ORIGIN_INDOOR",
                23: "STR_ORIGIN_2ND_CYCLE",
                27: "STR_ORIGIN_OUTDOOR",
                31: "STR_ORIGIN_SYSTEM",
                35: "STR_ORIGIN_SYSTEM",
                36: "STR_ORIGIN_SYSTEM",
                41: "STR_ORIGIN_INDOOR",
                42: "STR_REFRIGERANT_CYCLE",
                43: "STR_REFRIGERANT_CYCLE",
                44: "STR_REFRIGERANT_CYCLE",
                45: "STR_REFRIGERANT_CYCLE",
                46: "STR_REFRIGERANT_CYCLE",
                47: "STR_REFRIGERANT_CYCLE",
                48: "STR_ORIGIN_INVERTER",
                49: "STR_REFRIGERANT_CYCLE",
                51: "STR_ORIGIN_INVERTER",
                53: "STR_ORIGIN_INVERTER",
                54: "STR_ORIGIN_INVERTER",
                55: "STR_ORIGIN_INVERTER",
                57: "STR_ORIGIN_OUTDOOR_FAN",
                60: "STR_ORIGIN_COMUNICATION",
                61: "STR_ORIGIN_COMUNICATION",
                77: "STR_ORIGIN_INDOOR_UNIT_CONTROLLER",
                78: "STR_ORIGIN_INDOOR_UNIT_CONTROLLER",
                79: "STR_ORIGIN_SYSTEM",
                80: "STR_ORIGIN_INDOOR_UNIT_CONTROLLER",
                81: "STR_ORIGIN_INDOOR",
                85: "STR_ORIGIN_INDOOR",
                91: "STR_ORIGIN_OUTDOOR_FAN",
                92: "STR_ORIGIN_OUTDOOR_FAN",
                238: "STR_ORIGIN_COMPRESSOR",
            }

            # Group mappings for similar origins
            if value in [11, 12, 13, 14, 75, 76, 83]:
                origin_key = "STR_ORIGIN_INDOOR"
            elif value in [15, 16, 17, 18, 19, 25, 33, 34, 40, 72, 73, 74]:
                origin_key = "STR_ORIGIN_INDOOR"
            elif value in [20, 21, 22, 24, 28, 29, 38, 59]:
                origin_key = "STR_ORIGIN_OUTDOOR"
            elif value == 26:
                origin_key = "STR_ORIGIN_INDOOR"
            elif value in [70, 71, 84, 90]:
                origin_key = "STR_ORIGIN_INDOOR"
            elif value in [
                101,
                102,
                103,
                104,
                105,
                106,
                124,
                125,
                126,
                127,
                128,
                129,
                130,
                132,
                134,
                135,
                136,
                151,
                152,
                153,
                154,
                155,
                156,
                157,
            ]:
                origin_key = "STR_ORIGIN_2ND_CYCLE"
            elif value in [202, 203, 204, 205]:
                origin_key = "STR_ORIGIN_INDOOR"
            elif value in [208, 209]:
                origin_key = "STR_ORIGIN_CASCADE_CONTROLLER"
            elif value in [211, 212, 213, 214, 215, 216, 217, 218]:
                origin_key = "STR_ORIGIN_CASCADE_MODULE"
            elif value == 220:
                origin_key = "STR_ORIGIN_UNIT_CONTROLLER"
            else:
                origin_key = origin_map.get(value)

        # Translate the origin key if found
        if origin_key and origin_key in self.translations:
            return self.translations[origin_key]

        return ""

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
