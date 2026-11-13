"""Tests for what a poll costs."""

import logging
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.csnet_home.api import CSNetHomeAPI


class _Response:
    """Minimal aiohttp response carrying a JSON payload."""

    status = 200
    url = SimpleNamespace(path="/data/installationdevices")

    def __init__(self, payload):
        """Keep the payload to return."""
        self._payload = payload

    async def json(self):
        """Return the payload."""
        return self._payload

    async def __aenter__(self):
        """Enter the response context."""
        return self

    async def __aexit__(self, *exc):
        """Leave the response context."""
        return False


def _api(hass, payload):
    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = SimpleNamespace(closed=False, get=lambda *args, **kwargs: _Response(payload))
    api.logged_in = True
    return api


ELEMENTS = {"status": "success", "data": {"elements": [], "name": "Home", "device_status": []}}
DEVICES = {"status": "success", "data": [{"indoors": [{"heatingStatus": {"ouHz": 30}}]}]}
ALARMS = {"status": "success", "data": []}


@pytest.mark.parametrize(
    ("method", "payload", "copies_at_debug"),
    [
        ("async_get_elements_data", ELEMENTS, 3),
        ("async_get_installation_devices_data", DEVICES, 1),
        ("async_get_installation_alarms", ALARMS, 1),
    ],
)
@pytest.mark.parametrize("debug", [False, True])
async def test_payload_is_only_copied_for_the_debug_log(hass, caplog, method, payload, copies_at_debug, debug):
    """Redacting deep-copies the payload: skip it when nobody reads the debug log."""
    api = _api(hass, payload)
    api.installation_id = 1
    caplog.set_level(logging.DEBUG if debug else logging.INFO, logger="custom_components.csnet_home.api")

    with patch("custom_components.csnet_home.api.redact_data", wraps=lambda data: data) as redact:
        assert await getattr(api, method)() is not None

    assert redact.call_count == (copies_at_debug if debug else 0)
