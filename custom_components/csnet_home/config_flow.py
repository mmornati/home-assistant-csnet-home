"""Config flow for CSNet Home configuration when installing the module via the interface."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME

from .const import DOMAIN, CONF_LANGUAGE, DEFAULT_LANGUAGE, CONF_MAX_TEMP_OVERRIDE

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 60


class CsnetHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CSNet Home."""

    def __init__(self):
        """Initialize the config flow."""
        self._username = None
        self._password = None
        self._scan_interval = DEFAULT_SCAN_INTERVAL
        self._max_temp_override = None

    async def async_step_user(self, user_input=None):
        """Handle user input for login credentials."""
        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._scan_interval = user_input[CONF_SCAN_INTERVAL]

            # You might also want to handle validation and authentication here
            # cloud_service_api = CloudServiceAPI(hass, self._username, self._password)

            # Create the config entry and store the data
            return self.async_create_entry(
                title="CSNet Home",
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_SCAN_INTERVAL: self._scan_interval,
                    CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    CONF_MAX_TEMP_OVERRIDE: user_input.get(CONF_MAX_TEMP_OVERRIDE),
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
                }
            ),
            description_placeholders={
                "max_temp_override_desc": "Optional: Override maximum temperature limit (8-80°C). Leave empty to use device defaults (35°C for air circuits, 80°C for water circuits/heaters)."
            },
        )
