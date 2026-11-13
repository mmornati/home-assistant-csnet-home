"""Orders to the unit: one at a time, and a read-back that does not block the caller."""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.csnet_home import climate, number, sensor, water_heater
from custom_components.csnet_home.api import CSNetHomeAPI
from custom_components.csnet_home.coordinator import WRITE_REFRESH_DELAY_SECONDS, CSNetHomeCoordinator


def test_platforms_declare_how_many_updates_run_at_once():
    """Platforms that send orders take one at a time; sensors are not limited."""
    assert climate.PARALLEL_UPDATES == 1
    assert water_heater.PARALLEL_UPDATES == 1
    assert number.PARALLEL_UPDATES == 1
    assert sensor.PARALLEL_UPDATES == 0


async def test_orders_are_sent_one_at_a_time(hass):
    """Two orders started together do not overlap on the wire, whatever platform they come from."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.logged_in = True
    api.xsrf_token = "token"
    in_flight = 0
    most_in_flight = 0
    order = []

    def post(_url, **kwargs):
        response = MagicMock()
        response.status = 200

        async def text():
            nonlocal in_flight, most_in_flight
            in_flight += 1
            most_in_flight = max(most_in_flight, in_flight)
            order.append(sorted(key for key in kwargs["data"] if key.startswith(("settingTemp", "runStop"))))
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            in_flight -= 1
            return '{"status":"success"}'

        response.text = text
        manager = MagicMock()
        manager.__aenter__ = AsyncMock(return_value=response)
        manager.__aexit__ = AsyncMock(return_value=False)
        return manager

    api.session = MagicMock()
    api.session.post = MagicMock(side_effect=post)

    results = await asyncio.gather(
        api.async_set_temperature(1, 1234, 1, temperature=20.0),
        api.async_set_hvac_mode(2, 1234, "off"),
        api.async_set_temperature(3, 1234, 1, temperature=50),
    )

    assert results == [True, True, True]
    assert most_in_flight == 1
    assert order == [["settingTempRoomZ1"], ["runStopC2Air"], ["settingTempDHW"]]


async def test_a_failed_order_releases_the_lock(hass):
    """An order that fails does not block the next one."""
    api = CSNetHomeAPI(hass, "user", "pass")
    api.logged_in = True
    api.xsrf_token = "token"
    api.session = MagicMock()
    api.session.post = MagicMock(side_effect=asyncio.TimeoutError)

    assert await api.async_set_temperature(1, 1234, 1, temperature=20.0) is False
    assert not api._write_lock.locked()
    assert await api.async_set_temperature(1, 1234, 1, temperature=20.5) is False


def _coordinator(hass):
    """Return a coordinator whose refresh is counted instead of run."""
    coordinator = CSNetHomeCoordinator(hass, 60, "entry", api=MagicMock())
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


async def _advance(hass, seconds):
    """Move Home Assistant's clock forward."""
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


async def test_read_back_waits_for_the_server_and_does_not_block(hass):
    """Scheduling returns at once; the refresh runs after the delay."""
    coordinator = _coordinator(hass)

    coordinator.async_schedule_refresh_after_write()
    await hass.async_block_till_done()
    coordinator.async_request_refresh.assert_not_awaited()

    await _advance(hass, WRITE_REFRESH_DELAY_SECONDS + 0.1)
    coordinator.async_request_refresh.assert_awaited_once()


async def test_several_orders_give_one_read_back(hass):
    """Each new order restarts the wait: one refresh after the last of them."""
    coordinator = _coordinator(hass)
    start = dt_util.utcnow()

    with patch("homeassistant.helpers.event.dt_util.utcnow", return_value=start):
        coordinator.async_schedule_refresh_after_write()
        coordinator.async_schedule_refresh_after_write()
        coordinator.async_schedule_refresh_after_write()

    await _advance(hass, WRITE_REFRESH_DELAY_SECONDS + 0.1)
    coordinator.async_request_refresh.assert_awaited_once()


async def test_unload_drops_a_waiting_read_back(hass):
    """Nothing is refreshed after the entry was unloaded."""
    coordinator = _coordinator(hass)
    coordinator.async_schedule_refresh_after_write()

    coordinator.async_cancel_refresh_after_write()
    coordinator.async_cancel_refresh_after_write()  # harmless twice

    await _advance(hass, WRITE_REFRESH_DELAY_SECONDS + 0.1)
    coordinator.async_request_refresh.assert_not_awaited()
