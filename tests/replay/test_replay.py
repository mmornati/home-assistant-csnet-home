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
