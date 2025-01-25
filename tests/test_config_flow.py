"""Test ConfigFlows configuration."""

from unittest.mock import patch

import pytest

from custom_components.csnet_home.const import DOMAIN
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

# Define test constants
TEST_CONFIG = {
    "host": "192.168.1.1",
    "port": 8080,
    "username": "test_user",
    "password": "test_password",
}


@pytest.fixture(name="hass")
async def test_config_flow_user_init(hass: HomeAssistant, mock_csnet_connection):
    """Test the initial step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.fixture(name="hass")
async def test_config_flow_user_success(hass: HomeAssistant, mock_csnet_connection):
    """Test a successful configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_CONFIG
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_CONFIG["host"]
    assert result["data"] == TEST_CONFIG


@pytest.fixture(name="hass")
async def test_config_flow_invalid_auth(hass: HomeAssistant):
    """Test the config flow with invalid authentication."""
    with patch("custom_components.csnet_home.api.CSNetHomeAPI") as mock_api:
        mock_instance = mock_api.return_value
        mock_instance.authenticate.side_effect = Exception("Invalid credentials")

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_CONFIG
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


@pytest.fixture(name="hass")
async def test_config_flow_cannot_connect(hass: HomeAssistant):
    """Test the config flow when the connection fails."""
    with patch("custom_components.csnet_home.config_flow.CSNetApi") as mock_api:
        mock_instance = mock_api.return_value
        mock_instance.authenticate.side_effect = Exception("Cannot connect")

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_CONFIG
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


@pytest.fixture(name="hass")
async def test_config_flow_duplicate_entry(hass: HomeAssistant, mock_csnet_connection):
    """Test that the config flow aborts on duplicate entries."""
    # Create an existing entry
    hass.config_entries.async_add(
        config_entries.ConfigEntry(
            version=1,
            minor_version=0,
            domain=DOMAIN,
            title=TEST_CONFIG["host"],
            data=TEST_CONFIG,
            source=config_entries.SOURCE_USER,
            entry_id="test",
            unique_id=TEST_CONFIG["host"],
            discovery_keys={"host": TEST_CONFIG["host"]},
            options={},
        )
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
