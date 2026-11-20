"""Replay every sample through the integration and check what it shows.

The small samples in tests/fixtures/samples always run. Samples fetched with
``python scripts/fetch_samples.py`` (into tests/samples) run with
``pytest -m replay``. Set ``CSNET_REPLAY_REPORT=<file>`` to write each day's
figures to a JSON file, to compare two branches with tests/replay/report.py.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from custom_components.csnet_home.const import HEAT_SOURCE_CALCULATED, HEAT_SOURCES

from .harness import replay_sample
from .report import check_invariants, summary
from .sample import REPO_ROOT, find_samples, read_sample

BUNDLED = REPO_ROOT / "tests" / "fixtures" / "samples"
_REPORT: list[dict] = []


def _params():
    params = []
    for path in find_samples():
        marks = [] if BUNDLED in path.parents else [pytest.mark.replay]
        params.append(pytest.param(path, id=path.name.split(".")[0], marks=marks))
    return params


@pytest.fixture(scope="module", autouse=True)
def _write_report():
    yield
    target = os.environ.get("CSNET_REPLAY_REPORT")
    if target and _REPORT:
        Path(target).write_text(json.dumps(_REPORT, indent=1), encoding="utf-8")


@pytest.mark.parametrize("path", _params())
async def test_replay(hass, freezer, path: Path):
    """The sample replays without errors, and the figures stay possible."""
    sample = read_sample(path)
    result = await replay_sample(hass, freezer, sample)
    assert result.polls, "the sample has no poll"
    _REPORT.append(summary(result))
    assert check_invariants(result) == []


@pytest.mark.parametrize("path", _params())
async def test_replay_calculated_heat(hass, freezer, path: Path):
    """With the heat calculated by the integration, the heat counters fill up while the compressor runs."""
    sample = read_sample(path)
    result = await replay_sample(hass, freezer, sample, heat_source=HEAT_SOURCE_CALCULATED)
    assert check_invariants(result) == []
    heat = [p.values.get("server_heat_today_kwh") for p in result.polls]
    assert all(isinstance(v, float) for v in heat[1:]), "heat produced today has no value"
    if any((p.values.get("compressor_hz") or 0) > 0 for p in result.polls):
        assert max(heat[1:]) > 0, "the compressor ran but no heat was counted"


@pytest.mark.parametrize("heat_source", HEAT_SOURCES)
@pytest.mark.parametrize("path", _params())
async def test_replay_survives_restarts(hass, freezer, path: Path, heat_source: str):
    """A restart of Home Assistant in the middle of a day keeps the day's and month's figures."""
    sample = read_sample(path)
    count = len(sample.poll_times())
    result = await replay_sample(hass, freezer, sample, heat_source=heat_source, restart_before=(count // 3, count // 2 + 7))
    assert len(result.restarts) == 2
    # a figure that went down within a day (back to 0 after a restart) is reported here
    assert check_invariants(result) == []
    for index in result.restarts:
        before, after = result.polls[index - 1], result.polls[index]
        if before.time.date() != after.time.date():
            continue
        for name in ("daily_consumption_kwh", "server_heat_today_kwh", "server_heat_month_kwh"):
            old, new = before.values.get(name), after.values.get(name)
            if isinstance(old, float):
                assert isinstance(new, float), f"{name} lost its value after the restart at {after.time}"
                assert new >= old - 1e-6, f"{name} went from {old} to {new} after the restart at {after.time}"


# Keys that must not carry a value in a sample kept in this repository
_SECRET_KEYS = {"latitude", "longitude", "ownerid", "installationid", "installation_id", "installation", "administrator", "username", "user", "key", "hash"}
_SECRET_FRAGMENTS = ("serial", "mail", "password", "token", "displayablename")


def _unredacted(value, where=""):
    if isinstance(value, dict):
        found = []
        for key, item in value.items():
            lowered = str(key).lower()
            if (lowered in _SECRET_KEYS or any(f in lowered for f in _SECRET_FRAGMENTS)) and item not in (None, "", 0, -1, False, "**REDACTED**"):
                found.append(f"{where}.{key}")
            else:
                found += _unredacted(item, f"{where}.{key}")
        return found
    if isinstance(value, list):
        return [leak for item in value for leak in _unredacted(item, f"{where}[]")]
    return []


@pytest.mark.parametrize("path", sorted(BUNDLED.glob("*.jsonl.gz")), ids=lambda p: p.name.split(".")[0])
def test_bundled_samples_are_redacted(path: Path):
    """A sample kept in the repository carries no account or home identifier."""
    sample = read_sample(path)
    leaks = {leak for event in sample.events for leak in _unredacted(event.data, event.kind)}
    elements = [e.data for e in sample.events if e.kind == "elements"]
    assert all((e.get("data") or {}).get("name") in (None, "", "**REDACTED**") for e in elements)
    assert not leaks
