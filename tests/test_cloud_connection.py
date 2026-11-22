"""The link to CSNet Manager: what went wrong with a request, and the connection sensor."""

import asyncio
import logging
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.csnet_home.api import (
    PROBLEM_CONNECTION_LOST,
    PROBLEM_DNS,
    PROBLEM_ERROR_ANSWER,
    PROBLEM_HTTP_ERROR,
    PROBLEM_LOGIN_FAILED,
    PROBLEM_LOGIN_REJECTED,
    PROBLEM_LOGIN_WAITING,
    PROBLEM_NO_CONNECTION,
    PROBLEM_NO_DATA,
    PROBLEM_TIMEOUT,
    CSNetHomeAPI,
    describe_error,
    problem_of,
)
from custom_components.csnet_home.binary_sensor import CSNetHomeCloudConnectionSensor
from custom_components.csnet_home.cloud_connection import CloudConnection
from custom_components.csnet_home.coordinator import CSNetHomeCoordinator

from .test_data_access import FakeResponse, _api_with_session

NOON = datetime(2026, 11, 22, 12, 0)


def _connector_error(cls):
    """Return an aiohttp connection error as aiohttp raises it."""
    return cls(MagicMock(), OSError(8, "nodename nor servname provided"))


@pytest.mark.parametrize(
    ("error", "problem"),
    [
        (asyncio.TimeoutError(), PROBLEM_TIMEOUT),
        (_connector_error(aiohttp.ClientConnectorDNSError), PROBLEM_DNS),
        (_connector_error(aiohttp.ClientConnectorError), PROBLEM_NO_CONNECTION),
        (aiohttp.ServerDisconnectedError(), PROBLEM_CONNECTION_LOST),
    ],
)
def test_problem_of_tells_the_kinds_of_failure_apart(error, problem):
    """No name lookup and no connection point to this side; a timeout can be either."""
    assert problem_of(error) == problem


def test_a_timeout_is_described_with_its_name():
    """A timeout has no message: the log used to end with an empty colon."""
    assert describe_error(asyncio.TimeoutError()) == "TimeoutError"
    assert describe_error(aiohttp.ClientError("boom")) == "ClientError: boom"


async def test_a_timeout_says_so_and_is_noted(hass, caplog):
    """The log names the timeout; the request keeps the problem for the sensor."""
    api = _api_with_session(hass, [asyncio.TimeoutError()])
    with caplog.at_level(logging.WARNING):
        assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert "No answer from CSNet Manager to the elements request within 10 s (timeout)" in caplog.text
    assert api.problems == {"elements": (PROBLEM_TIMEOUT, "TimeoutError")}


async def test_a_connection_error_is_noted_with_its_kind(hass, caplog):
    """A failed name lookup is logged with its text and noted as such."""
    api = _api_with_session(hass, [_connector_error(aiohttp.ClientConnectorDNSError)])
    assert await api._async_get_json("https://example.test/x", {}, "installation devices") is None
    assert "Could not reach CSNet Manager for the installation devices request: ClientConnectorDNSError" in caplog.text
    assert api.problems["installation devices"][0] == PROBLEM_DNS


async def test_an_error_status_is_noted(hass):
    """An error status from CSNet points to CSNet."""
    api = _api_with_session(hass, [FakeResponse(status=503)])
    assert await api._async_get_json("https://example.test/x", {}, "elements") is None
    assert api.problems == {"elements": (PROBLEM_HTTP_ERROR, "HTTP 503")}


async def test_a_good_answer_keeps_its_response_time(hass):
    """The time the last answer took, for the sensor."""
    api = _api_with_session(hass, [FakeResponse(payload={"status": "success"})])
    assert await api._async_get_json("https://example.test/x", {}, "elements") == {"status": "success"}
    assert api.problems == {}
    assert 0 <= api.response_seconds["elements"] < 1


async def test_elements_without_success_is_an_error_answer(hass, caplog):
    """An answer without the readings is said as such, with the status it gave."""
    api = _api_with_session(hass, [FakeResponse(payload={"status": "error"})])
    assert await api.async_get_elements_data() is None
    assert "answered the elements request without success (status: error)" in caplog.text
    assert api.problems == {"elements": (PROBLEM_ERROR_ANSWER, "status: error")}


async def test_no_answer_is_not_reported_as_an_error_answer(hass, caplog):
    """Without an answer, no claim that CSNet answered without success."""
    api = _api_with_session(hass, [asyncio.TimeoutError(), asyncio.TimeoutError()])
    assert await api.async_get_elements_data() is None
    assert await api.async_get_installation_devices_data() is None
    assert "without success" not in caplog.text
    assert "status not 'success'" not in caplog.text
    assert "Error in installation devices API response" not in caplog.text


async def test_login_problems_are_noted(hass):
    """A login that cannot reach CSNet, one that is refused, and the wait after it."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api._async_do_login = AsyncMock(side_effect=asyncio.TimeoutError())
    assert await api.async_login() is False
    assert api.problems["login"] == (PROBLEM_TIMEOUT, "TimeoutError")

    assert await api.async_login() is False
    assert api.problems["login"][0] == PROBLEM_LOGIN_WAITING

    api._next_login_attempt = 0.0
    api._async_do_login = AsyncMock(return_value=False)
    api._last_login_rejected = True
    assert await api.async_login() is False
    assert api.problems["login"] == (PROBLEM_LOGIN_REJECTED, "")

    api._next_login_attempt = 0.0
    api._last_login_rejected = False
    assert await api.async_login() is False
    assert api.problems["login"] == (PROBLEM_LOGIN_FAILED, "")


def test_connection_record_counts_failures_and_clears_them():
    """In a row and today; a good poll clears the problem but keeps today's count."""
    connection = CloudConnection()
    assert connection.connected is None

    connection.record_failure(NOON, {"installation devices": (PROBLEM_TIMEOUT, "TimeoutError"), "elements": (PROBLEM_DNS, "x")})
    connection.record_failure(NOON + timedelta(minutes=1), {})
    assert connection.connected is False
    assert (connection.problem, connection.failed_request) == (PROBLEM_NO_DATA, None)
    assert connection.failed_polls_in_a_row == 2

    connection.record_failure(NOON + timedelta(minutes=2), {"installation devices": (PROBLEM_TIMEOUT, "TimeoutError"), "elements": (PROBLEM_DNS, "x")})
    # the elements request decides the poll: its problem is the one shown
    assert (connection.problem, connection.failed_request, connection.detail) == (PROBLEM_DNS, "elements", "x")

    connection.record_success(NOON + timedelta(minutes=3), 0.42)
    attributes = connection.as_attributes()
    assert connection.connected is True
    assert attributes["problem"] is None and attributes["failed_polls_in_a_row"] == 0
    assert attributes["failed_polls_today"] == 3
    assert attributes["last_failure"] == (NOON + timedelta(minutes=2)).isoformat()
    assert attributes["last_success"] == (NOON + timedelta(minutes=3)).isoformat()
    assert attributes["response_time"] == 0.42

    connection.record_failure(NOON + timedelta(days=1), {}, rejected=True)
    assert connection.failed_polls_today == 1
    assert (connection.problem, connection.failed_request) == (PROBLEM_LOGIN_REJECTED, "login")


def _coordinator(hass, api):
    coordinator = CSNetHomeCoordinator(hass, 60, "entry", api=api)
    return coordinator


async def test_coordinator_notes_each_poll(hass):
    """A failed poll keeps the problems of its requests; the next poll starts from none."""
    api = CSNetHomeAPI(hass, "user", "pass")
    coordinator = _coordinator(hass, api)

    async def failing():
        api.note_problem("elements", PROBLEM_TIMEOUT, "TimeoutError")
        raise UpdateFailed("CSNet Manager returned no data")

    coordinator._async_fetch_data = failing
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert (coordinator.connection.connected, coordinator.connection.problem) == (False, PROBLEM_TIMEOUT)

    async def working():
        assert api.problems == {}
        api.response_seconds["elements"] = 0.3
        return {"sensors": []}

    coordinator._async_fetch_data = working
    assert await coordinator._async_update_data() == {"sensors": []}
    assert coordinator.connection.connected is True
    assert coordinator.connection.response_seconds == 0.3


async def test_coordinator_notes_rejected_credentials(hass):
    """Credentials CSNet refuses say so, whatever the requests noted."""
    coordinator = _coordinator(hass, CSNetHomeAPI(hass, "user", "pass"))
    coordinator._async_fetch_data = AsyncMock(side_effect=ConfigEntryAuthFailed("rejected"))
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()
    assert coordinator.connection.problem == PROBLEM_LOGIN_REJECTED


def test_connection_sensor_stays_available_and_reports_the_problem():
    """When the polls fail, the sensor is off with the reason, not unavailable."""
    connection = CloudConnection()
    coordinator = SimpleNamespace(
        connection=connection,
        last_update_success=False,
        get_installation_devices_data=lambda: {},
        get_common_data=lambda: {},
    )
    sensor = CSNetHomeCloudConnectionSensor(coordinator)
    assert sensor.available is True
    assert sensor.is_on is None
    assert sensor.unique_id == "csnet_home-cloud-connection"
    assert sensor.device_class == "connectivity"
    assert sensor.entity_category == "diagnostic"

    connection.record_failure(NOON, {"elements": (PROBLEM_TIMEOUT, "TimeoutError")})
    assert sensor.is_on is False
    assert sensor.extra_state_attributes["problem"] == PROBLEM_TIMEOUT
    assert sensor.device_info["name"] == "System-Controller"

    connection.record_success(NOON, 0.2)
    assert sensor.is_on is True


async def test_a_login_form_timeout_is_named_and_noted(hass, caplog):
    """The login form timing out was logged as "Login exception: " with nothing after it."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.session = MagicMock(closed=False)
    api.session.post = MagicMock(side_effect=asyncio.TimeoutError())
    api.get_xsrf_token = AsyncMock(return_value=True)
    api.xsrf_token = "token"

    assert await api.async_login() is False
    assert "Could not sign in to CSNet Manager: TimeoutError" in caplog.text
    assert "Login exception" not in caplog.text
    assert api.problems["login"] == (PROBLEM_TIMEOUT, "TimeoutError")
