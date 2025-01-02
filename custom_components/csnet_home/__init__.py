# custom_components/my_cloud_service/__init__.py

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .api import CSNetHomeAPI
from .coordinator import CSNetHomeCoordinator
from dataclasses import dataclass
from collections.abc import Callable

from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = 60
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CLIMATE]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the CSNet Home component."""
    _LOGGER.debug("Initializing CSNet Home Service integration")

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up CSNet Home from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Config entry found")
    username = entry.data.get('username')
    password = entry.data.get('password')
    
    # Initialize the CloudServiceAPI with credentials from config
    api = CSNetHomeAPI(hass, username, password)

    _LOGGER.debug("Starting CSNet Home sensor setup")
    coordinator = CSNetHomeCoordinator(hass,entry.data.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL), entry.entry_id)

    # Initialise a listener for config flow options changes.
    # See config_flow for defining an options setting that shows up as configure on the integration.
    cancel_update_listener = entry.add_update_listener(_async_update_listener)
    
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator":coordinator, 
        "cancel_update_listener":cancel_update_listener, 
        "api":api
    }
    
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    

    return True

async def _async_update_listener(hass: HomeAssistant, config_entry):
    """Handle config options update."""
    # Reload the integration when the options change.
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Delete device if selected from UI."""
    # Adding this function shows the delete device option in the UI.
    # Remove this function if you do not want that option.
    # You may need to do some checks here before allowing devices to be removed.
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when you remove your integration or shutdown HA.
    # If you have created any custom services, they need to be removed here too.

    # Remove the config options update listener
    hass.data[DOMAIN][entry.entry_id]["cancel_update_listener"]()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    # Remove the config entry from the hass data object.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    # Return that unloading was successful.
    return unload_ok
