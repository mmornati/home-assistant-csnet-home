"""List of static data used within the code."""

DOMAIN = "csnet_home"
API_URL = "https://www.csnetmanager.com"
LOGIN_PATH = "/login"
ELEMENTS_PATH = "/data/elements"
INSTALLATION_DEVICES_PATH = "/data/installationdevices"
INSTALLATION_ALARMS_PATH = "/data/installationalarms"
HEAT_SETTINGS_PATH = "/data/indoor/heat_setting"
CONF_ENABLE_DEVICE_LOGGING = "enable_device_logging"
CONF_MAX_TEMP_OVERRIDE = "max_temp_override"
CONF_FAN_COIL_MODEL = "fan_coil_model"
FAN_COIL_MODEL_STANDARD = "standard"  
FAN_COIL_MODEL_LEGACY = "legacy"  
DEFAULT_FAN_COIL_MODEL = FAN_COIL_MODEL_STANDARD

COMMON_API_HEADERS = {
    "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "origin": "null",
    "pragma": "no-cache",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
DEFAULT_API_TIMEOUT = 10

WATER_HEATER_MAX_TEMPERATURE = 80
WATER_HEATER_MIN_TEMPERATURE = 30

# Air circuit (RTU) temperature limits - for zones 1, 2 (C1_AIR, C2_AIR)
HEATING_MAX_TEMPERATURE = 35  # RTU_MAX from JavaScript
HEATING_MIN_TEMPERATURE = 8

# Water circuit temperature limits - for zones 5, 6 (C1_WATER, C2_WATER)
WATER_CIRCUIT_MAX_HEAT = 80  # C1_MAX_HEAT / C2_MAX_HEAT from JavaScript
WATER_CIRCUIT_MIN_HEAT = 20

# Fan Speed Control (for fan coil systems)
FAN_SPEED_OFF = "0"
FAN_SPEED_LOW = "1"
FAN_SPEED_MEDIUM = "2"
FAN_SPEED_AUTO = "3"

# Standard
FAN_SPEED_MAP_STANDARD = {
    "off": 0,
    "low": 1,
    "medium": 2,
    "auto": 3,
}

FAN_SPEED_REVERSE_MAP_STANDARD = {
    0: "off",
    1: "low",
    2: "medium",
    3: "auto",
}

# Legacy
FAN_SPEED_MAP_LEGACY = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "auto": 3,
}

FAN_SPEED_REVERSE_MAP_LEGACY = {
    0: "low",
    1: "medium",
    2: "high",
    3: "auto",
}

FAN_SPEED_MAP = FAN_SPEED_MAP_STANDARD
FAN_SPEED_REVERSE_MAP = FAN_SPEED_REVERSE_MAP_STANDARD

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
