# custom_components/my_cloud_service/config_flow.py

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from .const import DOMAIN
import logging
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 60

class CsnetHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CSNet Home."""

    def __init__(self):
        """Initialize the config flow."""
        self._username = None
        self._password = None
        self._scan_interval = DEFAULT_SCAN_INTERVAL

    async def async_step_user(self, user_input=None):
        """Handle user input for login credentials."""
        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._scan_interval = user_input[CONF_SCAN_INTERVAL]

            # You might also want to handle validation and authentication here
            #cloud_service_api = CloudServiceAPI(hass, self._username, self._password)

            # Create the config entry and store the data
            return self.async_create_entry(
                title="CSNet Home",
                data={
                    CONF_USERNAME: self._username, 
                    CONF_PASSWORD: self._password,
                    CONF_SCAN_INTERVAL: self._scan_interval
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }),
        )
