"""Turn a replay into checks and per-day figures, and compare two runs.

Usage, to compare the figures of two branches::

    python -m tests.replay.report base.json head.json > comparison.md

where each JSON file was written by the replay tests with
``CSNET_REPLAY_REPORT=<file> pytest -m replay``. A run with pytest-xdist
writes one file per worker beside it (``<file>.gw0.json``...): give the same
``<file>`` and they are read together. Without a base report, the head is
shown alone.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .harness import ReplayResult

# A day counts as complete when the sample covers it from this close to midnight
DAY_EDGE_MINUTES = 15
# Figures no unit reaches; above them a COP is a bug, not a good day
MAX_COP = 12.0


def check_invariants(result: ReplayResult) -> list[str]:
    """Return what went wrong during a replay: errors logged, impossible or decreasing figures."""
    problems = [f"error logged: {message}" for message in result.errors]
    previous: dict[str, tuple[date, float]] = {}
    for poll in result.polls:
        values = poll.values
        for name in ("instant_consumption_w", "output_power_w"):
            value = values.get(name)
            if isinstance(value, float) and value < 0:
                problems.append(f"{poll.time:%Y-%m-%d %H:%M} {name} is negative ({value})")
        for name in ("daily_hvac_cop", "metered_cop_today"):
            value = values.get(name)
            if isinstance(value, float) and not 0 <= value <= MAX_COP:
                problems.append(f"{poll.time:%Y-%m-%d %H:%M} {name} is out of range ({value})")
        for name in ("daily_consumption_kwh", "server_heat_today_kwh"):
            value = values.get(name)
            if not isinstance(value, float):
                continue
            day = poll.time.date()
            last = previous.get(name)
            if last and last[0] == day and value < last[1] - 1e-6:
                problems.append(f"{poll.time:%Y-%m-%d %H:%M} {name} went down from {last[1]} to {value}")
            previous[name] = (day, value)
    if result.polls and all(p.values.get("compressor_hz") is None for p in result.polls):
        problems.append("the compressor frequency never had a value")
    # one line per kind of problem is enough to see what is wrong
    seen: dict[str, int] = defaultdict(int)
    kept = []
    for problem in problems:
        kind = problem.split(" ", 2)[-1].split(" (")[0]
        seen[kind] += 1
        if seen[kind] <= 3:
            kept.append(problem)
    return kept


def warnings(result: ReplayResult) -> list[str]:
    """Return what looks wrong but does not fail the replay: counted, to compare two runs."""
    found = []
    spikes = [p for p in result.polls if isinstance(p.values.get("instant_cop"), float) and p.values["instant_cop"] > MAX_COP]
    if spikes:
        worst = max(spikes, key=lambda p: p.values["instant_cop"])
        found.append(f"instant COP above {MAX_COP:g} on {len(spikes)} polls (up to {worst.values['instant_cop']} at {worst.time:%Y-%m-%d %H:%M})")
    return found


def _last(polls, name):
    for poll in reversed(polls):
        value = poll.values.get(name)
        if isinstance(value, float):
            return value
    return None


def _max(polls, name):
    values = [p.values.get(name) for p in polls if isinstance(p.values.get(name), float)]
    return max(values) if values else None


def csnet_daily_heat(result: ReplayResult) -> dict[date, float]:
    """Return CSNet's own heat of each day, from the last energy records of the sample.

    CSNet groups its hourly records by the date in their time, as its daily
    records do. The integration's "heat produced today" can miss the day's
    last hour: this is the figure to compare against.
    """
    energy = [e.data for e in result.sample.events if e.kind == "energy_records"]
    totals: dict[date, float] = defaultdict(float)
    for unit in ((energy[-1] or {}).get("data") or []) if energy else []:
        for record in unit.get("hourly") or []:
            time = record.get("time") or {}
            try:
                day = date(time["year"], time["month"], time["day"])
            except (KeyError, TypeError, ValueError):
                continue
            totals[day] += sum(v for v in (record.get("capacity") or {}).values() if isinstance(v, (int, float)))
    return dict(totals)


def daily_figures(result: ReplayResult) -> list[dict[str, Any]]:
    """Return the figures of each day of the replay."""
    csnet_heat = csnet_daily_heat(result)
    by_day: dict[date, list] = defaultdict(list)
    for poll in result.polls:
        by_day[poll.time.date()].append(poll)
    days = []
    for day, polls in sorted(by_day.items()):
        first, last = polls[0].time, polls[-1].time
        complete = first.hour * 60 + first.minute <= DAY_EDGE_MINUTES and last.hour * 60 + last.minute >= 24 * 60 - DAY_EDGE_MINUTES
        meter = [p.meter_energy_kwh for p in polls if p.meter_energy_kwh is not None]
        running = sum(1 for p in polls if (p.values.get("compressor_hz") or 0) > 0)
        days.append(
            {
                "day": day.isoformat(),
                "complete": complete,
                "polls": len(polls),
                "running_polls": running,
                "estimated_kwh": _max(polls, "daily_consumption_kwh"),
                "meter_kwh": round(meter[-1] - meter[0], 2) if len(meter) > 1 else None,
                "csnet_heat_kwh": csnet_heat.get(day) if complete else None,
                "heat_today_sensor_kwh": _max(polls, "server_heat_today_kwh"),
                "hvac_cop": _last(polls, "daily_hvac_cop"),
                "metered_cop": _last(polls, "metered_cop_today"),
            }
        )
    return days


def summary(result: ReplayResult) -> dict[str, Any]:
    """Return what the report file keeps of a replay."""
    return {
        "sample": result.sample.name,
        "source": result.sample.header.get("source"),
        "polls": len(result.polls),
        "entities": result.entity_count,
        "heat_source": result.heat_source,
        "problems": check_invariants(result),
        "warnings": warnings(result),
        "days": daily_figures(result),
    }


COLUMNS = [
    ("estimated_kwh", "Estimated kWh"),
    ("meter_kwh", "Meter kWh"),
    ("heat_today_sensor_kwh", "Heat today kWh"),
    ("csnet_heat_kwh", "CSNet heat kWh"),
    ("hvac_cop", "HVAC COP"),
]


def _fmt(value) -> str:
    return "–" if value is None else f"{value:.2f}"


def compare(base: list[dict], head: list[dict]) -> str:
    """Return a markdown table of each complete day's figures before and after a change."""
    base_days = {(s["sample"], d["day"]): d for s in base for d in s["days"]}
    lines = [
        "| Sample | Day | " + " | ".join(label for _, label in COLUMNS) + " |",
        "|---|---|" + "---|" * len(COLUMNS),
    ]
    for sample in head:
        for day in sample["days"]:
            if not day["complete"]:
                continue
            before = base_days.get((sample["sample"], day["day"]), {})
            cells = []
            for key, _ in COLUMNS:
                old, new = before.get(key), day.get(key)
                if key == "meter_kwh" or old == new:
                    cells.append(_fmt(new))
                else:
                    cells.append(f"{_fmt(old)} → **{_fmt(new)}**")
            lines.append(f"| {sample['sample']} | {day['day']} | " + " | ".join(cells) + " |")
    problems = [f"- {s['sample']}: {p}" for s in head for p in s["problems"]]
    if problems:
        lines += ["", "**Problems found:**", *problems]
    base_warnings = {s["sample"]: s.get("warnings", []) for s in base}
    notes = []
    for sample in head:
        for warning in sample.get("warnings", []):
            before = [w for w in base_warnings.get(sample["sample"], []) if w.split(" on ")[0] == warning.split(" on ")[0]]
            notes.append(f"- {sample['sample']}: {warning}" + (f" (base: {before[0].split(' on ', 1)[1]})" if before and before[0] != warning else ""))
    if notes:
        lines += ["", "**Warnings:**", *notes]
    return "\n".join(lines) + "\n"


def worker_report_path(target: Path, worker: str | None) -> Path:
    """Return the file a replay run writes its report to: one per pytest-xdist worker."""
    if not worker:
        return target
    return target.with_name(f"{target.stem}.{worker}{target.suffix}")


def load_report(target: Path) -> list[dict] | None:
    """Return the report written to ``target`` and by each worker beside it, or None without any."""
    paths = [target] if target.is_file() else []
    paths += sorted(target.parent.glob(f"{target.stem}.gw*{target.suffix}"))
    if not paths:
        return None
    report = []
    for path in paths:
        report += json.loads(path.read_text(encoding="utf-8"))
    # workers finish in any order: keep the table in the same order on each run
    return sorted(report, key=lambda s: (s["sample"], s.get("heat_source") or ""))


def main(argv: list[str]) -> int:
    """Print the comparison of two reports."""
    if len(argv) != 3:
        print(__doc__)
        return 2
    base, head = load_report(Path(argv[1])), load_report(Path(argv[2]))
    if head is None:
        print("No report was written.")
        return 0
    if base is not None:
        print("Figures of each complete day, base branch → this change.\n")
    sys.stdout.write(compare(base or head, head))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
