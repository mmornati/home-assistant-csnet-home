"""Test the integration's config entry setup and unload."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import ServiceRegistry
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home import async_remove_entry, async_setup_entry, async_unload_entry
from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.coordinator import CSNetHomeData, alarm_storage_key


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
    # the alarm list is read again right away instead of after five minutes
    coordinator.async_invalidate_installation_alarms.assert_called_once()
    coordinator.async_request_refresh.assert_awaited_once()


async def test_real_coordinator_through_setup_reload_and_unload(hass, enable_custom_integrations):
    """Home Assistant sets up, reloads and unloads the entry with the real coordinator."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.csnet_home.coordinator.CSNetHomeCoordinator._async_update_data",
            AsyncMock(return_value={"sensors": [], "common_data": {}}),
        ),
        patch("custom_components.csnet_home.CSNetHomeAPI.close", AsyncMock()) as close,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        coordinator = entry.runtime_data.coordinator
        assert coordinator.config_entry is entry
        assert coordinator.api is entry.runtime_data.api

        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        assert entry.runtime_data.coordinator is not coordinator
        assert close.await_count == 1

        assert await hass.config_entries.async_unload(entry.entry_id)
        assert close.await_count == 2
        # with nothing loaded the service finds no entry and does not raise
        await hass.services.async_call(DOMAIN, "delete_alarm", {"alarm_id": 1}, blocking=True)


async def test_failed_platform_setup_closes_the_session(hass):
    """A failure after the first refresh also ends setup, so the session is closed there too."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    with (
        patch("custom_components.csnet_home.CSNetHomeCoordinator", return_value=coordinator),
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock(side_effect=RuntimeError("platform failed"))),
        patch("custom_components.csnet_home.CSNetHomeAPI.close", AsyncMock()) as close,
        pytest.raises(RuntimeError),
    ):
        await async_setup_entry(hass, entry)
    close.assert_awaited_once()


async def test_delete_alarm_service_is_registered_once(hass):
    """A second entry, or a reload, does not register the service again."""
    with (
        patch("custom_components.csnet_home.CSNetHomeCoordinator") as coordinator_cls,
        patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()),
        patch("homeassistant.core.ServiceRegistry.async_register", autospec=True, side_effect=ServiceRegistry.async_register) as register,
    ):
        coordinator_cls.return_value.async_config_entry_first_refresh = AsyncMock()
        for username in ("first", "second"):
            entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: username, CONF_PASSWORD: "pass"})
            entry.add_to_hass(hass)
            assert await async_setup_entry(hass, entry)

    assert [call.args[1:3] for call in register.call_args_list] == [(DOMAIN, "delete_alarm")]
    assert hass.services.has_service(DOMAIN, "delete_alarm")


async def test_removing_the_entry_deletes_its_stored_alarms(hass, hass_storage):
    """Nothing of a removed entry stays in Home Assistant's storage."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass"})
    key = alarm_storage_key(entry.entry_id)
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": {"installation_alarm_ids": [1]}}

    await async_remove_entry(hass, entry)

    assert key not in hass_storage
