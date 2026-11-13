"""Alarm polling, and notifying each alarm only once."""

import copy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.csnet_home import coordinator as coordinator_module
from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.coordinator import ALARM_POLL_SECONDS, CSNetHomeCoordinator, alarm_storage_key

ACTIVE = "1980-01-01 00:00:00"
ALARMS = {
    "status": "success",
    "data": [
        {"id": 101, "unitId": 6996, "code": 62, "recoveredAtString": ACTIVE},
        {"id": 102, "unitId": 6996, "code": 70, "recoveredAtString": ACTIVE},
        {"id": 90, "unitId": 6996, "code": 41, "recoveredAtString": "2025-10-31 13:00:00"},
    ],
}
ZONE_IN_ALARM = {
    "device_id": 1,
    "room_id": 2,
    "zone_id": 1,
    "device_name": "Hitachi PAC",
    "room_name": "Ground floor",
    "alarm_code": 62,
}


class Clock:
    """A monotonic clock the tests move by hand."""

    def __init__(self):
        """Start at an arbitrary time."""
        self.now = 1000.0

    def __call__(self):
        """Return the current time."""
        return self.now


@pytest.fixture
def clock():
    """Replace the coordinator's clock."""
    fake = Clock()
    with patch.object(coordinator_module.time, "monotonic", fake):
        yield fake


@pytest.fixture
def api(hass):
    """Return an API double answering with two active alarms and one recovered alarm."""
    mock = MagicMock(spec=CSNetHomeAPI)
    mock.hass = hass
    mock.logged_in = True
    mock.async_get_elements_data = AsyncMock(side_effect=lambda: {"sensors": [], "common_data": {"name": "Home"}})
    mock.async_get_installation_devices_data = AsyncMock(return_value={})
    mock.async_get_installation_alarms = AsyncMock(side_effect=lambda: copy.deepcopy(ALARMS))
    mock.load_translations = AsyncMock()
    mock.translate_alarm = MagicMock(side_effect=lambda code: f"Alarm {code}")
    mock.get_heating_status_from_installation_devices = MagicMock(return_value={})
    return mock


@pytest.fixture
def notify(hass):
    """Capture the notifications the coordinator creates."""
    call = AsyncMock()
    hass.services = MagicMock()
    hass.services.async_call = call
    return call


def notified_ids(notify):
    """Return the notification ids created so far."""
    return [call.args[2]["notification_id"] for call in notify.call_args_list]


def make(hass, api, **kwargs):
    """Build a coordinator for the stored entry id "entry"."""
    return CSNetHomeCoordinator(hass, 60, "entry", filtered_alarm_codes="", api=api, **kwargs)


async def test_alarms_are_asked_for_every_five_minutes(hass, hass_storage, api, notify, clock):
    """Readings are polled every minute, the alarm list only when it is due."""
    coordinator = make(hass, api)

    for _ in range(4):
        await coordinator._async_update_data()
        clock.now += 60
    assert api.async_get_elements_data.await_count == 4
    assert api.async_get_installation_alarms.await_count == 1
    # the alarm history stays available between two requests
    assert len(coordinator.get_installation_alarms_data()["data"]) == 3

    clock.now += ALARM_POLL_SECONDS
    await coordinator._async_update_data()
    assert api.async_get_installation_alarms.await_count == 2


async def test_each_active_alarm_is_notified_once(hass, hass_storage, api, notify, clock):
    """Later polls and later alarm requests do not repeat a notification."""
    coordinator = make(hass, api)

    for _ in range(3):
        await coordinator._async_update_data()
        clock.now += ALARM_POLL_SECONDS

    assert sorted(notified_ids(notify)) == ["csnet_home_inst_alarm_101", "csnet_home_inst_alarm_102"]


async def test_a_failed_alarm_request_does_not_notify_everything_again(hass, hass_storage, api, notify, clock):
    """Issue #185: one failed request used to forget what was notified."""
    coordinator = make(hass, api)
    await coordinator._async_update_data()
    assert len(notify.call_args_list) == 2

    # the session expires: the alarm request fails once
    clock.now += ALARM_POLL_SECONDS
    api.async_get_installation_alarms.side_effect = lambda: None
    await coordinator._async_update_data()
    # the history sensor keeps the last list instead of dropping to zero
    assert len(coordinator.get_installation_alarms_data()["data"]) == 3

    # the failed request is repeated on the next poll, without waiting five minutes
    clock.now += 60
    api.async_get_installation_alarms.side_effect = lambda: copy.deepcopy(ALARMS)
    await coordinator._async_update_data()
    assert api.async_get_installation_alarms.await_count == 3
    assert len(notify.call_args_list) == 2


async def test_notified_alarms_survive_a_restart(hass, hass_storage, api, notify, clock):
    """A new coordinator (restart or reload) does not notify the same alarms again."""
    await make(hass, api)._async_update_data()
    assert hass_storage[alarm_storage_key("entry")]["data"]["installation_alarm_ids"] == [101, 102]
    assert len(notify.call_args_list) == 2

    restarted = make(hass, api)
    await restarted._async_update_data()
    assert len(notify.call_args_list) == 2

    # an alarm that appears after the restart is still notified
    new_alarms = copy.deepcopy(ALARMS)
    new_alarms["data"].append({"id": 103, "unitId": 6996, "code": 75, "recoveredAtString": ACTIVE})
    api.async_get_installation_alarms.side_effect = lambda: new_alarms
    clock.now += ALARM_POLL_SECONDS
    await restarted._async_update_data()
    assert notified_ids(notify)[2:] == ["csnet_home_inst_alarm_103"]


async def test_zone_alarm_is_not_notified_again_after_a_restart(hass, hass_storage, api, notify, clock):
    """The alarm code of a zone is remembered too."""
    api.async_get_installation_alarms.side_effect = lambda: {"data": []}
    api.async_get_elements_data.side_effect = lambda: {"sensors": [dict(ZONE_IN_ALARM)], "common_data": {"name": "Home"}}

    await make(hass, api)._async_update_data()
    assert len(notify.call_args_list) == 1

    await make(hass, api)._async_update_data()
    assert len(notify.call_args_list) == 1


async def test_a_recovered_alarm_is_forgotten_and_a_new_one_notified(hass, hass_storage, api, notify, clock):
    """An alarm that is no longer active leaves the stored list."""
    coordinator = make(hass, api)
    await coordinator._async_update_data()

    recovered = copy.deepcopy(ALARMS)
    recovered["data"][0]["recoveredAtString"] = "2025-11-01 08:00:00"
    api.async_get_installation_alarms.side_effect = lambda: recovered
    clock.now += ALARM_POLL_SECONDS
    await coordinator._async_update_data()

    assert hass_storage[alarm_storage_key("entry")]["data"]["installation_alarm_ids"] == [102]
    assert len(notify.call_args_list) == 2


async def test_alarms_seen_with_notifications_off_are_not_notified_when_turned_on(hass, hass_storage, api, notify, clock):
    """Turning notifications on later only notifies alarms that appear from then on."""
    await make(hass, api, enable_alarm_notifications=False)._async_update_data()
    assert notify.call_args_list == []

    await make(hass, api, enable_alarm_notifications=True)._async_update_data()
    assert notify.call_args_list == []


async def test_deleting_an_alarm_asks_for_the_list_again(hass, hass_storage, api, notify, clock):
    """After delete_alarm the next poll reads the alarm list without waiting."""
    coordinator = make(hass, api)
    await coordinator._async_update_data()

    coordinator.async_invalidate_installation_alarms()
    clock.now += 60
    await coordinator._async_update_data()
    assert api.async_get_installation_alarms.await_count == 2


async def test_unreadable_storage_does_not_stop_the_poll(hass, hass_storage, api, notify, clock):
    """Storage errors are logged; readings and notifications still work."""
    coordinator = make(hass, api)
    with (
        patch.object(coordinator._alarm_store, "async_load", AsyncMock(side_effect=OSError("disk"))),
        patch.object(coordinator._alarm_store, "async_save", AsyncMock(side_effect=OSError("disk"))),
    ):
        data = await coordinator._async_update_data()
    assert data["common_data"]["name"] == "Home"
    assert len(notify.call_args_list) == 2
