from homeassistant.const import UnitOfTemperature
from homeassistant.components.climate import ClimateEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("Starting CSNet Home climate setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None
    # Add sensors based on the coordinator's data
    async_add_entities([CSNetHomeClimate(hass, entry, sensor_data) for sensor_data in coordinator.get_sensors_data()])

class CSNetHomeClimate(ClimateEntity):
    """Representation of a thermostat (climate) entity."""

    def __init__(self, hass, entry, sensor_data):
        """Initialize the thermostat entity."""
        self.hass = hass
        self.sensor_data = sensor_data
        self._attr_name = sensor_data["room_name"]
        self.entry = entry
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = ["off", "heat", "cool"] # [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]
        self._attr_preset_modes = ['away', 'comfort', 'eco']
        self._attr_preset_mode = 'comfort'
        self._attr_supported_features = (
            self.supported_features.PRESET_MODE |
            self.supported_features.TARGET_TEMPERATURE |
            self.supported_features.TURN_ON |
            self.supported_features.TURN_OFF
        )

    @property
    def temperature(self):
        """Return the current temperature."""
        return self.sensor_data["current_temperature"]

    @property
    def hvac_mode(self):
        """Return the current operation mode."""
        # Operation mode can be COOL, HEAT, AUTO, OFF
        return "heat"  # Adjust as needed based on your API data

    @property
    def target_temperature(self):
        """Return the target temperature set by the user."""
        return self.sensor_data["setting_temperature"]

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature for a room."""
        temperature = kwargs.get("temperature")
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        await cloud_api.async_set_temperature(self.sensor_data["zone_id"], self.sensor_data["parent_id"], temperature=temperature)

    async def async_update(self):
        """Update the thermostat data from the API."""
        _LOGGER.debug(f"Updating CSNet Home refresh request {self.sensor_data['room_name']}")
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        if not coordinator:
            _LOGGER.error("No coordinator instance found!")
        await coordinator.async_request_refresh()