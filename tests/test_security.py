"""Tests for security and PII redaction."""

import pytest
from custom_components.csnet_home.api import redact_data


def test_redact_data_dictionary():
    """Test redaction of sensitive keys in a dictionary."""
    data = {
        "latitude": "50.123456",
        "longitude": "3.12",
        "name": "My Home",
        "user_dispayableName": "Myself",
        "status": "success",
        "weatherTemperature": 9,
    }
    redacted = redact_data(data)
    assert redacted["latitude"] == "**REDACTED**"
    assert redacted["longitude"] == "**REDACTED**"
    assert redacted["user_dispayableName"] == "**REDACTED**"
    assert redacted["status"] == "success"
    assert redacted["weatherTemperature"] == 9


def test_redact_data_recursive():
    """Test recursive redaction of sensitive keys."""
    data = {
        "data": {
            "installation": 1234,
            "administrator": "admin",
            "elements": [
                {
                    "deviceName": "Device 1",
                    "latitude": "50.1",
                }
            ],
        },
        "_csrf": "secret-token",
    }
    redacted = redact_data(data)
    assert redacted["data"]["installation"] == "**REDACTED**"
    assert redacted["data"]["administrator"] == "**REDACTED**"
    assert redacted["data"]["elements"][0]["latitude"] == "**REDACTED**"
    assert redacted["data"]["elements"][0]["deviceName"] == "Device 1"
    assert redacted["_csrf"] == "**REDACTED**"


def test_redact_data_list():
    """Test redaction in a list of dictionaries."""
    data = [
        {"ownerId": 123, "val": 1},
        {"ownerId": 456, "val": 2},
    ]
    redacted = redact_data(data)
    assert redacted[0]["ownerId"] == "**REDACTED**"
    assert redacted[0]["val"] == 1
    assert redacted[1]["ownerId"] == "**REDACTED**"
    assert redacted[1]["val"] == 2


def test_redact_data_no_sensitive_keys():
    """Test that non-sensitive data is left untouched."""
    data = {"temp": 20, "mode": "heat"}
    redacted = redact_data(data)
    assert redacted == data


def test_redact_data_mixed_types():
    """Test redaction with mixed data types."""
    data = {
        "password": "secret_password",
        "username": "user123",
        "nested": [1, 2, {"token": "t1"}],
    }
    redacted = redact_data(data)
    assert redacted["password"] == "**REDACTED**"
    assert redacted["username"] == "**REDACTED**"
    assert redacted["nested"][2]["token"] == "**REDACTED**"
    assert redacted["nested"][0] == 1
