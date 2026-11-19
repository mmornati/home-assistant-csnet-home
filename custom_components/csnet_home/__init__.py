"""Main Files for the CSNet Home Hitachi integration."""

import logging

import voluptuous as vol
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.loader import async_get_integration

from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.const import (
    CONF_ENABLE_ALARM_NOTIFICATIONS,
    CONF_ENERGY_METER,
    CONF_FILTERED_ALARM_CODES,
    CONF_LANGUAGE,
    CONF_POWER_SUPPLY,
    CONF_USER_AGENT,
    DEFAULT_ENABLE_ALARM_NOTIFICATIONS,
    DEFAULT_FILTERED_ALARM_CODES,
    DOMAIN,
)
from custom_components.csnet_home.coordinator import ALARM_STORAGE_VERSION, CSNetHomeConfigEntry, CSNetHomeCoordinator, CSNetHomeData, alarm_storage_key
from custom_components.csnet_home.dashboard import async_register_dashboard
from custom_components.csnet_home.migration import async_migrate_zone_identifiers
from custom_components.csnet_home.power_calibration import POWER_CALIBRATION_STORAGE_VERSION, power_calibration_storage_key
from custom_components.csnet_home.sample_recorder import SHARE_URL, SampleRecorder, sample_header, sample_path
from custom_components.csnet_home.sensor import DEVICE_SENSOR_DESCRIPTIONS, ZONE_SENSOR_DESCRIPTIONS
from custom_components.csnet_home.server_energy import METER_STORAGE_VERSION, meter_storage_key

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SCAN_INTERVAL = 60

SERVICE_START_SAMPLE_RECORDING = "start_sample_recording"
SERVICE_STOP_SAMPLE_RECORDING = "stop_sample_recording"
SAMPLE_NOTIFICATION_ID = "csnet_home_sample_recording"
START_SAMPLE_RECORDING_SCHEMA = vol.Schema(
    {
        vol.Optional("duration_hours", default=48): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=336)),
        vol.Optional("meter_energy_entity"): cv.entity_id,
        vol.Optional("meter_power_entity"): cv.entity_id,
        vol.Optional("notes", default=""): cv.string,
    }
)
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.WATER_HEATER,
    Platform.NUMBER,
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the CSNet Home component."""
    _LOGGER.debug("Initializing CSNet Home Service integration")

    # the dashboard cards: served and listed in the card picker, whatever the entries
    integration = await async_get_integration(hass, DOMAIN)
    await async_register_dashboard(hass, str(integration.version))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CSNetHomeConfigEntry):
    """Set up CSNet Home from a config entry."""
    _LOGGER.debug("Config entry found")
    username = entry.data.get("username")
    password = entry.data.get("password")

    # Initialize the CloudServiceAPI with credentials from config
    api = CSNetHomeAPI(hass, username, password, user_agent=entry.data.get(CONF_USER_AGENT))
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
        entry.async_on_unload(coordinator.async_track_dismissed_notifications())
        entry.async_on_unload(coordinator.async_cancel_refresh_after_write)

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
    if not hass.services.has_service(DOMAIN, SERVICE_START_SAMPLE_RECORDING):
        hass.services.async_register(
            DOMAIN,
            SERVICE_START_SAMPLE_RECORDING,
            _async_handle_start_sample_recording,
            schema=START_SAMPLE_RECORDING_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )
        hass.services.async_register(DOMAIN, SERVICE_STOP_SAMPLE_RECORDING, _async_handle_stop_sample_recording)

    return True


def _loaded_entry(hass: HomeAssistant) -> CSNetHomeConfigEntry:
    """Return the loaded entry, or raise the error a service shows."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry
    raise ServiceValidationError("CSNet Home is not loaded")


async def _async_handle_start_sample_recording(call: ServiceCall) -> ServiceResponse:
    """Start recording what CSNet Manager sends to a sample file."""
    hass = call.hass
    entry = _loaded_entry(hass)
    api = entry.runtime_data.api
    if api.sample_recorder is not None:
        raise ServiceValidationError(f"A sample is already being recorded to {api.sample_recorder.path}")

    meter_energy = call.data.get("meter_energy_entity") or entry.data.get(CONF_ENERGY_METER)
    meter_power = call.data.get("meter_power_entity")
    duration = call.data["duration_hours"] * 3600
    integration = await async_get_integration(hass, DOMAIN)
    coordinator = entry.runtime_data.coordinator
    header = sample_header(
        integration_version=str(integration.version),
        scan_interval=coordinator.update_interval.total_seconds() if coordinator.update_interval else None,
        time_zone=hass.config.time_zone,
        power_supply=entry.data.get(CONF_POWER_SUPPLY),
        meter_energy=bool(meter_energy),
        meter_power=bool(meter_power),
        notes=call.data.get("notes"),
    )
    recorder = SampleRecorder(hass, sample_path(hass.config.config_dir), header, duration, meter_energy, meter_power)
    await recorder.async_start()
    api.sample_recorder = recorder

    async def _async_time_is_up(_now) -> None:
        await async_stop_sample_recording(hass, api)

    recorder.cancel_timer = async_call_later(hass, duration, _async_time_is_up)
    _LOGGER.info("Recording a sample to %s until %s", recorder.path, recorder.ends_at)
    return {"path": str(recorder.path), "ends_at": recorder.ends_at.isoformat(timespec="seconds")}


async def _async_handle_stop_sample_recording(call: ServiceCall) -> None:
    """Stop the sample recording now."""
    entry = _loaded_entry(call.hass)
    if entry.runtime_data.api.sample_recorder is None:
        raise ServiceValidationError("No sample is being recorded")
    await async_stop_sample_recording(call.hass, entry.runtime_data.api)


async def async_stop_sample_recording(hass: HomeAssistant, api: CSNetHomeAPI, notify: bool = True) -> None:
    """Stop a sample recording, write what is left and say where the file is."""
    recorder = getattr(api, "sample_recorder", None)
    if not isinstance(recorder, SampleRecorder):
        return
    api.sample_recorder = None
    cancel = getattr(recorder, "cancel_timer", None)
    if cancel:
        cancel()
    await recorder.async_flush()
    _LOGGER.info("Sample saved to %s (%s replies)", recorder.path, recorder.replies)
    if notify:
        persistent_notification.async_create(
            hass,
            f"The sample was saved to `{recorder.path}` ({recorder.replies} replies from CSNet Manager). "
            f"To share it so changes can be tested against your unit, see {SHARE_URL}.",
            title="CSNet Home sample recorded",
            notification_id=SAMPLE_NOTIFICATION_ID,
        )


async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry) -> bool:
    """Delete device if selected from UI."""
    # Adding this function shows the delete device option in the UI.
    # Remove this function if you do not want that option.
    # You may need to do some checks here before allowing devices to be removed.
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete what the removed entry kept in storage."""
    await Store(hass, ALARM_STORAGE_VERSION, alarm_storage_key(entry.entry_id)).async_remove()
    await Store(hass, METER_STORAGE_VERSION, meter_storage_key(entry.entry_id)).async_remove()
    await Store(hass, POWER_CALIBRATION_STORAGE_VERSION, power_calibration_storage_key(entry.entry_id)).async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: CSNetHomeConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when you remove your integration or shutdown HA.
    # If you have created any custom services, they need to be removed here too.

    # a recording in progress keeps what it has so far
    await async_stop_sample_recording(hass, entry.runtime_data.api, notify=False)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Home Assistant drops entry.runtime_data itself; the session is ours to close
    if unload_ok:
        await entry.runtime_data.api.close()

    # Return that unloading was successful.
    return unload_ok
