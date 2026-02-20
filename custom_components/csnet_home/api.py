"""API Module to connect to CSNet Home."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass

import aiohttp
import async_timeout
from homeassistant.core import HomeAssistant

from custom_components.csnet_home.const import (
    API_URL,
    COMMON_API_HEADERS,
    DEFAULT_API_TIMEOUT,
    ELEMENTS_PATH,
    HEAT_SETTINGS_PATH,
    HEATING_MAX_TEMPERATURE,
    INSTALLATION_ALARMS_PATH,
    INSTALLATION_DEVICES_PATH,
    LANGUAGE_FILES,
    LOGIN_PATH,
    WATER_CIRCUIT_MAX_HEAT,
    WATER_HEATER_MAX_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class TemperatureLimitConfig:
    """Configuration for temperature limits for a zone."""

    heat_min_key: str
    heat_max_key: str
    cool_min_key: str
    cool_max_key: str
    default_max: int


TEMPERATURE_LIMIT_CONFIGS = {
    1: TemperatureLimitConfig(
        "heatAirMinC1",
        "heatAirMaxC1",
        "coolAirMinC1",
        "coolAirMaxC1",
        HEATING_MAX_TEMPERATURE,
    ),
    2: TemperatureLimitConfig(
        "heatAirMinC2",
        "heatAirMaxC2",
        "coolAirMinC2",
        "coolAirMaxC2",
        HEATING_MAX_TEMPERATURE,
    ),
    5: TemperatureLimitConfig(
        "heatMinC1", "heatMaxC1", "coolMinC1", "coolMaxC1", WATER_CIRCUIT_MAX_HEAT
    ),
    6: TemperatureLimitConfig(
        "heatMinC2", "heatMaxC2", "coolMinC2", "coolMaxC2", WATER_CIRCUIT_MAX_HEAT
    ),
}

TO_REDACT = {
    "latitude",
    "longitude",
    "ownerId",
    "installationId",
    "installation",
    "administrator",
    "user_dispayableName",
    "_csrf",
    "username",
    "password",
    "password_unsanitized",
    "token",
}

# Alarm Origin Map Constants
# Optimized for performance to avoid recreation on every call
BCD_ALARM_ORIGIN_MAP = {
    0x62: "STR_ORIGIN_INVERTER",
    0x5B: "STR_ORIGIN_OUTDOOR_FAN",
    0x5C: "STR_ORIGIN_OUTDOOR_FAN",
    0xEE: "STR_ORIGIN_COMPRESSOR",
}

ALARM_ORIGIN_MAP = {
    # Standard Map entries
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
    # Merged List entries
    # STR_ORIGIN_INDOOR list 1
    11: "STR_ORIGIN_INDOOR",
    12: "STR_ORIGIN_INDOOR",
    13: "STR_ORIGIN_INDOOR",
    14: "STR_ORIGIN_INDOOR",
    75: "STR_ORIGIN_INDOOR",
    76: "STR_ORIGIN_INDOOR",
    83: "STR_ORIGIN_INDOOR",
    # STR_ORIGIN_INDOOR list 2
    15: "STR_ORIGIN_INDOOR",
    16: "STR_ORIGIN_INDOOR",
    17: "STR_ORIGIN_INDOOR",
    18: "STR_ORIGIN_INDOOR",
    19: "STR_ORIGIN_INDOOR",
    25: "STR_ORIGIN_INDOOR",
    33: "STR_ORIGIN_INDOOR",
    34: "STR_ORIGIN_INDOOR",
    40: "STR_ORIGIN_INDOOR",
    72: "STR_ORIGIN_INDOOR",
    73: "STR_ORIGIN_INDOOR",
    74: "STR_ORIGIN_INDOOR",
    # STR_ORIGIN_OUTDOOR
    20: "STR_ORIGIN_OUTDOOR",
    21: "STR_ORIGIN_OUTDOOR",
    22: "STR_ORIGIN_OUTDOOR",
    24: "STR_ORIGIN_OUTDOOR",
    28: "STR_ORIGIN_OUTDOOR",
    29: "STR_ORIGIN_OUTDOOR",
    38: "STR_ORIGIN_OUTDOOR",
    59: "STR_ORIGIN_OUTDOOR",
    # Single value checks
    26: "STR_ORIGIN_INDOOR",
    # STR_ORIGIN_INDOOR list 3
    70: "STR_ORIGIN_INDOOR",
    71: "STR_ORIGIN_INDOOR",
    84: "STR_ORIGIN_INDOOR",
    90: "STR_ORIGIN_INDOOR",
    # STR_ORIGIN_2ND_CYCLE list
    101: "STR_ORIGIN_2ND_CYCLE",
    102: "STR_ORIGIN_2ND_CYCLE",
    103: "STR_ORIGIN_2ND_CYCLE",
    104: "STR_ORIGIN_2ND_CYCLE",
    105: "STR_ORIGIN_2ND_CYCLE",
    106: "STR_ORIGIN_2ND_CYCLE",
    124: "STR_ORIGIN_2ND_CYCLE",
    125: "STR_ORIGIN_2ND_CYCLE",
    126: "STR_ORIGIN_2ND_CYCLE",
    127: "STR_ORIGIN_2ND_CYCLE",
    128: "STR_ORIGIN_2ND_CYCLE",
    129: "STR_ORIGIN_2ND_CYCLE",
    130: "STR_ORIGIN_2ND_CYCLE",
    132: "STR_ORIGIN_2ND_CYCLE",
    134: "STR_ORIGIN_2ND_CYCLE",
    135: "STR_ORIGIN_2ND_CYCLE",
    136: "STR_ORIGIN_2ND_CYCLE",
    151: "STR_ORIGIN_2ND_CYCLE",
    152: "STR_ORIGIN_2ND_CYCLE",
    153: "STR_ORIGIN_2ND_CYCLE",
    154: "STR_ORIGIN_2ND_CYCLE",
    155: "STR_ORIGIN_2ND_CYCLE",
    156: "STR_ORIGIN_2ND_CYCLE",
    157: "STR_ORIGIN_2ND_CYCLE",
    # STR_ORIGIN_INDOOR list 4
    202: "STR_ORIGIN_INDOOR",
    203: "STR_ORIGIN_INDOOR",
    204: "STR_ORIGIN_INDOOR",
    205: "STR_ORIGIN_INDOOR",
    # STR_ORIGIN_CASCADE_CONTROLLER
    208: "STR_ORIGIN_CASCADE_CONTROLLER",
    209: "STR_ORIGIN_CASCADE_CONTROLLER",
    # STR_ORIGIN_CASCADE_MODULE
    211: "STR_ORIGIN_CASCADE_MODULE",
    212: "STR_ORIGIN_CASCADE_MODULE",
    213: "STR_ORIGIN_CASCADE_MODULE",
    214: "STR_ORIGIN_CASCADE_MODULE",
    215: "STR_ORIGIN_CASCADE_MODULE",
    216: "STR_ORIGIN_CASCADE_MODULE",
    217: "STR_ORIGIN_CASCADE_MODULE",
    218: "STR_ORIGIN_CASCADE_MODULE",
    # STR_ORIGIN_UNIT_CONTROLLER
    220: "STR_ORIGIN_UNIT_CONTROLLER",
}


def redact_data(data):
    """Redact sensitive keys from a dictionary or list."""
    if isinstance(data, dict):
        return {
            k: redact_data(v) if k not in TO_REDACT else "**REDACTED**"
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact_data(i) for i in data]
    return data


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
        if self.session is None or self.session.closed:
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

        # CSNet API requires password field to replace % with # (as done in csnet.js)
        password_sanitized = self.password.replace("%", "#") if self.password else ""

        form_data = {
            "_csrf": self.xsrf_token,
            "token": "",
            "username": self.username,
            "password_unsanitized": self.password,
            "password": password_sanitized,
        }

        try:
            async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                async with self.session.post(
                    login_url, headers=headers, cookies=cookies, data=form_data
                ) as response:
                    if await self.check_logged_in(response):
                        _LOGGER.info("Login successful")
                        return True
                    _LOGGER.error("Login failed. Status code: %s", response.status)
                    return False
        except Exception as e:
            _LOGGER.error("Login exception: %s", e, exc_info=True)
            return False

    @staticmethod
    async def async_validate_credentials(
        hass: HomeAssistant, username: str, password: str, base_url: str = API_URL
    ) -> bool:
        """Validate credentials by attempting to login.

        This is a standalone method that creates a temporary API instance,
        attempts to login, and returns whether the credentials are valid.
        The session is properly cleaned up after validation.

        Args:
            hass: HomeAssistant instance
            username: CSNet username
            password: CSNet password
            base_url: Base URL for the API (defaults to API_URL constant)

        Returns:
            bool: True if credentials are valid, False otherwise
        """
        _LOGGER.info("Starting credential validation for user: %s", username)
        # Create a temporary API instance for validation
        temp_api = CSNetHomeAPI(hass, username, password, base_url)
        # Pre-create the session so it is always available for cleanup
        temp_api.session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())

        try:
            # Attempt to login with the provided credentials
            _LOGGER.debug("Attempting login for credential validation")
            login_success = await temp_api.async_login()
            _LOGGER.info(
                "Credential validation result: %s",
                "SUCCESS" if login_success else "FAILED",
            )
            return login_success
        except Exception as e:
            _LOGGER.error("Credential validation exception: %s", e, exc_info=True)
            return False
        finally:
            # Always clean up the session
            try:
                await temp_api.session.close()
                _LOGGER.debug("Validation session closed successfully")
            except Exception as e:
                _LOGGER.debug("Error closing validation session: %s", e)

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
                # Use cookies from session if self.cookies is not set
                # aiohttp will automatically use cookies from cookie_jar if cookies=None
                request_cookies = self.cookies if self.cookies else None
                async with self.session.get(
                    sensor_data_url, headers=headers, cookies=request_cookies
                ) as response:
                    data = await self.check_api_response(response)
                    if data is not None and data.get("status") == "success":
                        _LOGGER.debug(
                            "Sensor data retrieved: %s", redact_data(data["data"])
                        )

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
                        _LOGGER.debug("Retrieved Sensors: %s", redact_data(sensors))
                        data_elements = {"common_data": common_data, "sensors": sensors}
                        _LOGGER.debug(
                            "Retrieved Data Elements: %s", redact_data(data_elements)
                        )
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
                # Use cookies from session if self.cookies is not set
                # aiohttp will automatically use cookies from cookie_jar if cookies=None
                request_cookies = self.cookies if self.cookies else None
                async with self.session.get(
                    installation_devices_url, headers=headers, cookies=request_cookies
                ) as response:
                    data = await self.check_api_response(response)
                    if data is not None:
                        _LOGGER.debug(
                            "Installation devices data retrieved: %s", redact_data(data)
                        )
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
                # Use cookies from session if self.cookies is not set
                # aiohttp will automatically use cookies from cookie_jar if cookies=None
                request_cookies = self.cookies if self.cookies else None
                async with self.session.get(
                    installation_alarms_url, headers=headers, cookies=request_cookies
                ) as response:
                    data = await self.check_api_response(response)
                    if data is not None:
                        _LOGGER.debug(
                            "Installation alarms data retrieved: %s", redact_data(data)
                        )
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
        if not installation_devices_data:
            return None

        # Try direct access first (if already extracted)
        heating_status = installation_devices_data.get("heatingStatus")
        if heating_status:
            return heating_status

        # Navigate through: data[0].indoors[0].heatingStatus
        data_array = installation_devices_data.get("data", [])
        if isinstance(data_array, list) and len(data_array) > 0:
            first_device = data_array[0]
            if isinstance(first_device, dict):
                indoors_array = first_device.get("indoors", [])
                if isinstance(indoors_array, list) and len(indoors_array) > 0:
                    first_indoors = indoors_array[0]
                    if isinstance(first_indoors, dict):
                        return first_indoors.get("heatingStatus", {})

        return None

    def get_heating_setting_from_installation_devices(self, installation_devices_data):
        """Extract heatingSetting from installation devices data structure.

        Navigates through: data[0].indoors[0].heatingSetting

        Args:
            installation_devices_data: The installation devices API response

        Returns:
            dict or None: heatingSetting dictionary, or None if not found
        """
        if not installation_devices_data:
            return None

        # Try direct access first (if already extracted)
        heating_setting = installation_devices_data.get("heatingSetting")
        if heating_setting:
            return heating_setting

        # Navigate through: data[0].indoors[0].heatingSetting
        data_array = installation_devices_data.get("data", [])
        if isinstance(data_array, list) and len(data_array) > 0:
            first_device = data_array[0]
            if isinstance(first_device, dict):
                indoors_array = first_device.get("indoors", [])
                if isinstance(indoors_array, list) and len(indoors_array) > 0:
                    first_indoors = indoors_array[0]
                    if isinstance(first_indoors, dict):
                        return first_indoors.get("heatingSetting", {})

        return None

    def _validate_value(self, value, default):
        """Validate temperature limit value matching JavaScript validateValue logic.

        Args:
            value: The value to validate (can be None, int, float)
            default: The default value to return if validation fails

        Returns:
            The validated value or default if value is None, 0, or -1

        This matches the JavaScript validateValue function:
        function validateValue(v, def) {
            if (v != null && v != undefined && v != 0 && v != -1)
                return v;
            return def;
        }
        """
        if value is None:
            return default
        try:
            val = float(value)
            # Check if value is 0 or -1 (invalid sentinel values)
            if val in (0, -1):
                return default
            return val
        except (TypeError, ValueError):
            return default

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
        # SWP has fixed temperature range regardless of installation data
        if zone_id == 4:  # SWP (swimming pool)
            return (24, 33)

        if not installation_devices_data:
            return (None, None)

        heating_status = self.get_heating_status_from_installation_devices(
            installation_devices_data
        )
        if not heating_status:
            return (None, None)

        # Handle DHW (Zone 3) separately as it doesn't follow standard patterns
        if zone_id == 3:  # DHW (water heater)
            # DHW typically only has a max limit, min is constant
            raw_max = heating_status.get("dhwMax")
            # Validate with DHW_MAX default (80°C)
            max_temp = self._validate_value(raw_max, WATER_HEATER_MAX_TEMPERATURE)
            # Min is typically 30 for DHW, not provided by API
            return (None, max_temp)

        # Check for configured zone logic
        config = TEMPERATURE_LIMIT_CONFIGS.get(zone_id)
        if not config:
            return (None, None)

        # Determine if we're in heating or cooling mode
        is_heating = mode == 1  # mode 1 is heat, mode 0 is cool

        if is_heating:
            raw_min = heating_status.get(config.heat_min_key)
            raw_max = heating_status.get(config.heat_max_key)
        else:
            raw_min = heating_status.get(config.cool_min_key)
            raw_max = heating_status.get(config.cool_max_key)

        max_temp = self._validate_value(raw_max, config.default_max)
        min_temp = raw_min

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
        elif zone_id == 4:
            data["settingTempSWP"] = str(int(temperature))
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

        # Determine the correct key for run/stop based on circuit type
        run_stop_key = f"runStopC{circuit_id}"
        if not is_water_circuit:
            run_stop_key += "Air"

        # Mapping from HA mode to CSNet parameters
        mode_mapping = {
            "heat": "1",
            "cool": "0",
            "heat_cool": "2",
        }

        if hvac_mode_lower in mode_mapping:
            data["mode"] = mode_mapping[hvac_mode_lower]
            data[run_stop_key] = "1"
        elif hvac_mode_lower == "off":
            # only stop — do not send "mode" to preserve last setting
            data[run_stop_key] = "0"
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
                        redact_data(data),
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
                        redact_data(data),
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
        """Set the off/eco/performance demand mode for water_heater and swimming pool.

        For DHW (zone_id=3): supports eco/performance/off
        For SWP (zone_id=4): supports on/off only
        """
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

        if zone_id == 3:  # DHW (water heater)
            if preset_mode == "performance":
                data["boostDHW"] = 1
                data["runStopDHW"] = 1
            elif preset_mode == "eco":
                data["boostDHW"] = 0
                data["runStopDHW"] = 1
            elif preset_mode == "off":
                data["runStopDHW"] = 0
            elif preset_mode == "on":
                data["runStopDHW"] = 1
        elif zone_id == 4:  # SWP (swimming pool)
            if preset_mode == "on":
                data["runStopSWP"] = 1
            elif preset_mode == "off":
                data["runStopSWP"] = 0

        cookies = {
            "XSRF-TOKEN": self.xsrf_token,
            "acceptedCookies": "yes",
        }

        _LOGGER.debug("Sending data (%s): ", redact_data(data))

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
                        redact_data(data),
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
                        redact_data(data),
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
        if not heating_status:
            return False

        system_config_bits = heating_status.get("systemConfigBits", 0)
        return (system_config_bits & 0x2000) > 0

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
        if not self.is_fan_coil_compatible(installation_devices_data):
            return False

        heating_status = self.get_heating_status_from_installation_devices(
            installation_devices_data
        )
        if not heating_status:
            return False

        # Get the fan control flag for the circuit
        fan_control_key = f"fan{circuit}ControlledOnLCD"
        fan_controlled = heating_status.get(fan_control_key, 0)

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
                    "Found cookie %s with value %s",
                    cookie_name,
                    "**REDACTED**" if cookie_name in TO_REDACT else cookie.value,
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

        # Zone 4 is swimming pool
        if zone_id == 4:
            return "swimming_pool"

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
            origin_key = BCD_ALARM_ORIGIN_MAP.get(raw_value)

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
            origin_key = ALARM_ORIGIN_MAP.get(value)

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
