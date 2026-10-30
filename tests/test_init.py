"""Test the integration's config entry setup and unload."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home import async_setup_entry, async_unload_entry
from custom_components.csnet_home.const import DOMAIN


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
        assert entry.entry_id not in hass.data[DOMAIN]
