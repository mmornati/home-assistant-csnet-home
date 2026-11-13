"""Test the integration's config entry setup and unload."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home import async_setup_entry, async_unload_entry
from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.coordinator import CSNetHomeData


async def test_setup_entry_registers_no_update_listener(hass):
    """The flows own reloads; an update listener breaks from HA 2026.12.

    With a listener registered, reconfigure via ``async_update_reload_and_abort``
    logs a deprecation in 2026.11 and stops working in 2026.12.
    """
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    with (
        patch("custom_components.csnet_home.CSNetHomeCoordinator", return_value=coordinator),
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()),
        patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)),
    ):
        assert await async_setup_entry(hass, entry)
        assert entry.update_listeners == []

        assert await async_unload_entry(hass, entry)


async def test_setup_entry_keeps_api_and_coordinator_on_the_entry(hass):
    """The entry carries its API client and coordinator; nothing goes into hass.data."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    with (
        patch("custom_components.csnet_home.CSNetHomeCoordinator", return_value=coordinator) as coordinator_cls,
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()),
        patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)),
    ):
        assert await async_setup_entry(hass, entry)

        api = entry.runtime_data.api
        assert entry.runtime_data.coordinator is coordinator
        # the coordinator is given the same client and the entry it belongs to
        assert coordinator_cls.call_args.kwargs["api"] is api
        assert coordinator_cls.call_args.kwargs["config_entry"] is entry
        assert DOMAIN not in hass.data

        with patch.object(api, "close", AsyncMock()) as close:
            assert await async_unload_entry(hass, entry)
        close.assert_awaited_once()


async def test_unload_keeps_the_session_when_platforms_do_not_unload(hass):
    """A refused unload leaves the entry running, so its session stays open."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)
    api = MagicMock()
    api.close = AsyncMock()
    entry.runtime_data = CSNetHomeData(api=api, coordinator=MagicMock())

    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)):
        assert not await async_unload_entry(hass, entry)
    api.close.assert_not_awaited()


async def test_failed_first_refresh_closes_the_session(hass):
    """Setup is retried with a new client, so the one that failed must not stay open."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock(side_effect=ConfigEntryNotReady("CSNet Manager unreachable"))
    with (
        patch("custom_components.csnet_home.CSNetHomeCoordinator", return_value=coordinator),
        patch("custom_components.csnet_home.CSNetHomeAPI.close", AsyncMock()) as close,
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, entry)
    close.assert_awaited_once()


async def test_delete_alarm_service_uses_the_loaded_entry(hass):
    """The service reaches the API and coordinator through the loaded entry."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    with (
        patch("custom_components.csnet_home.CSNetHomeCoordinator", return_value=coordinator),
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()),
    ):
        assert await async_setup_entry(hass, entry)

    api = entry.runtime_data.api
    api.installation_id = 4242
    with patch.object(api, "async_delete_alarm", AsyncMock(return_value=True)) as delete_alarm:
        # not loaded yet: the service must not touch an entry that is not running
        await hass.services.async_call(DOMAIN, "delete_alarm", {"alarm_id": "17"}, blocking=True)
        delete_alarm.assert_not_awaited()

        entry.mock_state(hass, ConfigEntryState.LOADED)
        await hass.services.async_call(DOMAIN, "delete_alarm", {"alarm_id": "17"}, blocking=True)
        delete_alarm.assert_awaited_once_with(4242, 17)
    coordinator.async_request_refresh.assert_awaited_once()
