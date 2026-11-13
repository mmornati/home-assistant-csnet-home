"""Main Files for the CSNet Home Hitachi integration."""

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.storage import Store

from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.const import (
    CONF_ENABLE_ALARM_NOTIFICATIONS,
    CONF_FILTERED_ALARM_CODES,
    CONF_LANGUAGE,
    DEFAULT_ENABLE_ALARM_NOTIFICATIONS,
    DEFAULT_FILTERED_ALARM_CODES,
    DOMAIN,
)
from custom_components.csnet_home.coordinator import ALARM_STORAGE_VERSION, CSNetHomeConfigEntry, CSNetHomeCoordinator, CSNetHomeData, alarm_storage_key
from custom_components.csnet_home.migration import async_migrate_zone_identifiers
from custom_components.csnet_home.sensor import DEVICE_SENSOR_DESCRIPTIONS, ZONE_SENSOR_DESCRIPTIONS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SCAN_INTERVAL = 60
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.WATER_HEATER,
    Platform.NUMBER,
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the CSNet Home component."""
    _LOGGER.debug("Initializing CSNet Home Service integration")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: CSNetHomeConfigEntry):
    """Set up CSNet Home from a config entry."""
    _LOGGER.debug("Config entry found")
    username = entry.data.get("username")
    password = entry.data.get("password")

    # Initialize the CloudServiceAPI with credentials from config
    api = CSNetHomeAPI(hass, username, password)
    # store preferred language for translations
    api.preferred_language = entry.data.get(CONF_LANGUAGE)

    _LOGGER.debug("Starting CSNet Home sensor setup")
    coordinator = CSNetHomeCoordinator(
        hass,
        entry.data.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL),
        entry.entry_id,
        entry.data.get(CONF_ENABLE_ALARM_NOTIFICATIONS, DEFAULT_ENABLE_ALARM_NOTIFICATIONS),
        entry.data.get(CONF_FILTERED_ALARM_CODES, DEFAULT_FILTERED_ALARM_CODES),
        api=api,
        config_entry=entry,
    )

    try:
        await coordinator.async_config_entry_first_refresh()

        entry.runtime_data = CSNetHomeData(api=api, coordinator=coordinator)

        # Entities used to be keyed on the CSNet room name; move them to stable
        # zone ids before the platforms register them.
        async_migrate_zone_identifiers(
            hass,
            entry,
            coordinator.get_sensors_data(),
            [d.key for d in (*ZONE_SENSOR_DESCRIPTIONS, *DEVICE_SENSOR_DESCRIPTIONS)],
        )

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        # a failed setup is never unloaded, and a retry makes a new client:
        # do not leave this one's session open
        await api.close()
        raise

    async def async_handle_delete_alarm(call: ServiceCall):
        """Handle the delete alarm service call."""
        alarm_id_input = call.data.get("alarm_id")

        # Convert to int if it's a string (handles both direct ID and templates)
        if alarm_id_input is None:
            _LOGGER.error("alarm_id is required")
            return
        try:
            alarm_id = int(alarm_id_input)
        except (ValueError, TypeError):
            _LOGGER.error("Invalid alarm_id: %s", alarm_id_input)
            return

        # Iterate over all configured entries to find the API
        # In most cases there's only one
        for loaded_entry in hass.config_entries.async_entries(DOMAIN):
            if loaded_entry.state is not ConfigEntryState.LOADED:
                continue
            api_instance = loaded_entry.runtime_data.api
            coordinator_instance = loaded_entry.runtime_data.coordinator

            if api_instance and api_instance.installation_id:
                _LOGGER.debug(
                    "Attempting to delete alarm %s for installation %s",
                    alarm_id,
                    api_instance.installation_id,
                )
                success = await api_instance.async_delete_alarm(api_instance.installation_id, alarm_id)
                if success:
                    _LOGGER.info("Successfully deleted alarm %s", alarm_id)
                    # Refresh data to remove the alarm from sensors/notifications
                    coordinator_instance.async_invalidate_installation_alarms()
                    await coordinator_instance.async_request_refresh()
                    return

        _LOGGER.error(
            "Could not delete alarm %s: No active session or installation ID found",
            alarm_id,
        )

    # One service for all entries: it looks the entries up when it is called
    if not hass.services.has_service(DOMAIN, "delete_alarm"):
        hass.services.async_register(DOMAIN, "delete_alarm", async_handle_delete_alarm)

    return True


async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry) -> bool:
    """Delete device if selected from UI."""
    # Adding this function shows the delete device option in the UI.
    # Remove this function if you do not want that option.
    # You may need to do some checks here before allowing devices to be removed.
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete what the removed entry kept in storage."""
    await Store(hass, ALARM_STORAGE_VERSION, alarm_storage_key(entry.entry_id)).async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: CSNetHomeConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when you remove your integration or shutdown HA.
    # If you have created any custom services, they need to be removed here too.

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Home Assistant drops entry.runtime_data itself; the session is ours to close
    if unload_ok:
        await entry.runtime_data.api.close()

    # Return that unloading was successful.
    return unload_ok
