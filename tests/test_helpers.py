"""Tests for helper functions."""

from custom_components.csnet_home.helpers import extract_heating_status


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
