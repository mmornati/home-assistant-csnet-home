"""Create a Climate Component for Home Assistant."""

import asyncio
import logging

from homeassistant.components.climate import (
    FAN_AUTO,
    ClimateEntity,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import FAN_ON, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CONF_FAN_COIL_MODEL,
    CONF_MAX_TEMP_OVERRIDE,
    DEFAULT_FAN_COIL_MODEL,
    DOMAIN,
    FAN_COIL_MODEL_LEGACY,
    FAN_SPEED_MAP_LEGACY,
    FAN_SPEED_MAP_STANDARD,
    FAN_SPEED_REVERSE_MAP_LEGACY,
    FAN_SPEED_REVERSE_MAP_STANDARD,
    HEATING_MAX_TEMPERATURE,
    HEATING_MIN_TEMPERATURE,
    OPERATION_STATUS_MAP,
    OTC_COOLING_TYPE_NAMES,
    OTC_HEATING_TYPE_NAMES,
    WATER_CIRCUIT_MAX_HEAT,
    WATER_CIRCUIT_MIN_HEAT,
)
from .helpers import extract_heating_status

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the climate platform for CSNet Home."""
    _LOGGER.debug("Starting CSNet Home climate setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator:
        _LOGGER.error("No coordinator instance found!")
        return None
    # Add sensors based on the coordinator's data
    async_add_entities(
        [
            CSNetHomeClimate(
                hass,
                entry,
                sensor_data=sensor_data,
                common_data=coordinator.get_common_data()["device_status"][
                    sensor_data["device_id"]
                ],
            )
            for sensor_data in coordinator.get_sensors_data()
            if sensor_data.get("zone_id") != 3  # Skip if zone_id is 3
        ]
    )


class CSNetHomeClimate(ClimateEntity):
    """Representation of a thermostat (climate) entity."""

    def __init__(self, hass, entry, sensor_data, common_data):
        """Initialize the thermostat entity."""
        self.hass = hass
        self._sensor_data = sensor_data
        self._common_data = common_data
        self._attr_name = self._sensor_data["room_name"]
        self.entry = entry
        # Temperature limits will be computed dynamically based on mode
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        # Expose all modes supported by the API
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.HEAT_COOL,
        ]
        self._attr_preset_modes = ["comfort", "eco"]
        if self._sensor_data["ecocomfort"] and self._sensor_data["ecocomfort"] == 0:
            self._attr_preset_mode = "eco"
        else:
            self._attr_preset_mode = "comfort"

        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        installation_devices_data = coordinator.get_installation_devices_data()
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]

        # Determine Fan Coil type from config
        self._fan_model = self.entry.data.get(
            CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL
        )

        # Set the correct maps
        if self._fan_model == FAN_COIL_MODEL_LEGACY:
            self._fan_speed_map = FAN_SPEED_MAP_LEGACY
            self._fan_speed_reverse_map = FAN_SPEED_REVERSE_MAP_LEGACY
        else:
            self._fan_speed_map = FAN_SPEED_MAP_STANDARD
            self._fan_speed_reverse_map = FAN_SPEED_REVERSE_MAP_STANDARD

        # If user selects Legacy control it's assumed that a fan coil is installed
        if self._fan_model == FAN_COIL_MODEL_LEGACY:
            self._is_fan_coil = True
        else:
            # If it's Standard, then API detection is used
            self._is_fan_coil = cloud_api.is_fan_coil_compatible(
                installation_devices_data
            )

        if self._is_fan_coil:
            # Fan coil systems use fan speed control
            self._attr_fan_modes = list(self._fan_speed_map.keys())
        else:
            # Non-fan coil systems use silent mode (auto = normal, on = silent)
            self._attr_fan_modes = [FAN_AUTO, FAN_ON]

        self._assumed_fan_mode = self._get_fan_mode_from_data()

        self._attr_supported_features = (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.FAN_MODE
        )

        # cache for dynamically computed limits
        self._cached_limits: tuple[float | None, float | None] | None = None

    def _get_fan_mode_from_data(self):
        """Helper to read the fan mode from the raw API data."""
        if self._sensor_data is None:
            return FAN_AUTO if not self._is_fan_coil else "auto"

        if self._is_fan_coil:
            # Fan speed for fan coil
            zone_id = self._sensor_data.get("zone_id")
            circuit = 1 if zone_id == 1 else 2

            fan_speed_key = f"fan{circuit}_speed"
            fan_speed = self._sensor_data.get(fan_speed_key)

            if fan_speed is not None and fan_speed >= 0:
                return self._fan_speed_reverse_map.get(fan_speed, "auto")
            return "auto"

        # Silent mode for non fan coil systems
        silent_mode = self._sensor_data.get("silent_mode")
        # silent_mode: 0 = Off (auto), 1 = On (silent)
        if silent_mode == 1:
            return FAN_ON
        return FAN_AUTO

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._sensor_data is None:
            return None
        return self._sensor_data["current_temperature"]

    @property
    def hvac_mode(self):
        """Return the current operation mode."""
        # Operation mode can be COOL (0), HEAT (1), AUTO (2), or OFF
        if self._sensor_data is None:
            return HVACMode.OFF
        if self._sensor_data.get("on_off") == 0:
            return HVACMode.OFF
        mode = self._sensor_data.get("mode")
        if mode == 0:
            return HVACMode.COOL
        if mode == 1:
            return HVACMode.HEAT
        if mode == 2:
            return HVACMode.HEAT_COOL
        return HVACMode.OFF

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self._sensor_data is None:
            return "comfort"
        eco_comfort = self._sensor_data.get("ecocomfort")
        if eco_comfort == 0:
            return "eco"
        if eco_comfort == 1:
            return "comfort"
        # If not available (-1) default to comfort
        return "comfort"

    @property
    def fan_mode(self):
        """Return the current fan mode (fan speed for fan coil, silent mode otherwise)."""
        return self._assumed_fan_mode

    @property
    def target_temperature(self):
        """Return the target temperature set by the user."""
        if self._sensor_data is None:
            return None

        zone_id = self._sensor_data.get("zone_id")

        # For water circuits (zone 5, 6), only return target temperature if OTC type is FIX
        if zone_id in [5, 6]:  # Water circuits (C1_WATER, C2_WATER)
            # Get installation devices data to check OTC type
            coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
            installation_devices_data = coordinator.get_installation_devices_data()

            if installation_devices_data:
                cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
                mode = self._sensor_data.get("mode", 1)

                # Determine circuit number from zone_id
                circuit = 1 if zone_id == 5 else 2

                # Check if fixed temperature is editable (OTC type is FIX)
                is_editable = cloud_api.is_fixed_water_temperature_editable(
                    circuit, mode, installation_devices_data
                )

                if not is_editable:
                    return None

        return self._sensor_data["setting_temperature"]

    @property
    def min_temp(self):
        """Return the minimum temperature based on current mode and API data."""
        limits = self._calculate_temperature_limits()
        return limits[0]

    @property
    def max_temp(self):
        """Return the maximum temperature based on current mode and API data."""
        if self._sensor_data is None:
            return HEATING_MAX_TEMPERATURE

        # Check for user override first
        max_temp_override = self.entry.data.get(CONF_MAX_TEMP_OVERRIDE)
        if max_temp_override is not None:
            return max_temp_override

        limits = self._calculate_temperature_limits()
        return limits[1]

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-climate-{self._sensor_data['device_id']}-{self._sensor_data['room_name']}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_name = self._sensor_data.get("device_name", "Unknown Device")
        room_name = self._sensor_data.get("room_name", "Unknown Room")
        device_id = self._sensor_data.get("device_id")

        # Handle both data structures:
        # 1. Device-specific dict (initial): _common_data = {"name": "...", "firmware": "..."}
        # 2. Full common_data dict (after update): _common_data = {"device_status": {...}}
        if "device_status" in self._common_data:
            # After update: nested structure
            device_status = self._common_data.get("device_status", {}).get(
                device_id, {}
            )
            device_name_from_status = device_status.get("name", "Unknown")
            firmware = device_status.get("firmware")
        else:
            # Initial state: direct access
            device_name_from_status = self._common_data.get("name", "Unknown")
            firmware = self._common_data.get("firmware")

        return DeviceInfo(
            name=f"{device_name}-{room_name}",
            manufacturer="Hitachi",
            model=f"{device_name_from_status} Remote Controller",
            sw_version=firmware,  # None is acceptable for DeviceInfo
            identifiers={
                (
                    DOMAIN,
                    f"{device_name}-{room_name}",
                )
            },
        )

    @property
    def hvac_action(self):
        """Return the current running HVAC action."""
        # Prefer real operating mode if available
        if self.is_heating():
            return HVACAction.HEATING
        if self.is_cooling():
            return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def extra_state_attributes(self):
        """Return additional attributes from elements API."""
        if self._sensor_data is None:
            return {}

        # Decode operation_status to human-readable format
        operation_status = self._sensor_data.get("operation_status")
        operation_status_text = OPERATION_STATUS_MAP.get(
            operation_status, f"Unknown ({operation_status})"
        )

        attrs = {
            "real_mode": self._sensor_data.get("real_mode"),
            "operation_status": operation_status,
            "operation_status_text": operation_status_text,
            "timer_running": self._sensor_data.get("timer_running"),
            "alarm_code": self._sensor_data.get("alarm_code"),
            "c1_demand": self._sensor_data.get("c1_demand"),
            "c2_demand": self._sensor_data.get("c2_demand"),
            "doingBoost": self._sensor_data.get("doingBoost"),
            "silent_mode": self._sensor_data.get("silent_mode"),
            "fan_coil_model": self._fan_model,
        }

        # Get installation devices data (used by both fan coil and OTC)
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        installation_devices_data = coordinator.get_installation_devices_data()

        # Add fan speed information for fan coil systems
        if self._is_fan_coil:
            attrs["is_fan_coil_compatible"] = True
            attrs["fan1_speed"] = self._sensor_data.get("fan1_speed")
            attrs["fan2_speed"] = self._sensor_data.get("fan2_speed")

            # Add fan control availability info
            cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
            mode = self._sensor_data.get("mode", 1)

            attrs["fan1_control_available"] = cloud_api.get_fan_control_availability(
                1, mode, installation_devices_data
            )
            attrs["fan2_control_available"] = cloud_api.get_fan_control_availability(
                2, mode, installation_devices_data
            )
        else:
            attrs["is_fan_coil_compatible"] = False

        # Add OTC (Outdoor Temperature Compensation) information
        if installation_devices_data:
            heating_status = extract_heating_status(installation_devices_data) or {}
            zone_id = self._sensor_data.get("zone_id")

            # Determine which circuit this zone belongs to
            circuit = None
            if zone_id in [1, 5]:  # Zone 1 or C1 Water use circuit 1
                circuit = 1
            elif zone_id in [2, 6]:  # Zone 2 or C2 Water use circuit 2
                circuit = 2

            if circuit:
                # Get OTC types for this circuit
                otc_heat_key = f"otcTypeHeatC{circuit}"
                otc_cool_key = f"otcTypeCoolC{circuit}"

                otc_heat_type = heating_status.get(otc_heat_key)
                otc_cool_type = heating_status.get(otc_cool_key)

                if otc_heat_type is not None:
                    attrs["otc_heating_type"] = otc_heat_type
                    attrs["otc_heating_type_name"] = OTC_HEATING_TYPE_NAMES.get(
                        otc_heat_type, f"Unknown ({otc_heat_type})"
                    )

                if otc_cool_type is not None:
                    attrs["otc_cooling_type"] = otc_cool_type
                    attrs["otc_cooling_type_name"] = OTC_COOLING_TYPE_NAMES.get(
                        otc_cool_type, f"Unknown ({otc_cool_type})"
                    )

        return attrs

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature for a room."""
        temperature = kwargs.get("temperature")
        zone_id = self._sensor_data.get("zone_id")

        # For water circuits (zone 5, 6), only allow temperature changes if OTC type is FIX
        if zone_id in [5, 6]:  # Water circuits (C1_WATER, C2_WATER)
            # Get installation devices data to check OTC type
            coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
            installation_devices_data = coordinator.get_installation_devices_data()

            if installation_devices_data:
                cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
                mode = self._sensor_data.get("mode", 1)

                # Determine circuit number from zone_id
                circuit = 1 if zone_id == 5 else 2

                # Check if fixed temperature is editable (OTC type is FIX)
                is_editable = cloud_api.is_fixed_water_temperature_editable(
                    circuit, mode, installation_devices_data
                )

                if not is_editable:
                    _LOGGER.warning(
                        "Cannot set temperature for water circuit %d: OTC type is not FIX. "
                        "Use the fixed water temperature number entity instead.",
                        circuit,
                    )
                    return

        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.async_set_temperature(
            zone_id,
            self._sensor_data["parent_id"],
            self._sensor_data["mode"],
            temperature=temperature,
        )
        if response:
            self._sensor_data["setting_temperature"] = temperature
            # For water circuits (zone 5, 6), refresh data to get updated fixed temperature
            if zone_id in [5, 6]:
                # Wait a short delay to ensure the server has processed the change
                await asyncio.sleep(1.5)
                # Request coordinator refresh to update the value immediately
                coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
                await coordinator.async_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        await cloud_api.async_set_hvac_mode(
            self._sensor_data["zone_id"], self._sensor_data["parent_id"], hvac_mode
        )

    async def async_turn_on(self) -> None:
        """Turn the climate device on (preserve current mode if possible)."""
        desired_mode = self.hvac_mode
        if desired_mode == HVACMode.OFF:
            # fallback to last known mode or HEAT
            mode = self._sensor_data.get("mode")
            if mode == 0:
                desired_mode = HVACMode.COOL
            elif mode == 1:
                desired_mode = HVACMode.HEAT
            elif mode == 2:
                desired_mode = HVACMode.HEAT_COOL
            else:
                desired_mode = HVACMode.HEAT
        await self.async_set_hvac_mode(desired_mode)

    async def async_turn_off(self) -> None:
        """Turn the climate device off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        response = await cloud_api.set_preset_modes(
            self._sensor_data["zone_id"],
            self._sensor_data["parent_id"],
            preset_mode,
            current_mode=self._sensor_data.get("mode"),
            on_off=self._sensor_data.get("on_off"),
        )
        if response:
            self._sensor_data["ecocomfort"] = 1 if preset_mode == "eco" else 0

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode (fan speed for fan coil, silent mode otherwise)."""
        cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]

        if self._is_fan_coil:
            # For fan coil systems, set the fan speed
            if fan_mode not in self._fan_speed_map:
                _LOGGER.warning("Invalid fan mode %s for fan coil system", fan_mode)
                return

            fan_speed = self._fan_speed_map[fan_mode]

            # Determine which circuit to use based on zone_id
            zone_id = self._sensor_data.get("zone_id")
            # Zone 1 uses C1, Zone 2 uses C2
            circuit = 1 if zone_id == 1 else 2

            # Check if fan control is available for this circuit
            coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
            installation_devices_data = coordinator.get_installation_devices_data()
            mode = self._sensor_data.get("mode", 1)
            # Skip the API check if the user has selected Legacy
            check_availability = self._fan_model != FAN_COIL_MODEL_LEGACY

            if check_availability and not cloud_api.get_fan_control_availability(
                circuit, mode, installation_devices_data
            ):
                _LOGGER.warning(
                    "Fan control not available for circuit %s in mode %s", circuit, mode
                )
                return

            response = await cloud_api.async_set_fan_speed(
                self._sensor_data["zone_id"],
                self._sensor_data["parent_id"],
                fan_speed,
                circuit,
            )
            if response:
                self._assumed_fan_mode = fan_mode
        else:
            # For non-fan coil systems, set silent mode
            silent_mode = fan_mode == FAN_ON
            response = await cloud_api.async_set_silent_mode(
                self._sensor_data["zone_id"],
                self._sensor_data["parent_id"],
                silent_mode,
            )
            if response:
                self._assumed_fan_mode = fan_mode

    def is_heating(self):
        """Return true if the thermostat is currently heating."""
        if self._sensor_data is None:
            return False
        return (
            self._sensor_data.get("on_off") == 1
            and self._sensor_data.get("mode") == 1
            and self._sensor_data.get("setting_temperature")
            > self._sensor_data.get("current_temperature")
        )

    def is_cooling(self):
        """Return true if the thermostat is currently cooling."""
        if self._sensor_data is None:
            return False
        return (
            self._sensor_data.get("on_off") == 1
            and self._sensor_data.get("mode") == 0
            and self._sensor_data.get("setting_temperature")
            < self._sensor_data.get("current_temperature")
        )

    async def async_update(self):
        """Update the thermostat data from the API."""
        _LOGGER.debug("Updating CSNet Home refresh request %s", self._attr_name)
        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        if not coordinator:
            _LOGGER.error("No coordinator instance found!")
            return
        await coordinator.async_request_refresh()
        self._sensor_data = next(
            (
                x
                for x in coordinator.get_sensors_data()
                if x.get("room_name") == self._attr_name
            ),
            None,
        )
        if self._sensor_data is None:
            _LOGGER.warning(
                "No sensor data found for room %s after coordinator refresh",
                self._attr_name,
            )
            return

        # Obtain real state from API
        api_fan_mode = self._get_fan_mode_from_data()

        # Save current speed for Legacy Control
        if (
            self._is_fan_coil
            and self._fan_model == FAN_COIL_MODEL_LEGACY
            and api_fan_mode == "auto"
            and self._assumed_fan_mode not in ["auto", None]
        ):
            # Preserve the cached assumed fan mode
            pass
        else:
            self._assumed_fan_mode = api_fan_mode

        self._common_data = coordinator.get_common_data()
        # reset cached limits after data refresh
        self._cached_limits = None

    def _normalize_temperature_limit(self, value: float | int | None) -> float | None:
        """Convert raw API limit values to Celsius and validate."""
        if value is None:
            return None

        try:
            val = float(value)
        except (TypeError, ValueError):
            return None

        # Filter out invalid or sentinel values
        if val <= 0:
            return None

        # Air circuit values are tenths of °C (e.g. 190 => 19.0)
        if val > 200:
            val = round(val / 10, 1)

        return val

    def _calculate_temperature_limits(self) -> tuple[float, float]:
        """Compute sanitized temperature limits with sensible fallbacks."""
        if self._cached_limits is not None:
            return self._cached_limits

        if self._sensor_data is None:
            self._cached_limits = (HEATING_MIN_TEMPERATURE, HEATING_MAX_TEMPERATURE)
            return self._cached_limits

        zone_id = self._sensor_data.get("zone_id")
        default_min = (
            WATER_CIRCUIT_MIN_HEAT if zone_id in [5, 6] else HEATING_MIN_TEMPERATURE
        )
        default_max = (
            WATER_CIRCUIT_MAX_HEAT if zone_id in [5, 6] else HEATING_MAX_TEMPERATURE
        )

        min_limit = default_min
        max_limit = default_max

        coordinator = self.hass.data[DOMAIN][self.entry.entry_id]["coordinator"]
        installation_devices_data = coordinator.get_installation_devices_data()

        if installation_devices_data:
            cloud_api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
            mode = self._sensor_data.get("mode", 1)
            raw_min, raw_max = cloud_api.get_temperature_limits(
                zone_id, mode, installation_devices_data
            )

            normalized_min = self._normalize_temperature_limit(raw_min)
            normalized_max = self._normalize_temperature_limit(raw_max)

            if normalized_min is not None:
                min_limit = normalized_min
            if normalized_max is not None:
                max_limit = normalized_max

        # Ensure limits remain logical
        if min_limit >= max_limit:
            min_limit = default_min
            max_limit = default_max

        self._cached_limits = (min_limit, max_limit)
        return self._cached_limits
