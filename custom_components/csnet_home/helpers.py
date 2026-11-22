"""Helper functions for CSNet Home integration."""

import logging

_LOGGER = logging.getLogger(__name__)


def find_indoor_unit(installation_devices_data, indoor_id=None):
    """Return the indoor unit a zone belongs to, from installation devices data.

    Searches data[].indoors[] of every device for the indoor whose ``id`` is
    ``indoor_id`` (the ``parent_id`` of a zone). Falls back to the first indoor
    unit (data[0].indoors[0]) when ``indoor_id`` is None or matches no unit.

    Args:
        installation_devices_data: The installation devices API response
        indoor_id: The indoor unit id, or None for the first indoor unit

    Returns:
        dict or None: the indoor unit dictionary, or None if there is none
    """
    if not isinstance(installation_devices_data, dict):
        return None

    data_array = installation_devices_data.get("data", [])
    if not isinstance(data_array, list):
        return None

    if indoor_id is not None:
        for device in data_array:
            indoors_array = device.get("indoors", []) if isinstance(device, dict) else []
            if not isinstance(indoors_array, list):
                continue
            for indoor in indoors_array:
                if isinstance(indoor, dict) and indoor.get("id") is not None and str(indoor.get("id")) == str(indoor_id):
                    return indoor

        _LOGGER.debug("Indoor unit %s not found in installation devices data, using the first unit", indoor_id)

    if len(data_array) > 0 and isinstance(data_array[0], dict):
        indoors_array = data_array[0].get("indoors", [])
        if isinstance(indoors_array, list) and len(indoors_array) > 0 and isinstance(indoors_array[0], dict):
            return indoors_array[0]

    return None


def extract_indoor_data(installation_devices_data, key, indoor_id=None):
    """Extract one section (heatingStatus, heatingSetting...) of an indoor unit.

    Navigates through: data[].indoors[id == indoor_id].{key}, falling back to
    data[0].indoors[0].{key} (see ``find_indoor_unit``).

    Args:
        installation_devices_data: The installation devices API response
        key: The key to extract (e.g., "heatingStatus", "heatingSetting")
        indoor_id: The indoor unit id, or None for the first indoor unit

    Returns:
        dict or None: The extracted dictionary, or None if not found
    """
    if not installation_devices_data:
        return None

    # Try direct access first (if already extracted)
    value = installation_devices_data.get(key)
    if value:
        return value

    indoor = find_indoor_unit(installation_devices_data, indoor_id)
    if indoor is not None:
        return indoor.get(key, {})

    return None


def extract_heating_status(installation_devices_data, indoor_id=None):
    """Extract heatingStatus from installation devices data structure.

    Args:
        installation_devices_data: The installation devices API response
        indoor_id: The indoor unit id, or None for the first indoor unit

    Returns:
        dict or None: heatingStatus dictionary, or None if not found
    """
    return extract_indoor_data(installation_devices_data, "heatingStatus", indoor_id)


def zone_key(sensor_data):
    """Return a stable identifier for a CSNet zone.

    CSNet lets users rename rooms, so the room name cannot identify a zone.
    The (device, room id, element type) triple stays the same across renames
    and matches the coordinator's ``get_sensor_data_by_id`` lookup.
    """
    return f"{sensor_data.get('device_id')}-{sensor_data.get('room_id')}-{sensor_data.get('zone_id')}"


def zone_device_identifier(sensor_data):
    """Return the device registry identifier for a zone's device."""
    return f"zone-{zone_key(sensor_data)}"


def legacy_zone_device_identifier(sensor_data):
    """Return the name-based device identifier used before 2.11."""
    return f"{sensor_data.get('device_name', 'Unknown')}-{sensor_data.get('room_name', 'Unknown')}"


# heatingStatus.unitModel of the Yutaki S80, which needs centralConfig "Total" whatever its LCD software
YUTAKI_S80_UNIT_MODEL = 2
# heatingStatus.centralConfig from this value on is "Total": CSNet commands are applied
CENTRAL_CONFIG_TOTAL = 3
# LCD software from which units other than the S80 apply CSNet commands without "Total"
LCD_SOFT_CENTRAL_OK = 0x0222


def _as_int(value):
    """Return value when it is an int (not a bool), otherwise None."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def is_central_control_enabled(heating_status):
    """Tell whether the unit applies the commands CSNet Home sends it.

    Same rule as isCentralWellConfigured() of the CSNet web app, which hides
    the controls and shows "the central command setting is not set to Total"
    when it is false.

    Returns True or False, or None when heating_status does not say
    (no data yet, or no centralConfig in it).
    """
    if not isinstance(heating_status, dict):
        return None
    central_config = _as_int(heating_status.get("centralConfig"))
    if central_config is None:
        return None
    if central_config >= CENTRAL_CONFIG_TOTAL:
        return True
    if _as_int(heating_status.get("unitModel")) != YUTAKI_S80_UNIT_MODEL:
        lcd_soft = _as_int(heating_status.get("lcdSoft"))
        # 0: not known yet, while the unit's wizard runs or the unit restarts
        if lcd_soft is not None and (lcd_soft == 0 or lcd_soft >= LCD_SOFT_CENTRAL_OK):
            return True
    return False
