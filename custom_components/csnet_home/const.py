"""List of static data used within the code."""

DOMAIN = "csnet_home"
API_URL = "https://www.csnetmanager.com"
LOGIN_PATH = "/login"
ELEMENTS_PATH = "/data/elements"
INSTALLATION_DEVICES_PATH = "/data/installationdevices"
INSTALLATION_ALARMS_PATH = "/data/installationalarms"
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

SWIMMING_POOL_MAX_TEMPERATURE = 33
SWIMMING_POOL_MIN_TEMPERATURE = 24

HEATING_MAX_TEMPERATURE = 55
HEATING_MIN_TEMPERATURE = 8

# Fan Speed Control (for fan coil systems)
FAN_SPEED_OFF = "0"
FAN_SPEED_LOW = "1"
FAN_SPEED_MEDIUM = "2"
FAN_SPEED_AUTO = "3"

FAN_SPEED_MAP = {
    "off": 0,
    "low": 1,
    "medium": 2,
    "auto": 3,
}

FAN_SPEED_REVERSE_MAP = {
    0: "off",
    1: "low",
    2: "medium",
    3: "auto",
}

# Operation Status Constants
OPST_OFF = 0
OPST_COOL_D_OFF = 1
OPST_COOL_T_OFF = 2
OPST_COOL_T_ON = 3
OPST_HEAT_D_OFF = 4
OPST_HEAT_T_OFF = 5
OPST_HEAT_T_ON = 6
OPST_DHW_OFF = 7
OPST_DHW_ON = 8
OPST_SWP_OFF = 9
OPST_SWP_ON = 10
OPST_ALARM = 11

# Operation Status Description Map
OPERATION_STATUS_MAP = {
    OPST_OFF: "Off",
    OPST_COOL_D_OFF: "Cooling Demand Off",
    OPST_COOL_T_OFF: "Cooling Thermostat Off",
    OPST_COOL_T_ON: "Cooling Thermostat On",
    OPST_HEAT_D_OFF: "Heating Demand Off",
    OPST_HEAT_T_OFF: "Heating Thermostat Off",
    OPST_HEAT_T_ON: "Heating Thermostat On",
    OPST_DHW_OFF: "Domestic Hot Water Off",
    OPST_DHW_ON: "Domestic Hot Water On",
    OPST_SWP_OFF: "Swimming Pool Off",
    OPST_SWP_ON: "Swimming Pool On",
    OPST_ALARM: "Alarm",
}

# Localization
CONF_LANGUAGE = "language"
DEFAULT_LANGUAGE = "en"
LANGUAGE_FILES = {
    "en": "english.json",
    "fr": "french.json",
}

# OTC (Outdoor Temperature Compensation) Constants
# Heating OTC Types
OTC_HEATING_TYPE_NONE = 0
OTC_HEATING_TYPE_POINTS = 1
OTC_HEATING_TYPE_GRADIENT = 2
OTC_HEATING_TYPE_FIX = 3

# Cooling OTC Types
OTC_COOLING_TYPE_NONE = 0
OTC_COOLING_TYPE_POINTS = 1
OTC_COOLING_TYPE_FIX = 2

# OTC Type Names (for display)
OTC_HEATING_TYPE_NAMES = {
    OTC_HEATING_TYPE_NONE: "None",
    OTC_HEATING_TYPE_POINTS: "Points",
    OTC_HEATING_TYPE_GRADIENT: "Gradient",
    OTC_HEATING_TYPE_FIX: "Fixed",
}

OTC_COOLING_TYPE_NAMES = {
    OTC_COOLING_TYPE_NONE: "None",
    OTC_COOLING_TYPE_POINTS: "Points",
    OTC_COOLING_TYPE_FIX: "Fixed",
}
