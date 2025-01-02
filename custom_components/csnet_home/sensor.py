# custom_components/my_cloud_service/sensor.py

from homeassistant.helpers.entity import Entity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
import logging
from .const import DOMAIN
from .coordinator import CSNetHomeCoordinator
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("Starting CSNet Home sensor setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None
    # Add sensors based on the coordinator's data
    async_add_entities([CSNetHomeSensor(coordinator, sensor_data=sensor_data, common_data=coordinator.get_common_data()["device_status"][sensor_data['device_id']]) for sensor_data in coordinator.get_sensors_data()])

class CSNetHomeSensor(CoordinatorEntity, Entity):
    """Representation of a sensor from the CSNet Home integration."""

    def __init__(self, coordinator: CSNetHomeCoordinator, sensor_data, common_data):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_data = sensor_data
        self._common_data = common_data
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
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}",
            manufacturer="Hitachi",
            model=f"{self._common_data['name']} ATW-IOT-01",
            sw_version=self._common_data['firmware'],
            identifiers={
                (
                    DOMAIN,
                    f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}",
                )
            },
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}"
    
    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self._sensor_data["room_name"]}"

    async def async_update(self):
        """Fetch new state data for the sensor."""
        self._state = self._sensor_data['current_temperature']
