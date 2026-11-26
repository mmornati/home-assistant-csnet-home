"""Start each replay run with no report file left from an earlier run."""

from __future__ import annotations

import os
from pathlib import Path


def pytest_configure(config):
    """Delete the report and the per-worker reports of an earlier run, once, before the workers start."""
    target = os.environ.get("CSNET_REPLAY_REPORT")
    if not target or hasattr(config, "workerinput"):
        return
    target = Path(target)
    for path in [target, *target.parent.glob(f"{target.stem}.gw*{target.suffix}")]:
        path.unlink(missing_ok=True)
