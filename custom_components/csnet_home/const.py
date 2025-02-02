"""List of static data used within the code."""

DOMAIN = "csnet_home"
API_URL = "https://www.csnetmanager.com"
LOGIN_PATH = "/login"
ELEMENTS_PATH = "/data/elements"
HEAT_SETTINGS_PATH = "/data/indoor/heat_setting"
CONF_ENABLE_DEVICE_LOGGING = "enable_device_logging"
COMMON_API_HEADERS = {
    "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "origin": "null",
    "pragma": "no-cache",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
DEFAULT_API_TIMEOUT = 10

WATER_HEATER_MAX_TEMPERATURE = 55
WATER_HEATER_MIN_TEMPERATURE = 30

HEATING_MAX_TEMPERATURE = 35
HEATING_MIN_TEMPERATURE = 11
