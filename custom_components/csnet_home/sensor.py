# custom_components/my_cloud_service/sensor.py

from homeassistant.helpers.entity import Entity
from homeassistant.const import UnitOfTemperature
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("Starting CSNet Home sensor setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None
    # Add sensors based on the coordinator's data
    async_add_entities([CSNetHomeSensor(sensor_data) for sensor_data in coordinator.get_sensors_data()])

class CSNetHomeSensor(Entity):
    """Representation of a sensor from the My Cloud Service integration."""

    def __init__(self, sensor_data):
        """Initialize the sensor."""
        self._sensor_data = sensor_data
        self._name = f"{sensor_data['device_name']} {sensor_data['room_name']}"
        self._current_temperature = sensor_data['current_temperature']
        self._planned_temperature = sensor_data['setting_temperature']
        _LOGGER.debug(f"Configuring Sensor {self._name}")

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the current temperature as the state of the sensor."""
        return self._current_temperature

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return "temperature"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for the sensor."""
        return UnitOfTemperature.CELSIUS

    @property
    def extra_state_attributes(self):
        """Return the planned temperature as an extra attribute."""
        return {
            "planned_temperature": self._planned_temperature,
        }
    
    async def async_update(self):
        """Fetch new state data for the sensor."""
        self._state = self._sensor_data['current_temperature']
