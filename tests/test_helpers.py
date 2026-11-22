"""Tests for helper functions."""

import pytest

from custom_components.csnet_home.helpers import extract_heating_status, is_central_control_enabled


def test_extract_heating_status_none():
    """Test extract_heating_status with None input."""
    assert extract_heating_status(None) is None


def test_extract_heating_status_empty_dict():
    """Test extract_heating_status with empty dictionary."""
    assert extract_heating_status({}) is None


def test_extract_heating_status_direct_access():
    """Test extract_heating_status with direct heatingStatus."""
    data = {"heatingStatus": {"status": "ok"}}
    assert extract_heating_status(data) == {"status": "ok"}


def test_extract_heating_status_nested_access():
    """Test extract_heating_status with nested heatingStatus."""
    data = {"data": [{"indoors": [{"heatingStatus": {"status": "ok_nested"}}]}]}
    assert extract_heating_status(data) == {"status": "ok_nested"}


def test_extract_heating_status_missing_data():
    """Test extract_heating_status with missing data array."""
    data = {"other": "stuff"}
    assert extract_heating_status(data) is None


def test_extract_heating_status_empty_data_array():
    """Test extract_heating_status with empty data array."""
    data = {"data": []}
    assert extract_heating_status(data) is None


def test_extract_heating_status_missing_indoors():
    """Test extract_heating_status with missing indoors array."""
    data = {"data": [{"other": "stuff"}]}
    assert extract_heating_status(data) is None


def test_extract_heating_status_empty_indoors_array():
    """Test extract_heating_status with empty indoors array."""
    data = {"data": [{"indoors": []}]}
    assert extract_heating_status(data) is None


def test_extract_heating_status_missing_heating_status_nested():
    """Test extract_heating_status with missing heatingStatus in nested structure."""
    data = {"data": [{"indoors": [{"other": "stuff"}]}]}
    assert extract_heating_status(data) == {}


def test_extract_heating_status_not_dict_indoors():
    """Test extract_heating_status with indoors[0] not being a dict."""
    data = {"data": [{"indoors": ["not_a_dict"]}]}
    assert extract_heating_status(data) is None


def test_extract_heating_status_not_dict_data():
    """Test extract_heating_status with data[0] not being a dict."""
    data = {"data": ["not_a_dict"]}
    assert extract_heating_status(data) is None


@pytest.mark.parametrize(
    ("heating_status", "expected"),
    [
        (None, None),
        ({}, None),
        ({"centralConfig": None}, None),
        ({"centralConfig": True}, None),
        ({"centralConfig": 3, "unitModel": 2, "lcdSoft": 0x0100}, True),
        ({"centralConfig": 4}, True),
        # other than the S80: a recent LCD software is enough
        ({"centralConfig": 2, "unitModel": 0, "lcdSoft": 0x0222}, True),
        ({"centralConfig": 2, "unitModel": 0, "lcdSoft": 0x0221}, False),
        # 0: not known yet (wizard, restart, or a single poll on a running unit)
        ({"centralConfig": 0, "unitModel": 1, "lcdSoft": 0}, None),
        ({"centralConfig": 3, "unitModel": 0, "lcdSoft": 0}, True),
        # no lcdSoft: like the web app, not enough
        ({"centralConfig": 2, "unitModel": 0}, False),
        # the S80 always needs Total
        ({"centralConfig": 2, "unitModel": 2, "lcdSoft": 0x0300}, False),
        ({"centralConfig": 2, "unitModel": 2, "lcdSoft": 0}, False),
    ],
)
def test_is_central_control_enabled(heating_status, expected):
    """Same rule as isCentralWellConfigured() of the CSNet web app."""
    assert is_central_control_enabled(heating_status) is expected
