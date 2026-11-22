"""Run the schedule blueprints in Home Assistant and check the setpoints they send."""

import shutil
from datetime import datetime
from pathlib import Path

import pytest
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

BLUEPRINTS = Path(__file__).parent.parent / "blueprints" / "automation" / "csnet_home"
ZONE = "climate.house_living_room"
SCHEDULE = "schedule.living_room_heating"


async def _setup(hass: HomeAssistant, blueprint: str, inputs: dict) -> None:
    target = Path(hass.config.path("blueprints", "automation", "csnet_home"))
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy(BLUEPRINTS / blueprint, target / blueprint)
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "alias": "test",
                "use_blueprint": {"path": f"csnet_home/{blueprint}", "input": inputs},
            }
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get("automation.test").state == "on"


async def _start(hass: HomeAssistant) -> None:
    """Finish a Home Assistant start: automations set up during it get their start trigger."""
    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()


def _zone(hass, state="heat", temperature=19.0):
    hass.states.async_set(ZONE, state, {"temperature": temperature})


@pytest.mark.parametrize(
    ("schedule_state", "expected"),
    [("on", 21.5), ("off", 17.0)],
)
async def test_weekly_schedule_sets_comfort_or_eco(hass, schedule_state, expected):
    """The schedule on sets the comfort temperature, off the eco one."""
    calls = async_mock_service(hass, "climate", "set_temperature")
    _zone(hass)
    hass.states.async_set(SCHEDULE, "on" if schedule_state == "off" else "off")
    await _setup(
        hass,
        "csnet_weekly_schedule.yaml",
        {"climate_entity": ZONE, "schedule_entity": SCHEDULE, "comfort_temperature": 21.5, "eco_temperature": 17},
    )

    hass.states.async_set(SCHEDULE, schedule_state)
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["entity_id"] == [ZONE]
    assert calls[0].data["temperature"] == expected


async def test_weekly_schedule_skips_off_zone_same_setpoint_and_other_modes(hass):
    """Nothing is sent for a zone that is off, already at the setpoint, or in another mode."""
    calls = async_mock_service(hass, "climate", "set_temperature")
    hass.states.async_set(SCHEDULE, "off")
    _zone(hass, "off")
    await _setup(
        hass,
        "csnet_weekly_schedule.yaml",
        {"climate_entity": ZONE, "schedule_entity": SCHEDULE, "comfort_temperature": 21, "eco_temperature": 18},
    )

    # Zone off: nothing sent
    hass.states.async_set(SCHEDULE, "on")
    await hass.async_block_till_done()
    assert calls == []

    # Zone turned back on: the schedule's setpoint is applied
    _zone(hass, "heat", 19.0)
    await hass.async_block_till_done()
    assert [c.data["temperature"] for c in calls] == [21.0]

    # Already at the setpoint: nothing sent
    _zone(hass, "heat", 18.0)
    hass.states.async_set(SCHEDULE, "off")
    await hass.async_block_till_done()
    assert len(calls) == 1

    # Cooling is not in the default modes
    _zone(hass, "cool", 25.0)
    hass.states.async_set(SCHEDULE, "on")
    await hass.async_block_till_done()
    assert len(calls) == 1


async def test_weekly_schedule_applies_on_start(hass):
    """The schedule's temperature is applied when Home Assistant starts."""
    calls = async_mock_service(hass, "climate", "set_temperature")
    hass.states.async_set(SCHEDULE, "on")
    _zone(hass)
    hass.set_state(CoreState.not_running)
    await _setup(
        hass,
        "csnet_weekly_schedule.yaml",
        {"climate_entity": ZONE, "schedule_entity": SCHEDULE, "comfort_temperature": 22, "eco_temperature": 18},
    )

    await _start(hass)

    assert [c.data["temperature"] for c in calls] == [22.0]


DAY_NIGHT_INPUTS = {
    "climate_entity": ZONE,
    "day_temperature": 20,
    "day_time": "06:30:00",
    "bedtime_time": "21:00:00",
    "bedtime_increase": 1,
    "night_time": "00:30:00",
    "night_decrease": 2,
}


@pytest.mark.parametrize(
    ("clock", "expected"),
    [
        ("06:30:00", 20.0),
        ("12:00:00", 20.0),
        ("21:00:00", 21.0),
        ("23:59:00", 21.0),
        ("00:30:00", 18.0),
        ("03:00:00", 18.0),
    ],
)
async def test_day_bedtime_night_picks_the_period(hass, freezer, clock, expected):
    """The period whose start time passed last sets the temperature."""
    freezer.move_to(dt_util.as_utc(datetime.fromisoformat(f"2026-11-23T{clock}").replace(tzinfo=dt_util.get_default_time_zone())))
    calls = async_mock_service(hass, "climate", "set_temperature")
    _zone(hass, "heat", 10.0)
    hass.set_state(CoreState.not_running)
    await _setup(hass, "csnet_day_bedtime_night.yaml", DAY_NIGHT_INPUTS)

    await _start(hass)

    assert [c.data["temperature"] for c in calls] == [expected]


async def test_day_bedtime_night_fires_at_the_times(hass, freezer):
    """The temperature changes at bedtime and at night, also after midnight."""
    tz = dt_util.get_default_time_zone()
    freezer.move_to(dt_util.as_utc(datetime(2026, 11, 23, 20, 59, 59, tzinfo=tz)))
    calls = async_mock_service(hass, "climate", "set_temperature")
    _zone(hass, "heat", 20.0)
    await _setup(hass, "csnet_day_bedtime_night.yaml", DAY_NIGHT_INPUTS)

    now = dt_util.as_utc(datetime(2026, 11, 23, 21, 0, 0, tzinfo=tz))
    freezer.move_to(now)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()
    assert [c.data["temperature"] for c in calls] == [21.0]

    _zone(hass, "heat", 21.0)
    now = dt_util.as_utc(datetime(2026, 11, 24, 0, 30, 0, tzinfo=tz))
    freezer.move_to(now)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()
    assert [c.data["temperature"] for c in calls] == [21.0, 18.0]
