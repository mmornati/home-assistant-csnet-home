"""Test ConfigFlows configuration."""

from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import (
    CONF_ENABLE_ALARM_NOTIFICATIONS,
    CONF_FAN_COIL_MODEL,
    CONF_FILTERED_ALARM_CODES,
    CONF_LANGUAGE,
    CONF_MAX_TEMP_OVERRIDE,
    DEFAULT_ENABLE_ALARM_NOTIFICATIONS,
    DEFAULT_FILTERED_ALARM_CODES,
    DOMAIN,
)

# Define test constants
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"
TEST_SCAN_INTERVAL = 60
TEST_LANGUAGE = "en"
TEST_MAX_TEMP = 35
TEST_FAN_COIL_MODEL = "standard"
TEST_ENABLE_ALARM_NOTIFICATIONS = True
TEST_FILTERED_ALARM_CODES = "-1"

TEST_CONFIG = {
    CONF_USERNAME: TEST_USERNAME,
    CONF_PASSWORD: TEST_PASSWORD,
    CONF_SCAN_INTERVAL: TEST_SCAN_INTERVAL,
    CONF_LANGUAGE: TEST_LANGUAGE,
    CONF_MAX_TEMP_OVERRIDE: TEST_MAX_TEMP,
    CONF_FAN_COIL_MODEL: TEST_FAN_COIL_MODEL,
    CONF_ENABLE_ALARM_NOTIFICATIONS: TEST_ENABLE_ALARM_NOTIFICATIONS,
    CONF_FILTERED_ALARM_CODES: TEST_FILTERED_ALARM_CODES,
}


async def test_config_flow_user_init(hass: HomeAssistant):
    """Test the initial step of the config flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_config_flow_user_success(hass: HomeAssistant):
    """Test a successful configuration flow."""
    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=TEST_CONFIG)

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "CSNet Home"
        assert result["data"][CONF_USERNAME] == TEST_USERNAME
        assert result["data"][CONF_PASSWORD] == TEST_PASSWORD


async def test_reconfigure_flow_success(hass: HomeAssistant):
    """Test successful reconfiguration flow."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    # Mock credential validation
    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=True,
    ):
        # Start reconfigure flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        # Update configuration with new values
        new_config = TEST_CONFIG.copy()
        new_config[CONF_SCAN_INTERVAL] = 120  # Changed from 60 to 120
        new_config[CONF_PASSWORD] = "new_password"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=new_config)

        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"

        # Verify the entry was updated
        updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
        assert updated_entry.data[CONF_SCAN_INTERVAL] == 120
        assert updated_entry.data[CONF_PASSWORD] == "new_password"


async def test_reconfigure_flow_invalid_credentials(hass: HomeAssistant):
    """Test reconfiguration flow with invalid credentials."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    # Mock credential validation to fail
    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=False,
    ):
        # Start reconfigure flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

        # Submit with invalid credentials
        invalid_config = TEST_CONFIG.copy()
        invalid_config[CONF_PASSWORD] = "wrong_password"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=invalid_config)

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}

        # Verify the entry was NOT updated
        unchanged_entry = hass.config_entries.async_get_entry(entry.entry_id)
        assert unchanged_entry.data[CONF_PASSWORD] == TEST_PASSWORD


async def test_reconfigure_preserves_entry_id(hass: HomeAssistant):
    """Test that reconfigure doesn't create a new entry."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    original_entry_count = len(hass.config_entries.async_entries(DOMAIN))

    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=TEST_CONFIG)

        # Verify no new entry was created
        assert len(hass.config_entries.async_entries(DOMAIN)) == original_entry_count
        assert result["type"] == data_entry_flow.FlowResultType.ABORT


async def test_reauth_flow_success(hass: HomeAssistant):
    """Test successful reauthentication flow."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=True,
    ):
        # Start reauth flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data={"entry_id": entry.entry_id},
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        # Provide new credentials
        new_credentials = {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: "new_password",
        }

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=new_credentials)

        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"

        # Verify credentials were updated
        updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
        assert updated_entry.data[CONF_PASSWORD] == "new_password"


async def test_reauth_flow_invalid_password(hass: HomeAssistant):
    """Test reauthentication flow with invalid password."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=False,
    ):
        # Start reauth flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data={"entry_id": entry.entry_id},
        )

        # Provide invalid credentials
        invalid_credentials = {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: "wrong_password",
        }

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=invalid_credentials)

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}

        # Verify credentials were NOT updated
        unchanged_entry = hass.config_entries.async_get_entry(entry.entry_id)
        assert unchanged_entry.data[CONF_PASSWORD] == TEST_PASSWORD


async def test_validate_credentials_connection_error(hass: HomeAssistant):
    """Test credential validation with connection error."""
    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        side_effect=Exception("Connection failed"),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=TEST_CONFIG)

        # Should show form with connection error
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_config_flow_saves_alarm_notification_options(hass: HomeAssistant):
    """Test that config flow saves alarm notification options."""
    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Config with custom alarm options
        custom_config = TEST_CONFIG.copy()
        custom_config[CONF_ENABLE_ALARM_NOTIFICATIONS] = False
        custom_config[CONF_FILTERED_ALARM_CODES] = "-1,-2,-3"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=custom_config)

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_ALARM_NOTIFICATIONS] is False
        assert result["data"][CONF_FILTERED_ALARM_CODES] == "-1,-2,-3"


async def test_config_flow_default_alarm_notification_options(hass: HomeAssistant):
    """Test that config flow uses default alarm notification options."""
    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Config without custom alarm options
        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=TEST_CONFIG)

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ENABLE_ALARM_NOTIFICATIONS] is DEFAULT_ENABLE_ALARM_NOTIFICATIONS
        assert result["data"][CONF_FILTERED_ALARM_CODES] == DEFAULT_FILTERED_ALARM_CODES


async def test_reconfigure_flow_updates_alarm_notification_options(hass: HomeAssistant):
    """Test that reconfigure flow updates alarm notification options."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.csnet_home.api.CSNetHomeAPI.async_validate_credentials",
        return_value=True,
    ):
        # Start reconfigure flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        # Update alarm notification options
        new_config = TEST_CONFIG.copy()
        new_config[CONF_ENABLE_ALARM_NOTIFICATIONS] = False
        new_config[CONF_FILTERED_ALARM_CODES] = "-5,-10"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=new_config)

        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"

        # Verify the entry was updated
        updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
        assert updated_entry.data[CONF_ENABLE_ALARM_NOTIFICATIONS] is False
        assert updated_entry.data[CONF_FILTERED_ALARM_CODES] == "-5,-10"
