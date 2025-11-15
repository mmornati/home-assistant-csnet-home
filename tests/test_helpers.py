"""Tests for helper utilities."""

from __future__ import annotations

from custom_components.csnet_home.helpers import (
    detect_fan_coil_support,
    extract_heating_setting,
    extract_heating_status,
    extract_second_cycle,
    has_fan_coil_support,
)


def legacy_extract_heating_status(installation_devices_data):
    """Previous implementation preserved for regression comparison."""
    if not installation_devices_data:
        return None

    heating_status = installation_devices_data.get("heatingStatus")
    if heating_status:
        return heating_status

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


def legacy_extract_heating_setting(installation_devices_data):
    """Previous implementation preserved for regression comparison."""
    if not installation_devices_data:
        return None

    heating_setting = installation_devices_data.get("heatingSetting")
    if heating_setting:
        return heating_setting

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


def test_extract_heating_status_matches_legacy_direct():
    data = {"heatingStatus": {"systemConfigBits": 0x2000}}
    assert extract_heating_status(data) == legacy_extract_heating_status(data)


def test_extract_heating_status_matches_legacy_nested():
    data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "systemConfigBits": 0x1000,
                            "fan1ControlledOnLCD": 3,
                        }
                    }
                ]
            }
        ]
    }
    assert extract_heating_status(data) == legacy_extract_heating_status(data)


def test_extract_heating_status_matches_legacy_missing_key():
    data = {
        "data": [
            {
                "indoors": [
                    {
                        # heatingStatus intentionally missing to exercise default fallback
                    }
                ]
            }
        ]
    }
    assert extract_heating_status(data) == legacy_extract_heating_status(data) == {}


def test_extract_heating_status_matches_legacy_none():
    assert extract_heating_status(None) == legacy_extract_heating_status(None) is None


def test_extract_second_cycle_top_level():
    data = {
        "data": [
            {
                "secondCycle": {"dischargeTemp": 10, "suctionTemp": 5},
                "indoors": [{"heatingStatus": {}}],
            }
        ]
    }
    assert extract_second_cycle(data) == {"dischargeTemp": 10, "suctionTemp": 5}


def test_extract_second_cycle_nested():
    data = {
        "data": [
            {
                "indoors": [
                    {
                        "secondCycle": {"dischargeTemp": 8},
                    }
                ]
            }
        ]
    }
    assert extract_second_cycle(data) == {"dischargeTemp": 8}


def test_extract_second_cycle_none():
    assert extract_second_cycle(None) is None


def test_extract_heating_setting_matches_legacy():
    data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingSetting": {
                            "fan1Speed": 2,
                        }
                    }
                ]
            }
        ]
    }
    assert extract_heating_setting(data) == legacy_extract_heating_setting(data)


def test_has_fan_coil_support_from_bit():
    status = {"systemConfigBits": 0x2000}
    assert has_fan_coil_support(status) is True


def test_has_fan_coil_support_from_flags():
    status = {"fan1ControlledOnLCD": 3}
    assert has_fan_coil_support(status) is True


def test_has_fan_coil_support_from_setting():
    setting = {"fan1Speed": 1}
    assert has_fan_coil_support({}, setting) is True


def test_detect_fan_coil_support_combined():
    data = {
        "data": [
            {
                "indoors": [
                    {
                        "heatingStatus": {
                            "systemConfigBits": 0x0000,
                            "fan1ControlledOnLCD": 1,
                        },
                        "heatingSetting": {"fan1Speed": 2},
                    }
                ]
            }
        ]
    }
    assert detect_fan_coil_support(data) is True
