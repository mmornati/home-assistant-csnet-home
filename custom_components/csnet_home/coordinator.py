"""Coordinator Class to centralise all data fetching from CSNet Home."""

import logging
from datetime import timedelta

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

        # Enrich sensor data with correct temperatures from installation devices data
        # This fixes issue #137: water heater (zone_id 3) and water circuits (zone_id 5, 6)
        # need temperatures from heatingStatus, not from elements API
        if installation_devices_data and self._device_data.get("sensors"):
            heating_status = cloud_api.get_heating_status_from_installation_devices(
                installation_devices_data
            )
            if heating_status:
                for sensor in self._device_data["sensors"]:
                    zone_id = sensor.get("zone_id")
                    # For zone_id 3 (DHW/water heater), use tempDHW from heatingStatus
                    if zone_id == 3:
                        temp_dhw = heating_status.get("tempDHW")
                        if temp_dhw is not None:
                            sensor["current_temperature"] = temp_dhw
                            _LOGGER.debug(
                                "Enriched zone_id 3 (DHW) current_temperature: %s",
                                temp_dhw,
                            )
                    # For zone_id 5 (C1_WATER), use waterOutletHPTemp from heatingStatus
                    # BUT: elementType 5 can also represent HEAT elements (parentName "Heat")
                    # Only enrich if it's actually a water circuit, not a heat circuit
                    elif zone_id == 5:
                        room_name = sensor.get("room_name", "").lower()
                        # Skip enrichment for HEAT elements (parentName "Heat")
                        # Only enrich actual water circuits
                        if "heat" not in room_name:
                            temp_c1_water = heating_status.get("waterOutletHPTemp")
                            if temp_c1_water is not None:
                                sensor["current_temperature"] = temp_c1_water
                                _LOGGER.debug(
                                    "Enriched zone_id 5 (C1_WATER) current_temperature: %s",
                                    temp_c1_water,
                                )
                        else:
                            _LOGGER.debug(
                                "Skipping enrichment for zone_id 5 with room_name '%s' (HEAT element, not water circuit)",
                                sensor.get("room_name"),
                            )
                    # For zone_id 6 (C2_WATER), use waterOutlet2Temp from heatingStatus
                    elif zone_id == 6:
                        temp_c2_water = heating_status.get("waterOutlet2Temp")
                        if temp_c2_water is not None:
                            sensor["current_temperature"] = temp_c2_water
                            _LOGGER.debug(
                                "Enriched zone_id 6 (C2_WATER) current_temperature: %s",
                                temp_c2_water,
                            )

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

                    # Build enhanced notification message
                    message_parts = [
                        f"Device: {sensor.get('device_name')} | Room: {sensor.get('room_name')}",
                    ]

                    # Add formatted alarm code
                    alarm_code_formatted = sensor.get("alarm_code_formatted")
                    if alarm_code_formatted and alarm_code_formatted != "0":
                        message_parts.append(
                            f"Code: {alarm_code_formatted} (raw: {alarm_code})"
                        )
                    else:
                        message_parts.append(f"Code: {alarm_code}")

                    # Add alarm origin if available
                    alarm_origin = sensor.get("alarm_origin")
                    if alarm_origin:
                        message_parts.append(f"Origin: {alarm_origin}")

                    # Add alarm message
                    alarm_msg = sensor.get("alarm_message")
                    if alarm_msg:
                        message_parts.append(f"Message: {alarm_msg}")

                    # Add unit type for context
                    unit_type = sensor.get("unit_type")
                    if unit_type and unit_type != "standard":
                        message_parts.append(f"Unit Type: {unit_type}")

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
