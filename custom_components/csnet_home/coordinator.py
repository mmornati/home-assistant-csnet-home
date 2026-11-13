"""Coordinator Class to centralise all data fetching from CSNet Home."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MIN_SCAN_INTERVAL

if TYPE_CHECKING:
    from .api import CSNetHomeAPI

_LOGGER = logging.getLogger(__name__)

# The alarm list of an installation rarely changes: ask for it less often than the readings
ALARM_POLL_SECONDS = 300
ALARM_STORAGE_VERSION = 1
ZONE_ALARM_NOTIFICATION_PREFIX = "csnet_home_alarm_"
INSTALLATION_ALARM_NOTIFICATION_PREFIX = "csnet_home_inst_alarm_"


def installation_alarm_list(answer) -> list | None:
    """Return the alarms of an answer from CSNet, or None when it carries no alarm list."""
    if not isinstance(answer, dict):
        return None
    data = answer.get("data")
    alarms = answer.get("alarms")
    if isinstance(data, list) and data:
        return data
    if isinstance(alarms, list):
        return alarms
    return data if isinstance(data, list) else None


def alarm_storage_key(entry_id: str) -> str:
    """Return the storage key of the alarms an entry has already notified."""
    return f"{DOMAIN}.notified_alarms.{entry_id}"


@dataclass
class CSNetHomeData:
    """What a loaded config entry keeps in ``entry.runtime_data``."""

    api: CSNetHomeAPI
    coordinator: CSNetHomeCoordinator


CSNetHomeConfigEntry = ConfigEntry[CSNetHomeData]


class CSNetHomeCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch all sensor data from the cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        update_interval: int,
        entry_id: str,
        enable_alarm_notifications: bool = True,
        filtered_alarm_codes: str = "-1",
        *,
        api: CSNetHomeAPI | None = None,
        config_entry: ConfigEntry | None = None,
    ):
        """Initialize the coordinator for one config entry and the API client it reads from."""
        _LOGGER.debug("Configuring CSNetHome Coordinator")
        self.hass = hass
        self.entry_id = entry_id
        self.api = api
        if update_interval < MIN_SCAN_INTERVAL:
            _LOGGER.warning(
                "Scan interval of %s s is below the %s s minimum, using %s s",
                update_interval,
                MIN_SCAN_INTERVAL,
                MIN_SCAN_INTERVAL,
            )
            update_interval = MIN_SCAN_INTERVAL
        self.update_interval = timedelta(seconds=update_interval)
        self._device_data = {"sensors": [], "common_data": {}}
        self._sensors_by_id = {}
        self._last_alarm_codes: dict[str, int] = {}
        self._notified_installation_alarm_ids: set[int] = set()
        # Last alarm list CSNet answered with, when it was asked, and whether it still has to be processed
        self._installation_alarms_data = None
        self._installation_alarms_fetched_at: float | None = None
        self._installation_alarms_pending = False
        # Alarms that must not be notified again: the user dismissed the
        # notification, or they appeared while notifications were off. Stored,
        # because Home Assistant drops all notifications on a restart and the
        # ones still wanted are created again then.
        self._dismissed_installation_alarm_ids: set = set()
        self._dismissed_zone_alarm_codes: dict[str, int] = {}
        self._alarm_store = Store(hass, ALARM_STORAGE_VERSION, alarm_storage_key(entry_id))
        self._alarm_state_loaded = False
        self._saved_alarm_state: dict | None = None
        self._enable_alarm_notifications = enable_alarm_notifications
        self._filtered_alarm_codes = self._parse_filtered_alarm_codes(filtered_alarm_codes)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=self.update_interval,
            config_entry=config_entry,
        )

    def _parse_filtered_alarm_codes(self, codes_string: str) -> set[int]:
        """Parse comma-separated alarm codes string into a set of integers."""
        if not codes_string:
            return set()
        try:
            return {int(code.strip()) for code in codes_string.split(",") if code.strip()}
        except ValueError:
            _LOGGER.warning("Invalid alarm codes format: %s, defaulting to empty set", codes_string)
            return set()

    async def _async_update_data(self):
        """Fetch data for all sensors."""

        _LOGGER.debug("Fetching all CSNet Home sensor data from API.")

        cloud_api = self.api
        if not cloud_api:
            raise UpdateFailed("No CSNet API instance found")

        # Ensure login is valid before launching parallel tasks to avoid race conditions
        # with multiple concurrent login attempts.
        if not cloud_api.logged_in and not await cloud_api.async_login():
            self._raise_login_failure(cloud_api)

        async def fetch_elements_chain():
            # ensure translations are loaded before elements to enrich alarm messages
            await cloud_api.load_translations()
            # Fetch elements data and alarms
            elements = await cloud_api.async_get_elements_data()
            alarms = await self._async_get_installation_alarms(cloud_api)
            return elements, alarms

        # Run independent fetch operations in parallel
        # 1. Elements chain (translations -> elements -> alarms)
        # 2. Installation devices data (independent)
        results = await asyncio.gather(
            fetch_elements_chain(),
            cloud_api.async_get_installation_devices_data(),
        )

        elements_data, installation_alarms_data = results[0]
        installation_devices_data = results[1]

        if elements_data is None:
            # Keep the last known data and mark entities unavailable instead of
            # showing stale values as if they were current
            if not cloud_api.logged_in:
                self._raise_login_failure(cloud_api)
            raise UpdateFailed("CSNet Manager returned no data")

        # Update internal data
        self._update_internal_data(elements_data, installation_devices_data, installation_alarms_data)

        # Enrich sensor data
        self._enrich_sensor_data(cloud_api, installation_devices_data)

        await self._async_load_alarm_state()

        # Handle alarm notifications
        await self._handle_alarm_notifications()

        # Handle installation-level alarms
        await self._handle_installation_alarms(cloud_api)

        await self._async_save_alarm_state()

        return self._device_data

    async def _async_get_installation_alarms(self, cloud_api):
        """Return the installation alarms, asking CSNet at most every ALARM_POLL_SECONDS.

        Between two requests, and when a request fails or answers without an
        alarm list, the last answer is kept: that must not look like "no alarms".
        """
        now = time.monotonic()
        fetched_at = self._installation_alarms_fetched_at
        if fetched_at is not None and now - fetched_at < ALARM_POLL_SECONDS:
            return self._installation_alarms_data

        data = await cloud_api.async_get_installation_alarms()
        if installation_alarm_list(data) is None:
            # asked again on the next poll
            return self._installation_alarms_data

        self._installation_alarms_data = data
        self._installation_alarms_fetched_at = now
        # stays set until the alarms were processed, also when this poll fails later on
        self._installation_alarms_pending = True
        return data

    def async_invalidate_installation_alarms(self) -> None:
        """Ask CSNet for the alarm list again on the next poll (after an alarm was deleted)."""
        self._installation_alarms_fetched_at = None

    def _alarm_state(self) -> dict:
        """Return the alarms that must not be notified again, in the form they are stored."""
        return {
            "dismissed_installation_alarm_ids": sorted(self._dismissed_installation_alarm_ids, key=str),
            "dismissed_zone_alarm_codes": dict(self._dismissed_zone_alarm_codes),
        }

    async def _async_load_alarm_state(self) -> None:
        """Load once the alarms that were dismissed before the last restart."""
        if self._alarm_state_loaded:
            return
        self._alarm_state_loaded = True
        try:
            stored = await self._alarm_store.async_load()
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not load the notified alarms: %s", exc)
            return
        if not isinstance(stored, dict):
            return
        ids = stored.get("dismissed_installation_alarm_ids")
        if isinstance(ids, list):
            self._dismissed_installation_alarm_ids.update(i for i in ids if isinstance(i, (int, str)) and not isinstance(i, bool))
        codes = stored.get("dismissed_zone_alarm_codes")
        if isinstance(codes, dict):
            for key, code in codes.items():
                if isinstance(code, int) and not isinstance(code, bool):
                    self._dismissed_zone_alarm_codes.setdefault(key, code)
        self._saved_alarm_state = self._alarm_state()

    async def _async_save_alarm_state(self) -> None:
        """Store the alarms that must not be notified again, when they changed."""
        state = self._alarm_state()
        if state == self._saved_alarm_state:
            return
        try:
            await self._alarm_store.async_save(state)
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug("Could not save the notified alarms: %s", exc)
            return
        self._saved_alarm_state = state

    @callback
    def async_track_dismissed_notifications(self) -> CALLBACK_TYPE:
        """Follow which alarm notifications the user dismisses; returns the function that stops it."""
        return persistent_notification.async_register_callback(self.hass, self._async_notifications_updated)

    @callback
    def _async_notifications_updated(self, update_type, notifications) -> None:
        """Remember the alarms whose notification was dismissed."""
        if update_type != persistent_notification.UpdateType.REMOVED:
            return
        changed = False
        notified_by_text = {str(alarm_id): alarm_id for alarm_id in self._notified_installation_alarm_ids}
        for notification_id in notifications:
            if notification_id.startswith(INSTALLATION_ALARM_NOTIFICATION_PREFIX):
                alarm_id = notified_by_text.get(notification_id[len(INSTALLATION_ALARM_NOTIFICATION_PREFIX) :])
                if alarm_id is not None and alarm_id not in self._dismissed_installation_alarm_ids:
                    self._dismissed_installation_alarm_ids.add(alarm_id)
                    changed = True
            elif notification_id.startswith(ZONE_ALARM_NOTIFICATION_PREFIX):
                key = notification_id[len(ZONE_ALARM_NOTIFICATION_PREFIX) :]
                code = self._last_alarm_codes.get(key)
                if code is not None and self._dismissed_zone_alarm_codes.get(key) != code:
                    self._dismissed_zone_alarm_codes[key] = code
                    changed = True
        if changed:
            self.hass.async_create_task(self._async_save_alarm_state())

    @staticmethod
    def _raise_login_failure(cloud_api):
        """Raise the exception matching why the CSNet login failed."""
        if getattr(cloud_api, "auth_failed", False) is True:
            raise ConfigEntryAuthFailed("CSNet Manager rejected the credentials")
        raise UpdateFailed("Could not log in to CSNet Manager")

    async def _fetch_data(self, cloud_api):
        """Fetch all data from the API."""
        try:
            # ensure translations are loaded before elements to enrich alarm messages
            await cloud_api.load_translations()

            # Fetch elements data, installation devices data, and alarms
            elements_data = await cloud_api.async_get_elements_data()
            installation_devices_data = await cloud_api.async_get_installation_devices_data()
            installation_alarms_data = await cloud_api.async_get_installation_alarms()

            return elements_data, installation_devices_data, installation_alarms_data
        except Exception as exc:
            _LOGGER.error("Error fetching data from API: %s", exc)
            return None, None, None

    def _update_internal_data(self, elements_data, installation_devices_data, installation_alarms_data):
        """Update internal data structures with fetched data."""
        if elements_data:
            self._device_data = elements_data
        else:
            self._device_data = {"sensors": [], "common_data": {}}

        # Update fast lookup dictionary (enrichment changes these same dicts in place)
        self._sensors_by_id = {(s.get("device_id"), s.get("room_id"), s.get("zone_id")): s for s in self._device_data.get("sensors", [])}

        # Add installation devices data to common_data
        if installation_devices_data and self._device_data.get("common_data"):
            self._device_data["common_data"]["installation_devices"] = installation_devices_data

        # Add installation alarms data to common_data
        if installation_alarms_data is not None and self._device_data.get("common_data"):
            self._device_data["common_data"]["installation_alarms"] = installation_alarms_data

    def _enrich_sensor_data(self, cloud_api, installation_devices_data):
        """Enrich sensor data with correct temperatures from installation devices data."""
        # This fixes issue #137: water heater (zone_id 3) and water circuits (zone_id 5, 6)
        # need temperatures from heatingStatus, not from elements API
        if not (installation_devices_data and self._device_data.get("sensors")):
            return

        try:
            for sensor in self._device_data["sensors"]:
                # Each zone reads the heatingStatus of its own indoor unit
                heating_status = cloud_api.get_heating_status_from_installation_devices(installation_devices_data, sensor.get("parent_id"))
                if not heating_status:
                    continue

                zone_id = sensor.get("zone_id")
                # For zone_id 3 (DHW/water heater), use tempDHW from heatingStatus
                if zone_id == 3:
                    temp_dhw = heating_status.get("tempDHW")
                    if self._is_valid_temperature(temp_dhw):
                        sensor["current_temperature"] = temp_dhw
                        _LOGGER.debug(
                            "Enriched zone_id 3 (DHW) current_temperature: %s",
                            temp_dhw,
                        )
                # For zone_id 4 (swimming pool), use tempSWP from heatingStatus
                elif zone_id == 4:
                    temp_swp = heating_status.get("tempSWP")
                    if self._is_valid_temperature(temp_swp):
                        sensor["current_temperature"] = temp_swp
                        _LOGGER.debug("Enriched zone_id 4 (SWP) current_temperature: %s", temp_swp)
                # For zone_id 5 (C1_WATER), use waterOutletHPTemp from heatingStatus
                # BUT: elementType 5 can also represent HEAT elements (parentName "Heat")
                # Only enrich if it's actually a water circuit, not a heat circuit
                elif zone_id == 5:
                    room_name = sensor.get("room_name", "").lower()
                    # Skip enrichment for HEAT elements (parentName "Heat")
                    # Only enrich actual water circuits
                    if "heat" not in room_name:
                        temp_c1_water = heating_status.get("waterOutletHPTemp")
                        if self._is_valid_temperature(temp_c1_water):
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
                    if self._is_valid_temperature(temp_c2_water):
                        sensor["current_temperature"] = temp_c2_water
                        _LOGGER.debug(
                            "Enriched zone_id 6 (C2_WATER) current_temperature: %s",
                            temp_c2_water,
                        )
        except Exception as exc:
            _LOGGER.error("Error enriching sensor data: %s", exc)

    async def _handle_alarm_notifications(self):
        """Raise notification if new alarm codes appear.

        The codes are followed with notifications off too: a stored code that
        was never cleared would hide the same alarm when it comes back.
        """
        try:
            for sensor in self._device_data.get("sensors", []):
                key = f"{sensor.get('device_id')}-{sensor.get('room_id')}-{sensor.get('zone_id')}"
                alarm_code = sensor.get("alarm_code")
                if alarm_code is None or alarm_code == 0:
                    # clear last stored to allow future notifications
                    self._last_alarm_codes.pop(key, None)
                    self._dismissed_zone_alarm_codes.pop(key, None)
                    continue
                if self._dismissed_zone_alarm_codes.get(key, alarm_code) != alarm_code:
                    # the dismissed alarm was replaced by another one
                    self._dismissed_zone_alarm_codes.pop(key, None)

                if alarm_code in self._filtered_alarm_codes:
                    _LOGGER.debug("Skipping notification for filtered alarm code: %s", alarm_code)
                    # Still track the alarm code to avoid repeated processing on next poll
                    self._last_alarm_codes[key] = alarm_code
                    continue

                prev_code = self._last_alarm_codes.get(key)
                if prev_code != alarm_code:
                    # store and notify
                    self._last_alarm_codes[key] = alarm_code
                    if not self._enable_alarm_notifications:
                        # seen with notifications off: not notified when they are turned on
                        self._dismissed_zone_alarm_codes[key] = alarm_code
                        continue
                    if self._dismissed_zone_alarm_codes.get(key) == alarm_code:
                        continue
                    title = "Hitachi Device Alarm"

                    # Build enhanced notification message
                    message_parts = [
                        f"Device: {sensor.get('device_name')} | Room: {sensor.get('room_name')}",
                    ]

                    # Add formatted alarm code
                    alarm_code_formatted = sensor.get("alarm_code_formatted")
                    if alarm_code_formatted and alarm_code_formatted != "0":
                        message_parts.append(f"Code: {alarm_code_formatted} (raw: {alarm_code})")
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
                            "notification_id": f"{ZONE_ALARM_NOTIFICATION_PREFIX}{key}",
                        },
                        blocking=False,
                    )
        except Exception as exc:  # pragma: no cover - do not fail updates on notify
            _LOGGER.debug("Alarm notification handling error: %s", exc)

    async def _handle_installation_alarms(self, api):
        """Notify each active installation alarm once.

        Only runs on a new alarm list from CSNet: forgetting alarms because a
        request failed would notify every one of them again on the next poll.
        """
        if not self._installation_alarms_pending:
            return
        self._installation_alarms_pending = False
        alarms = installation_alarm_list(self._installation_alarms_data) or []

        current_active_ids = set()

        for alarm in alarms:
            if not isinstance(alarm, dict):
                continue
            # Check if active
            # User provided: "recoveredAtString": "1980-01-01 00:00:00" means active
            is_active = alarm.get("recoveredAtString") == "1980-01-01 00:00:00"
            if not is_active:
                continue

            alarm_id = alarm.get("id")
            if not isinstance(alarm_id, (int, str)) or isinstance(alarm_id, bool):
                continue

            code = alarm.get("code")

            if code in self._filtered_alarm_codes:
                _LOGGER.debug("Skipping notification for filtered installation alarm code: %s", code)
                continue

            current_active_ids.add(alarm_id)

            if alarm_id in self._notified_installation_alarm_ids:
                continue

            # New active alarm found. Seen with notifications off, it is not
            # notified when they are turned on later.
            self._notified_installation_alarm_ids.add(alarm_id)
            if not self._enable_alarm_notifications:
                self._dismissed_installation_alarm_ids.add(alarm_id)
                continue
            if alarm_id in self._dismissed_installation_alarm_ids:
                continue

            unit_id = alarm.get("unitId")

            description = api.translate_alarm(code) if code != -1 else "System/Communication Error"

            message = f"Installation Alarm ID: {alarm_id}\nCode: {code}\nDescription: {description}\nUnit ID: {unit_id}"

            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "CSNet Home Installation Alarm",
                    "message": message,
                    "notification_id": f"{INSTALLATION_ALARM_NOTIFICATION_PREFIX}{alarm_id}",
                },
                blocking=False,
            )

        # Clean up notified IDs for alarms that are no longer active
        # We only keep IDs that are currently active
        self._notified_installation_alarm_ids = self._notified_installation_alarm_ids.intersection(current_active_ids)
        self._dismissed_installation_alarm_ids = self._dismissed_installation_alarm_ids.intersection(current_active_ids)

    def get_sensors_data(self):
        """Return the list of sensor data."""

        return self._device_data["sensors"]

    def get_sensor_data_by_id(self, device_id, room_id, zone_id):
        """Return sensor data by unique ID combination (O(1) lookup)."""
        return self._sensors_by_id.get((device_id, room_id, zone_id))

    def get_common_data(self):
        """Return common data shared between all sensors."""

        return self._device_data["common_data"]

    def get_installation_devices_data(self):
        """Return installation devices data."""

        return self._device_data.get("common_data", {}).get("installation_devices", {})

    def get_installation_alarms_data(self):
        """Return installation alarms data."""

        return self._device_data.get("common_data", {}).get("installation_alarms", {})

    def _is_valid_temperature(self, value):
        """Validate if temperature value is reasonable."""
        if value is None:
            return False
        if isinstance(value, (int, float)) and value < -20:
            return False
        return True
