"""Diagnostics download for the CSNet Home integration.

The download holds the config entry and the data the coordinator last
received from CSNet Manager, with everything that identifies the account, the
installation or the hardware redacted. It is what to attach to an issue.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import TO_REDACT
from .const import DOMAIN

REDACTED = "**REDACTED**"

# Keys redacted wherever they appear, on top of the ones already hidden from
# the debug log. Compared case-insensitively.
_EXACT_KEYS = {
    key.lower()
    for key in TO_REDACT
    | {
        # account and installation
        "user",
        "address",
        "city",
        "zipCode",
        "postalCode",
        "country",
        "phone",
        # hardware and network identifiers
        "hash",
        "key",
        "mac",
        "ip",
        "ssid",
        "buildId",
        "desiredBuildId",
    }
}

# installation_devices and installation_alarms are passed through from CSNet
# Manager as received, so a key this integration has never seen can show up.
# Anything whose name contains one of these fragments is redacted too.
_KEY_FRAGMENTS = ("serial", "mail", "owner", "username", "displayablename", "password", "token", "csrf", "macaddr", "ipaddr", "ssid", "phone")

# The installation name is stored under the generic key "name", which is also
# used for zone and device names that are needed to read the data.
_INSTALLATION_NAME_KEY = "name"


def _is_sensitive(key: Any) -> bool:
    """Return True when the value stored under this key must not be shared."""
    lowered = str(key).lower()
    return lowered in _EXACT_KEYS or any(fragment in lowered for fragment in _KEY_FRAGMENTS)


def redact(data: Any) -> Any:
    """Return a copy of data with sensitive values replaced. Empty values are kept as they are."""
    if isinstance(data, dict):
        return {key: (REDACTED if _is_sensitive(key) and value not in (None, "", 0) else redact(value)) for key, value in data.items()}
    if isinstance(data, (list, tuple)):
        return [redact(item) for item in data]
    return data


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    common_data = dict(coordinator.get_common_data() or {})
    if common_data.get(_INSTALLATION_NAME_KEY):
        common_data[_INSTALLATION_NAME_KEY] = REDACTED

    return {
        "config_entry": redact(entry.as_dict()),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": coordinator.update_interval.total_seconds() if coordinator.update_interval else None,
        },
        "sensors": redact(coordinator.get_sensors_data() or []),
        "common_data": redact(common_data),
    }
