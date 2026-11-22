"""Tests for the sample recorder: what it writes, what it hides, and its services."""

from __future__ import annotations

import gzip
import json
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.csnet_home.const import CONF_ENERGY_METER, CONF_ENERGY_METER_POWER, DOMAIN
from custom_components.csnet_home.diagnostics import REDACTED
from custom_components.csnet_home.sample_recorder import SAMPLE_FORMAT, SampleRecorder, redact_reply, sample_header
from tests.replay.sample import read_sample


def _lines(path):
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def test_redact_reply_hides_the_installation_and_the_account():
    """The installation's name, its position and the account are not written."""
    elements = {
        "status": "success",
        "data": {
            "name": "Home of Someone",
            "latitude": 45.1,
            "installation": 99,
            "rooms": [{"id": 3, "installation_id": 99}],
            "elements": [{"parentName": "Kitchen"}],
        },
    }
    redacted = redact_reply("elements", elements)
    assert redacted["data"]["name"] == REDACTED
    assert redacted["data"]["latitude"] == REDACTED
    assert redacted["data"]["installation"] == REDACTED
    assert redacted["data"]["rooms"] == [{"id": 3, "installation_id": REDACTED}]
    # zone names are kept: the entities are named after them
    assert redacted["data"]["elements"][0]["parentName"] == "Kitchen"
    # the reply itself is not changed
    assert elements["data"]["name"] == "Home of Someone"

    devices = {"data": [{"ownerId": 7, "key": "abc", "firmware": "H-0302 0101000012345678", "indoors": [{"heatingStatus": {"ouHz": 40}, "oduSerial": "X1"}]}]}
    redacted = redact_reply("installation_devices", devices)
    # the version is kept, the module's number is not
    assert redacted["data"][0]["firmware"] == f"H-0302 {REDACTED}"
    assert redacted["data"][0]["ownerId"] == REDACTED
    assert redacted["data"][0]["key"] == REDACTED
    assert redacted["data"][0]["indoors"][0]["oduSerial"] == REDACTED
    assert redacted["data"][0]["indoors"][0]["heatingStatus"]["ouHz"] == 40


def test_redact_reply_keeps_only_how_many_installations():
    """An installation holds addresses and people: only their number is kept."""
    answer = {"status": "success", "data": [{"id": 5, "name": "Home", "address": "1 Street"}, {"id": 6, "name": "Flat"}]}
    assert redact_reply("installations", answer) == {"status": "success", "data": [{"id": 0}, {"id": 1}]}


async def test_recorder_writes_a_header_the_replies_and_the_meter(hass, tmp_path):
    """Each reply is a line with its time and kind; the meter follows the readings."""
    hass.states.async_set("sensor.meter_energy", "12.5", {"unit_of_measurement": "kWh"})
    hass.states.async_set("sensor.meter_power", "1.8", {"unit_of_measurement": "kW"})
    header = sample_header(
        integration_version="9.9.9",
        scan_interval=60,
        time_zone="Europe/Paris",
        power_supply="three_phase",
        meter_energy=True,
        meter_power=True,
        notes="test",
    )
    path = tmp_path / "samples" / "s.jsonl.gz"
    recorder = SampleRecorder(hass, path, header, 3600, "sensor.meter_energy", "sensor.meter_power")
    await recorder.async_start()
    recorder.add("elements", {"status": "success", "data": {"name": "Home", "elements": []}})
    recorder.add("installation devices", {"data": [{"indoors": [{"heatingStatus": {"ouHz": 30}}]}]})
    recorder.add("translations", {"ignored": True})
    await recorder.async_flush()

    lines = _lines(path)
    assert lines[0]["format"] == SAMPLE_FORMAT
    assert lines[0]["meter"] == {"energy": True, "power": True}
    assert [line["kind"] for line in lines[1:]] == ["elements", "installation_devices", "meter"]
    assert lines[1]["data"]["data"]["name"] == REDACTED
    assert lines[3]["energy_kwh"] == 12.5
    assert lines[3]["power_w"] == 1800.0
    assert recorder.replies == 2

    # the replay harness reads the same file
    sample = read_sample(path)
    assert sample.poll_times() == [lines[2]["t"]]
    assert sample.events[-1].values == {"energy_kwh": 12.5, "power_w": 1800.0}


async def test_recorder_writes_slow_replies_only_when_they_change(hass, tmp_path):
    """The energy records are asked for every 15 minutes but change once an hour."""
    path = tmp_path / "s.jsonl.gz"
    recorder = SampleRecorder(hass, path, {"format": SAMPLE_FORMAT}, 3600)
    await recorder.async_start()
    for hours in (1, 1, 2):
        recorder.add("energy records", {"data": [{"hourly": [hours]}]})
        recorder.add("elements", {"data": {}})
    await recorder.async_flush()
    kinds = [line["kind"] for line in _lines(path)[1:]]
    assert kinds == ["energy_records", "elements", "elements", "energy_records", "elements"]


async def test_recorder_stops_recording_when_the_time_is_up(hass, tmp_path):
    """Replies that come after the end are not written."""
    recorder = SampleRecorder(hass, tmp_path / "s.jsonl.gz", {"format": SAMPLE_FORMAT}, 0)
    await recorder.async_start()
    recorder.add("elements", {"data": {}})
    await recorder.async_flush()
    assert recorder.active is False
    assert len(_lines(tmp_path / "s.jsonl.gz")) == 1


@pytest.fixture
async def loaded_entry(hass):
    """Return a loaded entry whose coordinator does not reach CSNet."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_USERNAME: "user", CONF_PASSWORD: "pass", CONF_ENERGY_METER: "sensor.meter_energy"})
    entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.csnet_home.coordinator.CSNetHomeCoordinator._async_update_data",
            AsyncMock(return_value={"sensors": [], "common_data": {}}),
        ),
        patch("custom_components.csnet_home.CSNetHomeAPI.close", AsyncMock()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        yield entry


async def test_services_start_and_stop_a_recording(hass, loaded_entry, tmp_path):
    """The start service says where the file goes; stop writes it and leaves a notification."""
    hass.config.config_dir = str(tmp_path)
    api = loaded_entry.runtime_data.api
    response = await hass.services.async_call(DOMAIN, "start_sample_recording", {"duration_hours": 1, "notes": "hello"}, blocking=True, return_response=True)
    assert response["path"].startswith(str(tmp_path / "csnet_home_samples"))
    assert api.sample_recorder is not None

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "start_sample_recording", {}, blocking=True, return_response=True)

    api.sample_recorder.add("elements", {"data": {}})
    with patch("custom_components.csnet_home.persistent_notification.async_create") as notify:
        await hass.services.async_call(DOMAIN, "stop_sample_recording", {}, blocking=True)
    assert api.sample_recorder is None
    assert response["path"] in notify.call_args.args[1]

    lines = _lines(response["path"])
    assert lines[0]["notes"] == "hello"
    # the meter of the settings is used when none is given
    assert lines[0]["meter"] == {"energy": True, "power": False}
    assert [line["kind"] for line in lines[1:]] == ["elements"]

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "stop_sample_recording", {}, blocking=True)


async def test_recording_uses_the_power_sensor_of_the_settings(hass, loaded_entry, tmp_path):
    """The settings' power sensor is recorded with the settings' meter, not with another meter picked for the sample."""
    hass.config.config_dir = str(tmp_path)
    hass.config_entries.async_update_entry(loaded_entry, data={**loaded_entry.data, CONF_ENERGY_METER_POWER: "sensor.phases_power"})
    api = loaded_entry.runtime_data.api

    await hass.services.async_call(DOMAIN, "start_sample_recording", {"duration_hours": 1}, blocking=True, return_response=True)
    assert api.sample_recorder._meter_power_entity == "sensor.phases_power"  # pylint: disable=protected-access
    await hass.services.async_call(DOMAIN, "stop_sample_recording", {}, blocking=True)

    await hass.services.async_call(
        DOMAIN, "start_sample_recording", {"duration_hours": 1, "meter_energy_entity": "sensor.other_energy"}, blocking=True, return_response=True
    )
    assert api.sample_recorder._meter_power_entity is None  # pylint: disable=protected-access
    await hass.services.async_call(DOMAIN, "stop_sample_recording", {}, blocking=True)


async def test_unloading_the_entry_keeps_the_recording(hass, loaded_entry, tmp_path):
    """A reload or a shutdown writes what was recorded so far."""
    hass.config.config_dir = str(tmp_path)
    response = await hass.services.async_call(DOMAIN, "start_sample_recording", {}, blocking=True, return_response=True)
    loaded_entry.runtime_data.api.sample_recorder.add("elements", {"data": {}})
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    assert [line["kind"] for line in _lines(response["path"])[1:]] == ["elements"]
