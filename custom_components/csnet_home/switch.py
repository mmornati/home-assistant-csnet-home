"""Switch Platform for Holiday Mode Control."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Holiday Mode switches for CSNet Home."""
    _LOGGER.debug("Starting CSNet Home holiday mode switch setup")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    if not coordinator or not api:
        _LOGGER.error("No coordinator or API instance found!")
        return

    # Get units that support holiday mode
    units = coordinator.get_holiday_mode_units()

    if not units:
        _LOGGER.debug("No units with holiday mode support found")
        return

    switches = []
    for unit in units:
        switches.append(HolidayModeSwitch(hass, entry, coordinator, api, unit))

    async_add_entities(switches)
    _LOGGER.debug("Created %d holiday mode switches", len(switches))


class HolidayModeSwitch(SwitchEntity):
    """Representation of a Holiday Mode switch."""

    def __init__(self, hass, entry, coordinator, api, unit_data):
        """Initialize the holiday mode switch."""
        self.hass = hass
        self.entry = entry
        self._coordinator = coordinator
        self._api = api
        self._unit_data = unit_data
        self._unit_id = unit_data["unit_id"]
        self._unit_name = unit_data["unit_name"]

        self._attr_name = f"{self._unit_name} Holiday Mode"
        self._attr_unique_id = f"{DOMAIN}-holiday-mode-{self._unit_id}"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:palm-tree"

        # Create device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"unit-{self._unit_id}")},
            name=self._unit_name,
            manufacturer="Hitachi",
            model="Heat Pump Unit",
        )

        self._update_from_coordinator()

        _LOGGER.debug("Holiday mode switch initialized for unit %s", self._unit_id)

    def _update_from_coordinator(self):
        """Update the switch state from coordinator data."""
        units = self._coordinator.get_holiday_mode_units()

        # Find our unit in the updated data
        for unit in units:
            if unit["unit_id"] == self._unit_id:
                self._unit_data = unit
                break

        holiday_mode = self._unit_data.get("holiday_mode")

        if holiday_mode and isinstance(holiday_mode, dict):
            # Check if holiday mode is active (end date is in the future)
            try:
                end_date = datetime(
                    holiday_mode.get("year", 2000),
                    holiday_mode.get("month", 1),
                    holiday_mode.get("day", 1),
                    holiday_mode.get("hour", 0),
                    holiday_mode.get("minute", 0),
                )
                self._attr_is_on = datetime.now() < end_date

                # Add attributes with holiday mode details
                self._attr_extra_state_attributes = {
                    "return_date": end_date.strftime("%Y-%m-%d"),
                    "return_time": end_date.strftime("%H:%M"),
                    "return_datetime": end_date.isoformat(),
                }
            except (ValueError, TypeError) as e:
                _LOGGER.debug(
                    "Error parsing holiday mode date for unit %s: %s", self._unit_id, e
                )
                self._attr_is_on = False
                self._attr_extra_state_attributes = {}
        else:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on holiday mode (set for 7 days from now by default)."""
        # Default to 7 days from now at noon
        end_datetime = datetime.now() + timedelta(days=7)
        end_datetime = end_datetime.replace(hour=12, minute=0, second=0, microsecond=0)

        # Check if custom date/time was provided in service call
        if "return_date" in kwargs or "return_time" in kwargs:
            # Parse custom date/time if provided
            date_str = kwargs.get("return_date")
            time_str = kwargs.get("return_time", "12:00")

            if date_str:
                try:
                    date_parts = date_str.split("-")
                    time_parts = time_str.split(":")
                    end_datetime = datetime(
                        int(date_parts[0]),
                        int(date_parts[1]),
                        int(date_parts[2]),
                        int(time_parts[0]),
                        int(time_parts[1]) if len(time_parts) > 1 else 0,
                    )
                except (ValueError, IndexError) as e:
                    _LOGGER.error("Invalid date/time format: %s", e)
                    return

        success = await self._api.async_set_holiday_mode(
            self._unit_id,
            end_datetime.year,
            end_datetime.month,
            end_datetime.day,
            end_datetime.hour,
            end_datetime.minute,
        )

        if success:
            _LOGGER.debug(
                "Holiday mode enabled for unit %s until %s", self._unit_id, end_datetime
            )
            # Request coordinator update to refresh state
            await self._coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to enable holiday mode for unit %s", self._unit_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off holiday mode."""
        success = await self._api.async_stop_holiday_mode(self._unit_id)

        if success:
            _LOGGER.debug("Holiday mode disabled for unit %s", self._unit_id)
            # Request coordinator update to refresh state
            await self._coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to disable holiday mode for unit %s", self._unit_id)

    async def async_update(self):
        """Update the entity state."""
        self._update_from_coordinator()
