"""Coordinator Class to centralise all data fetching from CSNet Home."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CSNetHomeCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch all sensor data from the cloud API."""

    def __init__(self, hass: HomeAssistant, update_interval: int, entry_id: str):
        """Initialize the coordinator."""
        _LOGGER.debug("Configuring CSNetHome Coordinator")
        self.hass = hass
        self.entry_id = entry_id
        self.update_interval = timedelta(seconds=update_interval)
        self._device_data = {"sensors": [], "common_data": {}}
        self._last_alarm_codes: dict[str, int] = {}
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=self.update_interval,
        )

    async def _async_update_data(self):
        """Fetch data for all sensors."""

        _LOGGER.debug("Fetching all CSNet Home sensor data from API.")

        # Retrieve the CloudServiceAPI object from hass data
        cloud_api = self.hass.data[DOMAIN][self.entry_id]["api"]
        if not cloud_api:
            _LOGGER.error("No CloudServiceAPI instance found!")
            return

        # ensure translations are loaded before elements to enrich alarm messages
        await cloud_api.load_translations()

        # Fetch elements data, installation devices data, and alarms
        elements_data = await cloud_api.async_get_elements_data()
        installation_devices_data = (
            await cloud_api.async_get_installation_devices_data()
        )
        installation_alarms_data = await cloud_api.async_get_installation_alarms()

        if elements_data:
            self._device_data = elements_data
        else:
            self._device_data = {"sensors": [], "common_data": {}}

        # Add installation devices data to common_data
        if installation_devices_data and self._device_data.get("common_data"):
            self._device_data["common_data"][
                "installation_devices"
            ] = installation_devices_data

        # Add installation alarms data to common_data
        if installation_alarms_data and self._device_data.get("common_data"):
            self._device_data["common_data"][
                "installation_alarms"
            ] = installation_alarms_data

        # Raise notification if new alarm codes appear
        try:
            for sensor in self._device_data.get("sensors", []):
                key = f"{sensor.get('device_id')}-{sensor.get('room_id')}-{sensor.get('zone_id')}"
                alarm_code = sensor.get("alarm_code")
                if alarm_code is None or alarm_code == 0:
                    # clear last stored to allow future notifications
                    self._last_alarm_codes.pop(key, None)
                    continue

                prev_code = self._last_alarm_codes.get(key)
                if prev_code != alarm_code:
                    # store and notify
                    self._last_alarm_codes[key] = alarm_code
                    title = "Hitachi Device Alarm"
                    message_parts = [
                        f"Device: {sensor.get('device_name')} | Room: {sensor.get('room_name')}",
                        f"Code: {alarm_code}",
                    ]
                    alarm_msg = sensor.get("alarm_message")
                    if alarm_msg:
                        message_parts.append(f"Message: {alarm_msg}")
                    message = "\n".join(message_parts)
                    await self.hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": title,
                            "message": message,
                            "notification_id": f"csnet_home_alarm_{key}",
                        },
                        blocking=False,
                    )
        except Exception as exc:  # pragma: no cover - do not fail updates on notify
            _LOGGER.debug("Alarm notification handling error: %s", exc)

        return self._device_data

    def get_sensors_data(self):
        """Return the list of sensor data."""

        return self._device_data["sensors"]

    def get_common_data(self):
        """Return common data shared between all sensors."""

        return self._device_data["common_data"]

    def get_installation_devices_data(self):
        """Return installation devices data."""

        return self._device_data.get("common_data", {}).get("installation_devices", {})

    def get_installation_alarms_data(self):
        """Return installation alarms data."""

        return self._device_data.get("common_data", {}).get("installation_alarms", {})

    def get_holiday_mode_units(self):
        """Return list of units with their holiday mode status.

        Returns:
            list: List of dicts with unit info and holiday mode data
        """
        units = []
        installation_devices = self.get_installation_devices_data()

        if not installation_devices or "data" not in installation_devices:
            return units

        for outdoor in installation_devices.get("data", []):
            for indoor in outdoor.get("indoors", []):
                unit_id = indoor.get("id")
                if not unit_id:
                    continue

                unit_data = {
                    "unit_id": unit_id,
                    "unit_name": indoor.get("name", f"Unit {unit_id}"),
                    "outdoor_id": outdoor.get("id"),
                    "outdoor_name": outdoor.get("name", "Outdoor Unit"),
                    "holiday_mode": indoor.get("holidayMode"),
                }
                units.append(unit_data)

        return units
