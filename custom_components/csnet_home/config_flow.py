"""Config flow for CSNet Home configuration when installing the module via the interface."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME

from .const import (
    DOMAIN,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    CONF_MAX_TEMP_OVERRIDE,
    CONF_FAN_COIL_MODEL,
    FAN_COIL_MODEL_STANDARD,
    FAN_COIL_MODEL_LEGACY,
    DEFAULT_FAN_COIL_MODEL,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 60


class CsnetHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CSNet Home."""

    def __init__(self):
        """Initialize the config flow."""
        pass

    async def async_step_user(self, user_input=None):
        """Handle user input for login credentials."""
        if user_input is not None:
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
                        ["en", "fr"]
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
        )
