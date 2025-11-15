"""Utility helpers shared across the CSNet Home integration."""

from __future__ import annotations

from typing import Any, Mapping

FAN_COIL_BIT = 0x2000
_FAN_CONTROLLED_VALUES = {1, 2, 3}


def extract_heating_status(
    installation_devices_data: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Extract the heatingStatus dictionary from installation devices data."""
    if not isinstance(installation_devices_data, Mapping):
        return None

    heating_status = installation_devices_data.get("heatingStatus")
    if isinstance(heating_status, Mapping):
        return heating_status

    data_array = installation_devices_data.get("data")
    if isinstance(data_array, list) and data_array:
        first_device = data_array[0]
        if isinstance(first_device, Mapping):
            indoors_array = first_device.get("indoors")
            if isinstance(indoors_array, list) and indoors_array:
                first_indoors = indoors_array[0]
                if isinstance(first_indoors, Mapping):
                    nested_status = first_indoors.get("heatingStatus")
                    if isinstance(nested_status, Mapping):
                        return nested_status
                    return first_indoors.get("heatingStatus", {})
    return None


def extract_heating_setting(
    installation_devices_data: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Extract the heatingSetting dictionary from installation devices data."""
    if not isinstance(installation_devices_data, Mapping):
        return None

    heating_setting = installation_devices_data.get("heatingSetting")
    if isinstance(heating_setting, Mapping):
        return heating_setting

    data_array = installation_devices_data.get("data")
    if isinstance(data_array, list) and data_array:
        first_device = data_array[0]
        if isinstance(first_device, Mapping):
            indoors_array = first_device.get("indoors")
            if isinstance(indoors_array, list) and indoors_array:
                first_indoors = indoors_array[0]
                if isinstance(first_indoors, Mapping):
                    nested_setting = first_indoors.get("heatingSetting")
                    if isinstance(nested_setting, Mapping):
                        return nested_setting
                    return first_indoors.get("heatingSetting", {})
    return None


def extract_second_cycle(
    installation_devices_data: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Extract secondCycle data from installation devices data."""
    if not isinstance(installation_devices_data, Mapping):
        return None

    data_array = installation_devices_data.get("data")
    if isinstance(data_array, list) and data_array:
        first_device = data_array[0]
        if isinstance(first_device, Mapping):
            second_cycle = first_device.get("secondCycle")
            if isinstance(second_cycle, Mapping):
                return second_cycle

            indoors_array = first_device.get("indoors")
            if isinstance(indoors_array, list) and indoors_array:
                first_indoors = indoors_array[0]
                if isinstance(first_indoors, Mapping):
                    nested_second_cycle = first_indoors.get("secondCycle")
                    if isinstance(nested_second_cycle, Mapping):
                        return nested_second_cycle
                    if "secondCycle" in first_indoors:
                        return {}
    return None


def has_fan_coil_support(
    heating_status: Mapping[str, Any] | None,
    heating_setting: Mapping[str, Any] | None = None,
) -> bool:
    """Determine if a system exposes fan coil controls."""
    system_config_bits = 0
    if isinstance(heating_status, Mapping):
        system_config_bits = int(heating_status.get("systemConfigBits", 0))
        if system_config_bits & FAN_COIL_BIT:
            return True

        for flag_key in ("fan1ControlledOnLCD", "fan2ControlledOnLCD"):
            flag_value = heating_status.get(flag_key)
            if isinstance(flag_value, int) and flag_value in _FAN_CONTROLLED_VALUES:
                return True

    if isinstance(heating_setting, Mapping):
        for speed_key in ("fan1Speed", "fan2Speed"):
            speed_value = heating_setting.get(speed_key)
            if isinstance(speed_value, int) and speed_value >= 0:
                # Older firmwares expose speeds without the compatibility bit set
                return True

    return False


def detect_fan_coil_support(
    installation_devices_data: Mapping[str, Any] | None,
) -> bool:
    """Check installation data and determine if fan coil control should be enabled."""
    heating_status = extract_heating_status(installation_devices_data)
    heating_setting = extract_heating_setting(installation_devices_data)
    return has_fan_coil_support(heating_status, heating_setting)
