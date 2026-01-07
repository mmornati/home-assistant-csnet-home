"""Create a Number Component for Home Assistant to control fixed water temperature."""

import asyncio
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
    WATER_CIRCUIT_MAX_HEAT,
    WATER_CIRCUIT_MIN_HEAT,
)
from .coordinator import CSNetHomeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number platform for CSNet Home fixed water temperature."""
    _LOGGER.debug("Starting CSNet Home number setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None

    entities = []
    installation_devices_data = coordinator.get_installation_devices_data()

    if not installation_devices_data:
        _LOGGER.debug("No installation devices data available for number entities")
        return None

    # Get heating status from installation devices
    # Navigate through: data[0].indoors[0].heatingStatus and heatingSetting
    heating_status = None
    heating_setting = None
    data_array = installation_devices_data.get("data", [])
    if isinstance(data_array, list) and len(data_array) > 0:
        first_device = data_array[0]
        if isinstance(first_device, dict):
            indoors_array = first_device.get("indoors", [])
            if isinstance(indoors_array, list) and len(indoors_array) > 0:
                first_indoors = indoors_array[0]
                if isinstance(first_indoors, dict):
                    heating_status = first_indoors.get("heatingStatus", {})
                    heating_setting = first_indoors.get("heatingSetting", {})

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

        # Check heating mode
        otc_heat_key = f"otcTypeHeatC{circuit}"
        otc_heat_type = heating_status.get(otc_heat_key, 0)
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
                fix_temp_heat = heating_setting.get(f"fixTempHeatC{circuit}")
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
                        common_data.get("device_status", {}).get(
                            sensor_data.get("device_id"), {}
                        ),
                        circuit,
                        1,  # Heating mode
                        entry,
                    )
                )

        # Check cooling mode
        otc_cool_key = f"otcTypeCoolC{circuit}"
        otc_cool_type = heating_status.get(otc_cool_key, 0)
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
                fix_temp_cool = heating_setting.get(f"fixTempCoolC{circuit}")
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
                        common_data.get("device_status", {}).get(
                            sensor_data.get("device_id"), {}
                        ),
                        circuit,
                        0,  # Cooling mode
                        entry,
                    )
                )

    if entities:
        _LOGGER.info(
            "Created %d fixed water temperature number entities", len(entities)
        )
        async_add_entities(entities)
    else:
        _LOGGER.debug("No fixed water temperature entities created (OTC type not FIX)")

    return None


class CSNetHomeFixedWaterTemperatureNumber(CoordinatorEntity, NumberEntity):
    """Representation of a fixed water temperature number entity."""

    _attr_native_min_value = WATER_CIRCUIT_MIN_HEAT
    _attr_native_max_value = WATER_CIRCUIT_MAX_HEAT
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

        # Determine name based on mode
        mode_name = "Heating" if mode == 1 else "Cooling"
        circuit_name = f"C{circuit}"
        zone_name = sensor_data.get("room_name", f"Circuit {circuit}")

        self._attr_name = (
            f"{zone_name} Fixed Water Temperature {mode_name} {circuit_name}"
        )
        self._attr_unique_id = (
            f"{DOMAIN}-fixed-water-temp-{circuit_name.lower()}-"
            f"{mode_name.lower()}-{sensor_data.get('device_id')}"
        )

        _LOGGER.debug(
            "Initialized fixed water temperature number entity: %s (circuit %d, mode %d)",
            self._attr_name,
            circuit,
            mode,
        )

    @property
    def native_value(self) -> float | None:
        """Return the current fixed water temperature value."""
        installation_devices_data = self._coordinator.get_installation_devices_data()
        if not installation_devices_data:
            return None

        # Navigate through: data[0].indoors[0].heatingSetting
        heating_setting = None
        data_array = installation_devices_data.get("data", [])
        if isinstance(data_array, list) and len(data_array) > 0:
            first_device = data_array[0]
            if isinstance(first_device, dict):
                indoors_array = first_device.get("indoors", [])
                if isinstance(indoors_array, list) and len(indoors_array) > 0:
                    first_indoors = indoors_array[0]
                    if isinstance(first_indoors, dict):
                        heating_setting = first_indoors.get("heatingSetting", {})

        if not heating_setting:
            return None

        # Get the appropriate fixed temperature field
        if self._mode == 1:  # Heating mode
            temp_key = f"fixTempHeatC{self._circuit}"
        else:  # Cooling mode
            temp_key = f"fixTempCoolC{self._circuit}"

        value = heating_setting.get(temp_key)
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

        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        is_editable = cloud_api.is_fixed_water_temperature_editable(
            self._circuit, self._mode, installation_devices_data
        )

        return is_editable

    async def async_set_native_value(self, value: float) -> None:
        """Set the fixed water temperature value."""
        parent_id = self._sensor_data.get("parent_id")
        if not parent_id:
            _LOGGER.error("No parent_id found for fixed water temperature")
            return

        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        success = await cloud_api.async_set_fixed_water_temperature(
            self._circuit, parent_id, self._mode, value
        )

        if success:
            _LOGGER.debug(
                "Fixed water temperature set to %s for circuit %d (mode %d)",
                value,
                self._circuit,
                self._mode,
            )
            # Wait a short delay to ensure the server has processed the change
            # The API sometimes ignores calls between two requests
            await asyncio.sleep(1.5)
            # Request coordinator refresh to update the value immediately
            await self._coordinator.async_refresh()
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
            identifiers={
                (
                    DOMAIN,
                    f"{self._sensor_data['device_name']}-{self._sensor_data['room_name']}",
                )
            },
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update sensor_data reference
        sensors_data = self._coordinator.get_sensors_data()
        self._sensor_data = next(
            (
                x
                for x in sensors_data
                if x.get("device_id") == self._sensor_data.get("device_id")
                and x.get("zone_id") == self._sensor_data.get("zone_id")
            ),
            self._sensor_data,
        )
        self.async_write_ha_state()
