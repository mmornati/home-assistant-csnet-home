"""Tests for how the integration reads CSNet data.

Covers the zone index, the per-indoor-unit lookups, session renewal on reads,
the alarm translation language and the device status sensors.
"""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.csnet_home.api import TRANSLATIONS_RETRY_SECONDS, CSNetHomeAPI
from custom_components.csnet_home.const import LOGIN_PATH
from custom_components.csnet_home.coordinator import CSNetHomeCoordinator
from custom_components.csnet_home.helpers import extract_heating_status, extract_indoor_data, find_indoor_unit
from custom_components.csnet_home.sensor import CSNetHomeDeviceSensor


@pytest.fixture(autouse=True)
def mock_integration_frame():
    """Let the coordinator be created outside a config entry setup."""
    with patch("homeassistant.helpers.frame.report_usage"):
        yield


def two_unit_installation():
    """Return installation devices data with two indoor units on two devices."""
    return {
        "status": "success",
        "data": [
            {
                "id": 1709,
                "indoors": [
                    {
                        "id": 6996,
                        "heatingStatus": {"heatAirMinC1": 10, "heatAirMaxC1": 30, "tempDHW": 45, "dhwMax": 55, "systemConfigBits": 0},
                        "heatingSetting": {"fixTempHeatC1": 40},
                    }
                ],
            },
            {
                "id": 1710,
                "indoors": [
                    {
                        "id": 7001,
                        "heatingStatus": {"heatAirMinC1": 12, "heatAirMaxC1": 26, "tempDHW": 52, "dhwMax": 60, "systemConfigBits": 0x2000},
                        "heatingSetting": {"fixTempHeatC1": 35},
                    }
                ],
            },
        ],
    }


# --------------------------------------------------------------------------
# Indoor unit lookup
# --------------------------------------------------------------------------


def test_find_indoor_unit_by_id_across_devices():
    """A zone's unit is found by id, on any device."""
    data = two_unit_installation()

    assert find_indoor_unit(data, 6996)["id"] == 6996
    assert find_indoor_unit(data, 7001)["id"] == 7001
    # ids are compared as text: CSNet sends numbers, config and tests may hold strings
    assert find_indoor_unit(data, "7001")["id"] == 7001


@pytest.mark.parametrize("indoor_id", [None, 9999])
def test_find_indoor_unit_falls_back_to_first_unit(indoor_id):
    """Without an id, or with an unknown one, the first unit is used as before."""
    assert find_indoor_unit(two_unit_installation(), indoor_id)["id"] == 6996


@pytest.mark.parametrize("data", [None, {}, {"data": []}, {"data": [{"indoors": []}]}, {"data": "broken"}, []])
def test_find_indoor_unit_with_no_usable_data(data):
    """Missing or malformed data gives None instead of an exception."""
    assert find_indoor_unit(data, 6996) is None


def test_extract_indoor_data_per_unit():
    """Status and setting sections come from the requested unit."""
    data = two_unit_installation()

    assert extract_heating_status(data, 7001)["tempDHW"] == 52
    assert extract_heating_status(data)["tempDHW"] == 45
    assert extract_indoor_data(data, "heatingSetting", 7001) == {"fixTempHeatC1": 35}


def test_api_limits_and_capabilities_use_the_zones_unit(hass):
    """Limits, fan-coil support and fixed temperature are read per unit."""
    api = CSNetHomeAPI(hass, "user", "pass")
    data = two_unit_installation()

    assert api.get_temperature_limits(1, 1, data, 6996) == (10, 30)
    assert api.get_temperature_limits(1, 1, data, 7001) == (12, 26)
    # no id: first unit, as before this change
    assert api.get_temperature_limits(1, 1, data) == (10, 30)

    assert api.is_fan_coil_compatible(data, 6996) is False
    assert api.is_fan_coil_compatible(data, 7001) is True

    assert api.get_heating_setting_from_installation_devices(data, 7001)["fixTempHeatC1"] == 35


# --------------------------------------------------------------------------
# Coordinator: zone index and enrichment
# --------------------------------------------------------------------------


def _coordinator_with_api(hass, api):
    hass.data["csnet_home"] = {"test": {"api": api}}
    return CSNetHomeCoordinator(hass=hass, update_interval=60, entry_id="test")


def _api_returning(elements, installation_devices):
    api = MagicMock()
    api.logged_in = True
    api.async_get_elements_data = AsyncMock(return_value=elements)
    api.async_get_installation_devices_data = AsyncMock(return_value=installation_devices)
    api.async_get_installation_alarms = AsyncMock(return_value=None)
    api.load_translations = AsyncMock()
    api.get_heating_status_from_installation_devices = lambda data, indoor_id=None: extract_heating_status(data, indoor_id)
    return api


def _elements(*sensors):
    return {"common_data": {"name": "Home", "device_status": {}}, "sensors": list(sensors)}


async def test_zone_index_is_rebuilt_when_installation_devices_are_missing(hass):
    """Zones must not keep the previous poll's data when installationdevices fails."""
    first = {"device_id": 1, "room_id": 10, "zone_id": 1, "parent_id": 6996, "current_temperature": 19.0}
    api = _api_returning(_elements(first), two_unit_installation())
    coordinator = _coordinator_with_api(hass, api)
    await coordinator._async_update_data()
    assert coordinator.get_sensor_data_by_id(1, 10, 1)["current_temperature"] == 19.0

    second = {"device_id": 1, "room_id": 10, "zone_id": 1, "parent_id": 6996, "current_temperature": 21.5}
    api.async_get_elements_data = AsyncMock(return_value=_elements(second))
    api.async_get_installation_devices_data = AsyncMock(return_value=None)
    await coordinator._async_update_data()

    assert coordinator.get_sensor_data_by_id(1, 10, 1)["current_temperature"] == 21.5


async def test_zone_index_is_built_on_first_poll_without_heating_status(hass):
    """The first poll indexes the zones even if no unit reports heatingStatus."""
    zone = {"device_id": 1, "room_id": 10, "zone_id": 1, "parent_id": 6996, "current_temperature": 19.0}
    api = _api_returning(_elements(zone), {"data": [{"id": 1709, "indoors": [{"id": 6996}]}]})
    coordinator = _coordinator_with_api(hass, api)

    await coordinator._async_update_data()

    assert coordinator.get_sensor_data_by_id(1, 10, 1) is zone


async def test_each_zone_is_enriched_from_its_own_indoor_unit(hass):
    """Two hot water zones on two units each get their own tank temperature."""
    dhw_a = {"device_id": 1709, "room_id": 1, "zone_id": 3, "parent_id": 6996, "current_temperature": 0}
    dhw_b = {"device_id": 1710, "room_id": 2, "zone_id": 3, "parent_id": 7001, "current_temperature": 0}
    api = _api_returning(_elements(dhw_a, dhw_b), two_unit_installation())
    coordinator = _coordinator_with_api(hass, api)

    await coordinator._async_update_data()

    assert coordinator.get_sensor_data_by_id(1709, 1, 3)["current_temperature"] == 45
    assert coordinator.get_sensor_data_by_id(1710, 2, 3)["current_temperature"] == 52


# --------------------------------------------------------------------------
# Session renewal on reads
# --------------------------------------------------------------------------


class FakeResponse:
    """Minimal aiohttp response."""

    def __init__(self, *, status=200, path="/data/elements", payload=None, error=None):
        """Describe the answer: status, final URL path and JSON payload or error."""
        self.status = status
        self.url = SimpleNamespace(path=path)
        self._payload = payload
        self._error = error

    async def json(self):
        """Return the payload, or raise the configured error."""
        if self._error:
            raise self._error
        return self._payload

    async def __aenter__(self):
        """Enter the response context."""
        return self

    async def __aexit__(self, *exc):
        """Leave the response context."""
        return False


class FakeSession:
    """Session whose get() hands out the queued answers in order."""

    def __init__(self, answers):
        """Queue the answers."""
        self._answers = list(answers)
        self.get_calls = 0

    def get(self, *args, **kwargs):
        """Return the next queued answer, or raise it if it is an exception."""
        self.get_calls += 1
        answer = self._answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def _login_page():
    return FakeResponse(path=LOGIN_PATH)


def _api_with_session(hass, answers):
    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = FakeSession(answers)
    api.logged_in = True
    return api


def _successful_login(api):
    async def do_login():
        api.logged_in = True
        return True

    return AsyncMock(side_effect=do_login)


async def test_read_signs_in_again_and_retries_when_session_expired(hass):
    """An expired session costs one extra login, not a failed poll."""
    api = _api_with_session(hass, [_login_page(), FakeResponse(payload={"status": "success"})])
    api._async_do_login = _successful_login(api)

    data = await api._async_get_json("https://example.test/data/elements", {}, "elements")

    assert data == {"status": "success"}
    assert api._async_do_login.await_count == 1
    assert api.session.get_calls == 2
    assert api.logged_in is True


async def test_read_treats_a_non_json_answer_as_an_expired_session(hass):
    """HTML served with a 200 (no redirect seen) is handled the same way."""
    not_json = aiohttp.ContentTypeError(MagicMock(), ())
    api = _api_with_session(hass, [FakeResponse(error=not_json), FakeResponse(payload={"ok": 1})])
    api._async_do_login = _successful_login(api)

    assert await api._async_get_json("https://example.test/x", {}, "elements") == {"ok": 1}
    assert api._async_do_login.await_count == 1


async def test_read_gives_up_when_sign_in_fails(hass):
    """No second request when the login itself fails."""
    api = _api_with_session(hass, [_login_page()])
    api._async_do_login = AsyncMock(return_value=False)

    assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert api.session.get_calls == 1
    assert api.logged_in is False


async def test_read_stops_after_one_retry(hass):
    """A login page after a fresh login is reported, not retried forever."""
    api = _api_with_session(hass, [_login_page(), _login_page()])
    api._async_do_login = _successful_login(api)

    assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert api._async_do_login.await_count == 1
    assert api.session.get_calls == 2
    assert api.logged_in is False


@pytest.mark.parametrize("error", [asyncio.TimeoutError(), aiohttp.ClientConnectionError("down")])
async def test_read_timeout_keeps_the_session(hass, error):
    """A timeout or network error is not a reason to sign in again."""
    api = _api_with_session(hass, [error])
    api._async_do_login = AsyncMock(return_value=True)

    assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert api._async_do_login.await_count == 0
    assert api.session.get_calls == 1
    assert api.logged_in is True


async def test_parallel_reads_share_one_sign_in(hass):
    """Elements and installation devices expire together: one login serves both.

    The second request was sent before the session was renewed and its login
    page arrives after: it must reuse the new session instead of discarding it.
    """
    api = CSNetHomeAPI(hass, "user", "pass")
    api.logged_in = True
    renewed = asyncio.Event()
    answers = {
        "a": [_login_page(), FakeResponse(payload={"n": 1})],
        "b": [_login_page(), FakeResponse(payload={"n": 2})],
    }

    class YieldingLoginPage(FakeResponse):
        async def __aenter__(self):
            await asyncio.sleep(0)  # let the other request go out first
            return self

    class GatedLoginPage(FakeResponse):
        async def __aenter__(self):
            await renewed.wait()  # answer only once the session was renewed
            return self

    answers["a"][0] = YieldingLoginPage(path=LOGIN_PATH)
    answers["b"][0] = GatedLoginPage(path=LOGIN_PATH)
    api.session = SimpleNamespace(get=lambda url, **kwargs: answers[url[-1]].pop(0))

    async def do_login():
        api.logged_in = True
        renewed.set()
        return True

    api._async_do_login = AsyncMock(side_effect=do_login)

    results = await asyncio.gather(
        api._async_get_json("https://example.test/a", {}, "elements"),
        api._async_get_json("https://example.test/b", {}, "installation devices"),
    )

    assert [r["n"] for r in results] == [1, 2]
    assert api._async_do_login.await_count == 1
    assert api.logged_in is True


async def test_second_login_page_starts_the_login_back_off(hass):
    """A renewed session that still gets the login page must not sign in on every request."""
    api = _api_with_session(hass, [_login_page(), _login_page()])
    api._async_do_login = _successful_login(api)

    assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert api.login_backoff_remaining > 0

    # the next request is refused by the back-off without another sign-in
    assert await api.async_get_installation_devices_data() is None
    assert api._async_do_login.await_count == 1
    assert api.session.get_calls == 2


async def test_unreadable_json_keeps_the_session(hass):
    """A broken body is a bad answer, not an expired session."""
    broken = json.JSONDecodeError("Expecting value", "", 0)
    api = _api_with_session(hass, [FakeResponse(error=broken)])
    api._async_do_login = AsyncMock(return_value=True)

    assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert api._async_do_login.await_count == 0
    assert api.logged_in is True


async def test_http_error_status_keeps_the_session(hass):
    """A server error fails the request without a new sign-in."""
    api = _api_with_session(hass, [FakeResponse(status=500)])
    api._async_do_login = AsyncMock(return_value=True)

    assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert api._async_do_login.await_count == 0
    assert api.logged_in is True


@pytest.mark.parametrize("status", [401, 403])
async def test_unauthorized_status_renews_the_session(hass, status):
    """401 and 403 mean the session is no longer accepted."""
    api = _api_with_session(hass, [FakeResponse(status=status), FakeResponse(payload={"ok": 1})])
    api._async_do_login = _successful_login(api)

    assert await api._async_get_json("https://example.test/x", {}, "elements") == {"ok": 1}
    assert api._async_do_login.await_count == 1


async def test_getter_recovers_from_an_expired_session(hass):
    """The public read goes through the renewal: one poll, data returned."""
    payload = {"status": "success", "data": [{"indoors": []}]}
    api = _api_with_session(hass, [_login_page(), FakeResponse(payload=payload)])
    api._async_do_login = _successful_login(api)

    assert await api.async_get_installation_devices_data() == payload
    assert api._async_do_login.await_count == 1


async def test_getter_replaces_a_closed_session(hass):
    """A closed session is noticed before the request and replaced by a login."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = SimpleNamespace(closed=True)
    api.logged_in = True
    fresh = FakeSession([FakeResponse(payload={"status": "success"})])

    async def do_login():
        api.session = fresh
        api.logged_in = True
        return True

    api._async_do_login = AsyncMock(side_effect=do_login)

    assert await api.async_get_installation_devices_data() == {"status": "success"}
    assert api._async_do_login.await_count == 1
    assert fresh.get_calls == 1


async def test_getter_timeout_does_not_sign_in_again(hass):
    """A timeout fails the read and leaves the session for the next poll."""
    api = _api_with_session(hass, [asyncio.TimeoutError()])
    api._async_do_login = AsyncMock(return_value=True)

    assert await api.async_get_elements_data() is None
    assert api.logged_in is True
    assert api._async_do_login.await_count == 0


# --------------------------------------------------------------------------
# Alarm translations
# --------------------------------------------------------------------------


def _translation_session(files):
    """Session serving /translations/<file> from a dict; None means failure."""
    requested = []

    def get(url, **kwargs):
        name = url.rsplit("/", 1)[-1]
        requested.append(name)
        payload = files.get(name)
        if payload is None:
            raise aiohttp.ClientConnectionError("down")
        return FakeResponse(payload=payload)

    return SimpleNamespace(get=get), requested


@pytest.mark.parametrize(("language", "expected"), [("fr", "Défaut"), ("es", "Fallo"), ("en", "Fault"), (None, "Fallo")])
async def test_preferred_language_wins_for_alarm_text(hass, language, expected):
    """The chosen language is not overwritten by the fallbacks."""
    files = {
        "english.json": {"alarm_1": "Fault", "only_en": "English only"},
        "french.json": {"alarm_1": "Défaut"},
        "spanish.json": {"alarm_1": "Fallo"},
    }
    api = CSNetHomeAPI(hass, "user", "pass")
    api.session, _ = _translation_session(files)
    api.preferred_language = language

    await api.load_translations()

    assert api.translations["alarm_1"] == expected
    # keys missing from the preferred language still come from another one
    assert api.translations["only_en"] == "English only"


async def test_failed_translation_load_is_not_repeated_on_every_poll(hass):
    """After a failure the three requests wait before being sent again."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.session, requested = _translation_session({})

    with patch("custom_components.csnet_home.api.time.monotonic", return_value=1000.0):
        await api.load_translations()
        await api.load_translations()
    assert len(requested) == 3

    with patch("custom_components.csnet_home.api.time.monotonic", return_value=1000.0 + TRANSLATIONS_RETRY_SECONDS + 1):
        await api.load_translations()
    assert len(requested) == 6


async def test_loaded_translations_are_not_requested_again(hass):
    """A successful load is kept for the life of the session."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.session, requested = _translation_session({"english.json": {"a": "b"}, "french.json": {}, "spanish.json": {}})

    await api.load_translations()
    await api.load_translations()

    assert len(requested) == 3


# --------------------------------------------------------------------------
# Device status sensors
# --------------------------------------------------------------------------


def _device_sensor(common_data, key):
    sensor_data = {"device_id": 1709, "room_id": 394, "zone_id": 1, "device_name": "Hitachi PAC", "room_name": "Ground floor"}
    coordinator = SimpleNamespace(get_sensors_data=lambda: [sensor_data], get_common_data=lambda: common_data)
    return CSNetHomeDeviceSensor(coordinator, sensor_data, common_data, key)


def test_device_sensor_has_a_value_before_the_first_coordinator_update():
    """Created with the device's own status entry, the sensor reads it at once."""
    device_entry = {"name": "Hitachi PAC", "rssi": -57, "firmware": "H-0302", "lastComm": 1794553114000, "currentTimeMillis": 1794553133468}

    sensor = _device_sensor(device_entry, "wifi_signal")

    assert sensor.native_value == -57
    assert sensor.device_info["sw_version"] == "H-0302"


def test_device_sensor_reads_the_full_common_data_after_an_update():
    """After an update the sensor holds the whole common_data dict."""
    common_data = {"name": "Home", "device_status": {1709: {"name": "Hitachi PAC", "rssi": -61, "firmware": "H-0302"}}}

    sensor = _device_sensor(common_data, "wifi_signal")

    assert sensor.native_value == -61


def test_device_sensor_without_status_is_unknown():
    """No status for this device: no value, no exception."""
    sensor = _device_sensor({"name": "Home", "device_status": {}}, "wifi_signal")

    assert sensor.native_value is None
    assert sensor.device_info["sw_version"] is None
