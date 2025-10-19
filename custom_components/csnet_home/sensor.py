"""Support for CSNet Home sensors."""

import logging

from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import STATE_ON, STATE_OFF

from .const import DOMAIN
from .coordinator import CSNetHomeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors for CSNet Home."""
    _LOGGER.debug("Starting CSNet Home sensor setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None

    sensors = []
    for sensor_data in coordinator.get_sensors_data():
        common_data = coordinator.get_common_data()["device_status"][
            sensor_data["device_id"]
        ]

        sensors.append(
            CSNetHomeSensor(
                coordinator,
                sensor_data,
                common_data,
                "current_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
            )
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator,
                sensor_data,
                common_data,
                "setting_temperature",
                "temperature",
                UnitOfTemperature.CELSIUS,
            )
        )
        sensors.append(
            CSNetHomeSensor(coordinator, sensor_data, common_data, "mode", "enum")
        )
        sensors.append(
            CSNetHomeSensor(coordinator, sensor_data, common_data, "on_off", "enum")
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "doingBoost", "binary"
            )
        )
        # expose alarm information
        sensors.append(
            CSNetHomeSensor(coordinator, sensor_data, common_data, "alarm_code", "enum")
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "alarm_active", "binary"
            )
        )
        sensors.append(
            CSNetHomeSensor(
                coordinator, sensor_data, common_data, "alarm_message", "enum"
            )
        )

    async_add_entities(sensors)


class CSNetHomeSensor(CoordinatorEntity, Entity):
    """Representation of a sensor from the CSNet Home integration."""

    def __init__(
        self,
        coordinator: CSNetHomeCoordinator,
        sensor_data,
        common_data,
        key,
        device_class=None,
        unit=None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._sensor_data = sensor_data
        self._common_data = common_data
        self._key = key
        self._device_class = device_class
        self._unit = unit
        self._name = f"{sensor_data['device_name']} {sensor_data['room_name']} {key}"
        _LOGGER.debug("Configuring Sensor %s", self._name)

    @property
    def state(self):
        """Return the current temperature as the state of the sensor."""
        value = self._sensor_data.get(self._key)
        if self._key == "mode":
            if value == 0:
                return HVACMode.COOL
            if value == 1:
                return HVACMode.HEAT
            return HVACMode.OFF
        if self._key == "on_off":
            return STATE_ON if value == 1 else STATE_OFF
        if self._key == "alarm_active":
            # computed from alarm_code
            alarm_code = self._sensor_data.get("alarm_code")
            return STATE_ON if alarm_code not in (None, 0) else STATE_OFF
        return value

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for the sensor."""
        return self._unit

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self._sensor_data = next(
            (
                x
                for x in self._coordinator.get_sensors_data()
                if x.get("room_name") in self._name
            ),
            None,
        )
        if self._sensor_data:
            self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}",
            manufacturer="Hitachi",
            model=f"{self._common_data['name']} ATW-IOT-01",
            sw_version=self._common_data["firmware"],
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
        return self._name

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self._sensor_data['room_name']}-{self._key}"
