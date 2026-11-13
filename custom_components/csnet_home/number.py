"""Create a Number Component for Home Assistant to control fixed water temperature."""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    OTC_COOLING_TYPE_FIX,
    OTC_HEATING_TYPE_FIX,
    WATER_CIRCUIT_MAX_COOL,
    WATER_CIRCUIT_MAX_HEAT,
    WATER_CIRCUIT_MIN_COOL,
    WATER_CIRCUIT_MIN_HEAT,
)
from .coordinator import CSNetHomeCoordinator
from .helpers import extract_indoor_data, zone_device_identifier

_LOGGER = logging.getLogger(__name__)

# Orders to the unit go out one at a time; reads come from the coordinator
PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number platform for CSNet Home fixed water temperature."""
    _LOGGER.debug("Starting CSNet Home number setup")

    coordinator = entry.runtime_data.coordinator

    entities = []
    installation_devices_data = coordinator.get_installation_devices_data()

    if not installation_devices_data:
        _LOGGER.debug("No installation devices data available for number entities")
        return None

    heating_status = extract_indoor_data(installation_devices_data, "heatingStatus")
    heating_setting = extract_indoor_data(installation_devices_data, "heatingSetting")

    if not heating_status or not heating_setting:
        _LOGGER.debug("No heating status or setting available for number entities")
        return None

    # Get sensor data to find parent_id for water circuits
    sensors_data = coordinator.get_sensors_data()
    common_data = coordinator.get_common_data()

    # Create number entities for C1 and C2 fixed water temperature
    # Fixed temperature is a CIRCUIT-level setting that affects both air and water zones
    # Check each circuit for both heating and cooling modes
    for circuit in [1, 2]:
        # Map circuit to zone IDs: Air zones (1,2) and Water zones (5,6)
        air_zone_id = circuit  # Zone 1 = C1_AIR, Zone 2 = C2_AIR
        water_zone_id = circuit + 4  # Zone 5 = C1_WATER, Zone 6 = C2_WATER

        # The entity is attached to one zone of the circuit: decide from, and
        # later read, the indoor unit that zone belongs to. One entity per
        # circuit and mode exists per device (see unique_id), so with several
        # indoor units only the first matching zone gets one.
        circuit_sensor = next((x for x in sensors_data if x.get("zone_id") == air_zone_id), None) or next(
            (x for x in sensors_data if x.get("zone_id") == water_zone_id), None
        )
        indoor_id = circuit_sensor.get("parent_id") if circuit_sensor else None
        circuit_status = extract_indoor_data(installation_devices_data, "heatingStatus", indoor_id) or heating_status
        circuit_setting = extract_indoor_data(installation_devices_data, "heatingSetting", indoor_id) or heating_setting

        # Check heating mode
        otc_heat_key = f"otcTypeHeatC{circuit}"
        otc_heat_type = circuit_status.get(otc_heat_key, 0)
        if otc_heat_type == OTC_HEATING_TYPE_FIX:
            # Try to find sensor data for air zone first (preferred for UI)
            # If not available, fall back to water zone
            sensor_data = next(
                (x for x in sensors_data if x.get("zone_id") == air_zone_id),
                None,
            )

            # Fallback to water zone if air zone not found
            if not sensor_data:
                sensor_data = next(
                    (x for x in sensors_data if x.get("zone_id") == water_zone_id),
                    None,
                )

            if sensor_data:
                fix_temp_heat = circuit_setting.get(f"fixTempHeatC{circuit}")
                _LOGGER.debug(
                    "Creating fixed water temperature number entity for C%d heating (OTC type: %d, current temp: %s, zone: %d)",
                    circuit,
                    otc_heat_type,
                    fix_temp_heat,
                    sensor_data.get("zone_id"),
                )
                entities.append(
                    CSNetHomeFixedWaterTemperatureNumber(
                        coordinator,
                        sensor_data,
                        common_data.get("device_status", {}).get(sensor_data.get("device_id"), {}),
                        circuit,
                        1,  # Heating mode
                        entry,
                    )
                )

        # Check cooling mode
        otc_cool_key = f"otcTypeCoolC{circuit}"
        otc_cool_type = circuit_status.get(otc_cool_key, 0)
        if otc_cool_type == OTC_COOLING_TYPE_FIX:
            # Try to find sensor data for air zone first (preferred for UI)
            # If not available, fall back to water zone
            sensor_data = next(
                (x for x in sensors_data if x.get("zone_id") == air_zone_id),
                None,
            )

            # Fallback to water zone if air zone not found
            if not sensor_data:
                sensor_data = next(
                    (x for x in sensors_data if x.get("zone_id") == water_zone_id),
                    None,
                )

            if sensor_data:
                fix_temp_cool = circuit_setting.get(f"fixTempCoolC{circuit}")
                _LOGGER.debug(
                    "Creating fixed water temperature number entity for C%d cooling (OTC type: %d, current temp: %s, zone: %d)",
                    circuit,
                    otc_cool_type,
                    fix_temp_cool,
                    sensor_data.get("zone_id"),
                )
                entities.append(
                    CSNetHomeFixedWaterTemperatureNumber(
                        coordinator,
                        sensor_data,
                        common_data.get("device_status", {}).get(sensor_data.get("device_id"), {}),
                        circuit,
                        0,  # Cooling mode
                        entry,
                    )
                )

    if entities:
        _LOGGER.info("Created %d fixed water temperature number entities", len(entities))
        async_add_entities(entities)
    else:
        _LOGGER.debug("No fixed water temperature entities created (OTC type not FIX)")

    return None


class CSNetHomeFixedWaterTemperatureNumber(CoordinatorEntity, NumberEntity):
    """Representation of a fixed water temperature number entity."""

    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.AUTO

    def __init__(
        self,
        coordinator: CSNetHomeCoordinator,
        sensor_data,
        common_data,
        circuit: int,
        mode: int,
        entry,
    ):
        """Initialize the fixed water temperature number entity."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._sensor_data = sensor_data
        self._common_data = common_data
        self._circuit = circuit
        self._mode = mode  # 0 = cool, 1 = heat
        self.entry = entry

        # Set temperature limits based on mode
        if mode == 1:  # Heating
            self._attr_native_min_value = WATER_CIRCUIT_MIN_HEAT
            self._attr_native_max_value = WATER_CIRCUIT_MAX_HEAT
        else:  # Cooling
            self._attr_native_min_value = WATER_CIRCUIT_MIN_COOL
            self._attr_native_max_value = WATER_CIRCUIT_MAX_COOL

        # Determine name based on mode
        mode_name = "Heating" if mode == 1 else "Cooling"
        circuit_name = f"C{circuit}"
        zone_name = sensor_data.get("room_name", f"Circuit {circuit}")

        self._attr_name = f"{zone_name} Fixed Water Temperature {mode_name} {circuit_name}"
        self._attr_unique_id = f"{DOMAIN}-fixed-water-temp-{circuit_name.lower()}-" f"{mode_name.lower()}-{sensor_data.get('device_id')}"

        _LOGGER.debug(
            "Initialized fixed water temperature number entity: %s (circuit %d, mode %d)",
            self._attr_name,
            circuit,
            mode,
        )

    def _heating_setting(self):
        """Return the heatingSetting of the indoor unit this circuit belongs to, or None."""
        installation_devices_data = self._coordinator.get_installation_devices_data()
        if not installation_devices_data:
            return None
        return extract_indoor_data(installation_devices_data, "heatingSetting", self._sensor_data.get("parent_id"))

    @property
    def _temp_key(self) -> str:
        """Return the heatingSetting key of this entity's fixed temperature."""
        if self._mode == 1:  # Heating mode
            return f"fixTempHeatC{self._circuit}"
        return f"fixTempCoolC{self._circuit}"  # Cooling mode

    @property
    def native_value(self) -> float | None:
        """Return the current fixed water temperature value."""
        heating_setting = self._heating_setting()

        if not heating_setting:
            return None

        value = heating_setting.get(self._temp_key)
        if value is not None:
            return float(value)

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Entity is only available when OTC type is FIX
        installation_devices_data = self._coordinator.get_installation_devices_data()
        if not installation_devices_data:
            return False

        cloud_api = self.entry.runtime_data.api
        is_editable = cloud_api.is_fixed_water_temperature_editable(self._circuit, self._mode, installation_devices_data, self._sensor_data.get("parent_id"))

        return is_editable

    async def async_set_native_value(self, value: float) -> None:
        """Set the fixed water temperature value."""
        parent_id = self._sensor_data.get("parent_id")
        if not parent_id:
            _LOGGER.error("No parent_id found for fixed water temperature")
            return

        cloud_api = self.entry.runtime_data.api
        success = await cloud_api.async_set_fixed_water_temperature(self._circuit, parent_id, self._mode, value)

        if success:
            _LOGGER.debug(
                "Fixed water temperature set to %s for circuit %d (mode %d)",
                value,
                self._circuit,
                self._mode,
            )
            # Show the accepted value now, in the data the value is read from;
            # the next poll replaces that data
            heating_setting = self._heating_setting()
            if isinstance(heating_setting, dict):
                heating_setting[self._temp_key] = int(value)
            self.async_write_ha_state()
            # Read the value back once the server has processed the change,
            # without holding the service call open meanwhile
            self._coordinator.async_schedule_refresh_after_write()
        else:
            _LOGGER.error(
                "Failed to set fixed water temperature for circuit %d (mode %d)",
                self._circuit,
                self._mode,
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}",
            manufacturer="Hitachi",
            model=f"{self._common_data.get('name', 'Unknown')} Remote Controller",
            sw_version=self._common_data.get("firmware"),
            identifiers={(DOMAIN, zone_device_identifier(self._sensor_data))},
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update sensor_data reference
        sensors_data = self._coordinator.get_sensors_data()
        self._sensor_data = next(
            (x for x in sensors_data if x.get("device_id") == self._sensor_data.get("device_id") and x.get("zone_id") == self._sensor_data.get("zone_id")),
            self._sensor_data,
        )
        self.async_write_ha_state()
