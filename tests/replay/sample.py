"""Read sample files: what CSNet Manager sent to a unit, recorded or rebuilt from history.

See custom_components/csnet_home/sample_recorder.py for the format.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

SAMPLE_FORMAT = "csnet-home-sample"
SUPPORTED_VERSIONS = {1}
REPO_ROOT = Path(__file__).resolve().parents[2]
# Samples fetched with scripts/fetch_samples.py (not in git), and the small ones kept with the tests
SAMPLE_DIRS = (REPO_ROOT / "tests" / "samples", REPO_ROOT / "tests" / "fixtures" / "samples")


@dataclass
class Event:
    """One line of a sample after the header."""

    t: float
    kind: str
    data: Any = None
    values: dict = field(default_factory=dict)


@dataclass
class Sample:
    """A sample file: its header and its events in time order."""

    path: Path
    header: dict
    events: list[Event]

    @property
    def name(self) -> str:
        """Return the file name without its extensions."""
        return self.path.name.split(".")[0]

    @property
    def start(self) -> datetime:
        """Return when the sample begins (aware, UTC)."""
        return datetime.fromisoformat(self.header["start"])

    def at(self, t: float) -> datetime:
        """Return the time of an event."""
        return self.start + timedelta(seconds=t)

    def poll_times(self) -> list[float]:
        """Return when the unit's readings were received: one per poll."""
        return [e.t for e in self.events if e.kind == "installation_devices"]


class SampleError(ValueError):
    """The file is not a sample this harness can read."""


def read_sample(path: Path) -> Sample:
    """Read a sample file."""
    with gzip.open(path, "rt", encoding="utf-8") as file:
        lines = [line for line in file if line.strip()]
    if not lines:
        raise SampleError(f"{path} is empty")
    header = json.loads(lines[0])
    if header.get("format") != SAMPLE_FORMAT or header.get("version") not in SUPPORTED_VERSIONS:
        raise SampleError(f"{path} is not a {SAMPLE_FORMAT} file of a supported version")
    events = []
    for line in lines[1:]:
        item = json.loads(line)
        t = float(item.pop("t"))
        kind = item.pop("kind")
        events.append(Event(t, kind, item.pop("data", None), item))
    events.sort(key=lambda e: e.t)
    return Sample(path, header, events)


def find_samples() -> list[Path]:
    """Return every sample file in the sample folders."""
    found = []
    for folder in SAMPLE_DIRS:
        if folder.is_dir():
            found += sorted(folder.rglob("*.jsonl.gz"))
    return found
