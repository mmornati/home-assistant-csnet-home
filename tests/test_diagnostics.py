"""Test the diagnostics download."""

from datetime import timedelta
from unittest.mock import MagicMock

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import DOMAIN
from custom_components.csnet_home.coordinator import CSNetHomeData
from custom_components.csnet_home.diagnostics import REDACTED, async_get_config_entry_diagnostics, redact

SECRETS = [
    "someone@example.com",
    "s3cret-pass",
    "48.8566",
    "2.3522",
    "My House",
    "SERIAL-123",
    "HASH-abc",
    "657227",
    "AA:BB:CC:DD:EE:FF",
    "owner@example.com",
    "4529",
]


def _coordinator():
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.update_interval = timedelta(seconds=60)
    coordinator.get_sensors_data.return_value = [
        {"device_id": 1709, "room_id": 394, "zone_id": 1, "room_name": "Ground floor", "current_temperature": 19.5},
    ]
    coordinator.get_common_data.return_value = {
        "name": "My House",
        "latitude": "48.8566",
        "longitude": "2.3522",
        "weather_temperature": 2,
        "device_status": {1709: {"name": "Hitachi PAC", "ownerId": 657227, "hash": "HASH-abc", "rssi": -57}},
        "installation_devices": {
            "data": [
                {
                    "name": "Hitachi PAC",
                    "installationId": 4529,
                    "key": "HASH-abc",
                    # keys the integration has never seen still have to be caught
                    "wifiMacAddress": "AA:BB:CC:DD:EE:FF",
                    "ownerEmail": "owner@example.com",
                    "indoors": [
                        {
                            "id": 6996,
                            "iduSerial": "SERIAL-123",
                            "oduSerial": "SERIAL-123",
                            "heatingStatus": {"waterInletTemp": 40, "ouCurrent": 3},
                        }
                    ],
                }
            ]
        },
        "installation_alarms": {
            "status": "success",
            "data": [{"id": 544153, "installationId": 4529, "unitId": 6996, "code": 41, "createdAtString": "2026-06-25 04:12:47"}],
        },
    }
    return coordinator


async def test_diagnostics_redacts_account_and_hardware_identifiers(hass):
    """Nothing that identifies the account, place or hardware is in the download."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "someone@example.com", CONF_PASSWORD: "s3cret-pass"})
    entry.add_to_hass(hass)
    entry.runtime_data = CSNetHomeData(api=MagicMock(), coordinator=_coordinator())

    result = await async_get_config_entry_diagnostics(hass, entry)

    dumped = repr(result)
    for secret in SECRETS:
        assert secret not in dumped

    assert result["config_entry"]["data"][CONF_USERNAME] == REDACTED
    assert result["config_entry"]["data"][CONF_PASSWORD] == REDACTED
    assert result["common_data"]["name"] == REDACTED


async def test_diagnostics_keeps_the_values_needed_to_debug(hass):
    """Readings, ids used for lookups and zone names stay readable."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "u", CONF_PASSWORD: "p"})
    entry.add_to_hass(hass)
    entry.runtime_data = CSNetHomeData(api=MagicMock(), coordinator=_coordinator())

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["coordinator"] == {"last_update_success": True, "update_interval_seconds": 60.0}
    assert result["sensors"][0]["room_name"] == "Ground floor"
    assert result["sensors"][0]["current_temperature"] == 19.5
    assert result["common_data"]["weather_temperature"] == 2
    indoor = result["common_data"]["installation_devices"]["data"][0]["indoors"][0]
    assert indoor["id"] == 6996
    assert indoor["heatingStatus"] == {"waterInletTemp": 40, "ouCurrent": 3}
    # device names are kept, only the installation name is hidden
    assert result["common_data"]["installation_devices"]["data"][0]["name"] == "Hitachi PAC"
    alarm = result["common_data"]["installation_alarms"]["data"][0]
    assert alarm == {"id": 544153, "installationId": REDACTED, "unitId": 6996, "code": 41, "createdAtString": "2026-06-25 04:12:47"}


async def test_diagnostics_does_not_change_the_coordinator_data(hass):
    """Redaction works on a copy: entities keep reading the real values."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "u", CONF_PASSWORD: "p"})
    entry.add_to_hass(hass)
    coordinator = _coordinator()
    entry.runtime_data = CSNetHomeData(api=MagicMock(), coordinator=coordinator)

    await async_get_config_entry_diagnostics(hass, entry)

    common_data = coordinator.get_common_data.return_value
    assert common_data["name"] == "My House"
    assert common_data["latitude"] == "48.8566"
    assert common_data["installation_devices"]["data"][0]["indoors"][0]["iduSerial"] == "SERIAL-123"


def test_redact_matches_keys_case_insensitively_and_keeps_empty_values():
    """Unknown spellings are caught; empty values stay visible as empty."""
    data = {"Latitude": 1.5, "OWNERID": 7, "oduSerial": None, "hash": "", "iuAddress": 3, "rssi": -57, "nested": [{"readIduSerial": "X1"}]}

    assert redact(data) == {
        "Latitude": REDACTED,
        "OWNERID": REDACTED,
        "oduSerial": None,
        "hash": "",
        "iuAddress": 3,
        "rssi": -57,
        "nested": [{"readIduSerial": REDACTED}],
    }


async def test_diagnostics_with_no_data_yet(hass):
    """A coordinator that has not polled yet does not break the download."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "u", CONF_PASSWORD: "p"})
    entry.add_to_hass(hass)
    coordinator = MagicMock()
    coordinator.last_update_success = False
    coordinator.update_interval = None
    coordinator.get_sensors_data.return_value = []
    coordinator.get_common_data.return_value = {}
    entry.runtime_data = CSNetHomeData(api=MagicMock(), coordinator=coordinator)

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["sensors"] == []
    assert result["common_data"] == {}
    assert result["coordinator"]["update_interval_seconds"] is None


def test_installations_summary_carries_no_values():
    """Ids and field names only: an installation holds names, addresses and people."""
    from custom_components.csnet_home.diagnostics import _installations_summary

    installations = [
        {"id": 4529, "name": "My House", "address": "1 Secret Street", "privileges": [{"username": "someone@example.com"}]},
        {"id": 5000, "name": "Holiday home", "city": "Somewhere"},
        "junk",
    ]
    summary = _installations_summary(installations)
    assert summary == {
        "count": 3,
        "entries": [{"id": 4529, "fields": ["address", "id", "name", "privileges"]}, {"id": 5000, "fields": ["city", "id", "name"]}],
    }
    for secret in ("My House", "Secret Street", "someone@example.com", "Holiday home", "Somewhere"):
        assert secret not in repr(summary)
    assert _installations_summary(None) is None
