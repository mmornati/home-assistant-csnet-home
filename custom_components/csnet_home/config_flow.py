"""Config flow for CSNet Home configuration when installing the module via the interface."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (CONF_PASSWORD, CONF_SCAN_INTERVAL,
                                 CONF_USERNAME)

from .const import (CONF_FAN_COIL_MODEL, CONF_LANGUAGE, CONF_MAX_TEMP_OVERRIDE,
                    DEFAULT_FAN_COIL_MODEL, DEFAULT_LANGUAGE, DOMAIN,
                    FAN_COIL_MODEL_LEGACY, FAN_COIL_MODEL_STANDARD)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 60


class CsnetHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CSNet Home."""

    def __init__(self):
        """Initialize the config flow."""

    async def async_step_user(self, user_input=None):
        """Handle user input for login credentials."""
        errors = {}

        if user_input is not None:
            # Validate credentials before creating entry
            validation_error = await self._validate_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )

            if validation_error:
                errors = validation_error
            else:
                # Create the config entry and store the data
                return self.async_create_entry(
                    title="CSNet Home",
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                        CONF_MAX_TEMP_OVERRIDE: user_input.get(CONF_MAX_TEMP_OVERRIDE),
                        # Store the Fan coil control type
                        CONF_FAN_COIL_MODEL: user_input.get(
                            CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                    vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(
                        ["en", "fr", "es"]
                    ),
                    vol.Optional(CONF_MAX_TEMP_OVERRIDE): vol.All(
                        vol.Coerce(int), vol.Range(min=8, max=80)
                    ),
                    # Selection of Fan coil control type
                    vol.Optional(
                        CONF_FAN_COIL_MODEL, default=DEFAULT_FAN_COIL_MODEL
                    ): vol.In([FAN_COIL_MODEL_STANDARD, FAN_COIL_MODEL_LEGACY]),
                }
            ),
            description_placeholders={
                "max_temp_override_desc": "Optional: Override maximum temperature limit (8-80°C). Leave empty to use device defaults (35°C for air circuits, 80°C for water circuits/heaters)."
            },
            errors=errors,
        )

    async def _validate_credentials(
        self, username: str, password: str
    ) -> dict[str, str] | None:
        """Validate credentials with the CSNet API.

        Args:
            username: CSNet username
            password: CSNet password

        Returns:
            dict with error key if validation failed, None if successful
        """
        from .api import CSNetHomeAPI

        _LOGGER.info("Config flow: Validating credentials for user: %s", username)
        try:
            # Validate credentials using the API
            is_valid = await CSNetHomeAPI.async_validate_credentials(
                self.hass, username, password
            )

            if not is_valid:
                _LOGGER.warning("Config flow: Credential validation returned False")
                return {"base": "invalid_auth"}

            _LOGGER.info("Config flow: Credentials validated successfully")
            return None  # No errors

        except Exception as e:
            _LOGGER.error(
                "Config flow: Error during credential validation: %s", e, exc_info=True
            )
            return {"base": "cannot_connect"}

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of the integration."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors = {}

        if user_input is not None:
            # Validate credentials before saving
            validation_error = await self._validate_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )

            if validation_error:
                errors = validation_error
            else:
                # Update the config entry with new values and reload
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                        CONF_MAX_TEMP_OVERRIDE: user_input.get(CONF_MAX_TEMP_OVERRIDE),
                        CONF_FAN_COIL_MODEL: user_input.get(
                            CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL
                        ),
                    },
                )

        # Show form pre-populated with current values
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=reconfigure_entry.data.get(CONF_USERNAME)
                    ): str,
                    vol.Required(
                        CONF_PASSWORD, default=reconfigure_entry.data.get(CONF_PASSWORD)
                    ): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=reconfigure_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        CONF_LANGUAGE,
                        default=reconfigure_entry.data.get(
                            CONF_LANGUAGE, DEFAULT_LANGUAGE
                        ),
                    ): vol.In(["en", "fr"]),
                    vol.Optional(
                        CONF_MAX_TEMP_OVERRIDE,
                        default=reconfigure_entry.data.get(CONF_MAX_TEMP_OVERRIDE),
                    ): vol.All(vol.Coerce(int), vol.Range(min=8, max=80)),
                    vol.Optional(
                        CONF_FAN_COIL_MODEL,
                        default=reconfigure_entry.data.get(
                            CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL
                        ),
                    ): vol.In([FAN_COIL_MODEL_STANDARD, FAN_COIL_MODEL_LEGACY]),
                }
            ),
            description_placeholders={
                "max_temp_override_desc": "Optional: Override maximum temperature limit (8-80°C). Leave empty to use device defaults."
            },
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        """Handle reauthentication when credentials are invalid."""
        # Store the entry for later use
        self.context["entry_id"] = entry_data.get("entry_id")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Handle reauthentication confirmation."""
        errors = {}
        reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            # Validate new credentials
            validation_error = await self._validate_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )

            if validation_error:
                errors = validation_error
            else:
                # Update credentials and reload
                self.hass.config_entries.async_update_entry(
                    reauth_entry,
                    data={
                        **reauth_entry.data,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
                await self.hass.config_entries.async_reload(reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        # Show form with current username pre-filled
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(
                            reauth_entry.data.get(CONF_USERNAME) if reauth_entry else ""
                        ),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
