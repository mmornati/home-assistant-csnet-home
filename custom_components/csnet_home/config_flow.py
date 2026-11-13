"""Config flow for CSNet Home configuration when installing the module via the interface."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import (
    CONF_ENABLE_ALARM_NOTIFICATIONS,
    CONF_FAN_COIL_MODEL,
    CONF_FILTERED_ALARM_CODES,
    CONF_LANGUAGE,
    CONF_MAX_TEMP_OVERRIDE,
    CONF_POWER_SUPPLY,
    DEFAULT_ENABLE_ALARM_NOTIFICATIONS,
    DEFAULT_FAN_COIL_MODEL,
    DEFAULT_FILTERED_ALARM_CODES,
    DEFAULT_LANGUAGE,
    DEFAULT_POWER_SUPPLY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FAN_COIL_MODEL_LEGACY,
    FAN_COIL_MODEL_STANDARD,
    MIN_SCAN_INTERVAL,
    POWER_SUPPLY_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SCHEMA = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL))
# Masked in the browser, and never pre-filled: the stored password is not sent to the frontend
PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password"))


def _settings_schema(current: dict) -> dict:
    """Return the form fields other than the credentials, pre-filled from the current settings."""
    max_temp_key = vol.Optional(CONF_MAX_TEMP_OVERRIDE)
    if current.get(CONF_MAX_TEMP_OVERRIDE) is not None:
        # a suggestion, not a default: emptying the field removes the override
        max_temp_key = vol.Optional(CONF_MAX_TEMP_OVERRIDE, description={"suggested_value": current[CONF_MAX_TEMP_OVERRIDE]})
    return {
        vol.Optional(
            CONF_SCAN_INTERVAL,
            default=max(current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL), MIN_SCAN_INTERVAL),
        ): SCAN_INTERVAL_SCHEMA,
        vol.Optional(CONF_LANGUAGE, default=current.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)): vol.In(["en", "fr", "es"]),
        max_temp_key: vol.All(vol.Coerce(int), vol.Range(min=8, max=80)),
        vol.Optional(CONF_FAN_COIL_MODEL, default=current.get(CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL)): vol.In(
            [FAN_COIL_MODEL_STANDARD, FAN_COIL_MODEL_LEGACY]
        ),
        vol.Optional(
            CONF_ENABLE_ALARM_NOTIFICATIONS,
            default=current.get(CONF_ENABLE_ALARM_NOTIFICATIONS, DEFAULT_ENABLE_ALARM_NOTIFICATIONS),
        ): bool,
        # a suggestion, not a default: emptying the field means "notify every code"
        vol.Optional(
            CONF_FILTERED_ALARM_CODES,
            description={"suggested_value": current.get(CONF_FILTERED_ALARM_CODES, DEFAULT_FILTERED_ALARM_CODES)},
        ): str,
        vol.Optional(CONF_POWER_SUPPLY, default=current.get(CONF_POWER_SUPPLY, DEFAULT_POWER_SUPPLY)): vol.In(POWER_SUPPLY_OPTIONS),
    }


def _settings_from_input(user_input: dict) -> dict:
    """Return the settings to store from a submitted form."""
    return {
        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
        CONF_MAX_TEMP_OVERRIDE: user_input.get(CONF_MAX_TEMP_OVERRIDE),
        CONF_FAN_COIL_MODEL: user_input.get(CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL),
        CONF_ENABLE_ALARM_NOTIFICATIONS: user_input.get(CONF_ENABLE_ALARM_NOTIFICATIONS, DEFAULT_ENABLE_ALARM_NOTIFICATIONS),
        # the frontend leaves an emptied field out of what it sends
        CONF_FILTERED_ALARM_CODES: user_input.get(CONF_FILTERED_ALARM_CODES, ""),
        CONF_POWER_SUPPLY: user_input.get(CONF_POWER_SUPPLY, DEFAULT_POWER_SUPPLY),
    }


def _settings_errors(user_input: dict) -> dict[str, str]:
    """Return the errors in the submitted settings, by field."""
    codes = user_input.get(CONF_FILTERED_ALARM_CODES) or ""
    try:
        for code in codes.split(","):
            if code.strip():
                int(code.strip())
    except ValueError:
        return {CONF_FILTERED_ALARM_CODES: "invalid_alarm_codes"}
    return {}


class CsnetHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CSNet Home."""

    async def async_step_user(self, user_input=None):
        """Handle user input for login credentials."""
        errors = {}

        if user_input is not None:
            errors = _settings_errors(user_input)
            if not errors:
                # Validate credentials before creating entry
                errors = await self._validate_credentials(user_input[CONF_USERNAME], user_input[CONF_PASSWORD]) or {}

            if not errors:
                return self.async_create_entry(
                    title="CSNet Home",
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        **_settings_from_input(user_input),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                **_settings_schema({}),
            }
        )
        return self.async_show_form(
            step_id="user",
            # keep what was typed when the form comes back with an error, except the password
            data_schema=self.add_suggested_values_to_schema(schema, {k: v for k, v in (user_input or {}).items() if k != CONF_PASSWORD}),
            errors=errors,
        )

    async def _validate_credentials(self, username: str, password: str) -> dict[str, str] | None:
        """Validate credentials with the CSNet API.

        Args:
            username: CSNet username
            password: CSNet password

        Returns:
            dict with error key if validation failed, None if successful
        """
        from .api import CSNetHomeAPI

        _LOGGER.debug("Config flow: Validating credentials")
        try:
            # Validate credentials using the API
            is_valid = await CSNetHomeAPI.async_validate_credentials(self.hass, username, password)

            if not is_valid:
                _LOGGER.warning("Config flow: Credential validation returned False")
                return {"base": "invalid_auth"}

            _LOGGER.info("Config flow: Credentials validated successfully")
            return None  # No errors

        except Exception as e:
            _LOGGER.error("Config flow: Error during credential validation: %s", e, exc_info=True)
            return {"base": "cannot_connect"}

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of the integration."""
        reconfigure_entry = self._get_reconfigure_entry()
        current = reconfigure_entry.data
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            # an empty password field keeps the stored password
            password = user_input.get(CONF_PASSWORD) or current.get(CONF_PASSWORD)

            errors = _settings_errors(user_input)
            credentials_changed = username != current.get(CONF_USERNAME) or password != current.get(CONF_PASSWORD)
            if not errors and credentials_changed:
                # Unchanged credentials are in use already: no extra login for a settings change
                errors = await self._validate_credentials(username, password) or {}

            if not errors:
                # Update the config entry with new values and reload
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        **_settings_from_input(user_input),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=current.get(CONF_USERNAME)): str,
                vol.Optional(CONF_PASSWORD): PASSWORD_SELECTOR,
                **_settings_schema(current),
            }
        )
        if user_input is not None:
            # back with an error: keep what was typed, except the password
            schema = self.add_suggested_values_to_schema(schema, {k: v for k, v in user_input.items() if k != CONF_PASSWORD})
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data):
        """Handle reauthentication when credentials are invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Handle reauthentication confirmation."""
        errors = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            # Validate new credentials
            errors = await self._validate_credentials(user_input[CONF_USERNAME], user_input[CONF_PASSWORD]) or {}

            if not errors:
                # Update credentials and reload (no update listener: the flow
                # owns the reload, as Home Assistant requires from 2026.12)
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                    reason="reauth_successful",
                )

        # Show form with current username pre-filled
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=reauth_entry.data.get(CONF_USERNAME, "")): str,
                    vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                }
            ),
            errors=errors,
        )
