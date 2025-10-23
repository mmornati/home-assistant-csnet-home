"""Test Switch Platform for Holiday Mode."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.csnet_home.switch import HolidayModeSwitch, async_setup_entry


@pytest.mark.asyncio
async def test_switch_setup_entry(hass):
    """Test setting up holiday mode switches."""
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(
        return_value=[
            {
                "unit_id": 201,
                "unit_name": "Living Room",
                "outdoor_id": 100,
                "outdoor_name": "Outdoor Unit",
                "holiday_mode": None,
            }
        ]
    )

    api = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"

    hass.data = {
        "csnet_home": {
            "test_entry": {
                "coordinator": coordinator,
                "api": api,
            }
        }
    }

    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    assert async_add_entities.called
    added_entities = async_add_entities.call_args[0][0]
    entities_list = list(added_entities)
    assert len(entities_list) == 1


@pytest.mark.asyncio
async def test_switch_setup_entry_no_units(hass):
    """Test setting up holiday mode switches when no units available."""
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])

    api = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"

    hass.data = {
        "csnet_home": {
            "test_entry": {
                "coordinator": coordinator,
                "api": api,
            }
        }
    }

    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    assert not async_add_entities.called


def test_switch_initialization():
    """Test holiday mode switch initialization."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    api = MagicMock()

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": None,
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    assert switch._unit_id == 201
    assert switch._unit_name == "Living Room"
    assert switch._attr_name == "Living Room Holiday Mode"
    assert switch._attr_unique_id == "csnet_home-holiday-mode-201"
    assert switch._attr_is_on is False


def test_switch_state_inactive():
    """Test switch state when holiday mode is inactive."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    api = MagicMock()

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": None,
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    assert switch._attr_is_on is False
    assert switch._attr_extra_state_attributes == {}


def test_switch_state_active():
    """Test switch state when holiday mode is active."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(
        return_value=[
            {
                "unit_id": 201,
                "unit_name": "Living Room",
                "outdoor_id": 100,
                "outdoor_name": "Outdoor Unit",
                "holiday_mode": {
                    "year": 2030,  # Future date
                    "month": 12,
                    "day": 25,
                    "hour": 14,
                    "minute": 30,
                },
            }
        ]
    )
    api = MagicMock()

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": {
            "year": 2030,
            "month": 12,
            "day": 25,
            "hour": 14,
            "minute": 30,
        },
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    assert switch._attr_is_on is True
    assert "return_date" in switch._attr_extra_state_attributes
    assert switch._attr_extra_state_attributes["return_date"] == "2030-12-25"
    assert switch._attr_extra_state_attributes["return_time"] == "14:30"


def test_switch_state_expired():
    """Test switch state when holiday mode has expired."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    api = MagicMock()

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": {
            "year": 2020,  # Past date
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
        },
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    assert switch._attr_is_on is False


@pytest.mark.asyncio
async def test_switch_turn_on():
    """Test turning on holiday mode."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    coordinator.async_request_refresh = AsyncMock()

    api = MagicMock()
    api.async_set_holiday_mode = AsyncMock(return_value=True)

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": None,
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    await switch.async_turn_on()

    api.async_set_holiday_mode.assert_called_once()
    call_args = api.async_set_holiday_mode.call_args
    # Check positional arguments (unit_id is first arg)
    assert call_args[0][0] == 201
    # Should set for ~7 days from now
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_switch_turn_on_with_custom_date():
    """Test turning on holiday mode with custom date."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    coordinator.async_request_refresh = AsyncMock()

    api = MagicMock()
    api.async_set_holiday_mode = AsyncMock(return_value=True)

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": None,
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    await switch.async_turn_on(return_date="2025-12-25", return_time="15:30")

    api.async_set_holiday_mode.assert_called_once()
    call_args = api.async_set_holiday_mode.call_args
    # Check positional arguments
    assert call_args[0][0] == 201  # unit_id
    assert call_args[0][1] == 2025  # year
    assert call_args[0][2] == 12  # month
    assert call_args[0][3] == 25  # day
    assert call_args[0][4] == 15  # hour
    assert call_args[0][5] == 30  # minute


@pytest.mark.asyncio
async def test_switch_turn_on_failure():
    """Test turning on holiday mode when API fails."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    coordinator.async_request_refresh = AsyncMock()

    api = MagicMock()
    api.async_set_holiday_mode = AsyncMock(return_value=False)

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": None,
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    await switch.async_turn_on()

    api.async_set_holiday_mode.assert_called_once()
    # Should not refresh if API call failed
    coordinator.async_request_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_switch_turn_off():
    """Test turning off holiday mode."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    coordinator.async_request_refresh = AsyncMock()

    api = MagicMock()
    api.async_stop_holiday_mode = AsyncMock(return_value=True)

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": {
            "year": 2030,
            "month": 12,
            "day": 25,
            "hour": 14,
            "minute": 30,
        },
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    await switch.async_turn_off()

    api.async_stop_holiday_mode.assert_called_once_with(201)
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_switch_turn_off_failure():
    """Test turning off holiday mode when API fails."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    coordinator.async_request_refresh = AsyncMock()

    api = MagicMock()
    api.async_stop_holiday_mode = AsyncMock(return_value=False)

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": {
            "year": 2030,
            "month": 12,
            "day": 25,
            "hour": 14,
            "minute": 30,
        },
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    await switch.async_turn_off()

    api.async_stop_holiday_mode.assert_called_once_with(201)
    # Should not refresh if API call failed
    coordinator.async_request_refresh.assert_not_called()


def test_switch_available():
    """Test switch availability based on coordinator status."""
    hass = MagicMock()
    entry = MagicMock()
    coordinator = MagicMock()
    coordinator.get_holiday_mode_units = MagicMock(return_value=[])
    coordinator.last_update_success = True
    api = MagicMock()

    unit_data = {
        "unit_id": 201,
        "unit_name": "Living Room",
        "outdoor_id": 100,
        "outdoor_name": "Outdoor Unit",
        "holiday_mode": None,
    }

    switch = HolidayModeSwitch(hass, entry, coordinator, api, unit_data)

    assert switch.available is True

    coordinator.last_update_success = False
    assert switch.available is False
