#!/usr/bin/env python3
"""Resolve the Home Assistant versions CI should test against, from PyPI.

Prints a JSON document and, when running in GitHub Actions, writes the same
values to ``$GITHUB_OUTPUT``:

- ``latest``: newest stable release (e.g. ``2026.10.4``)
- ``latest_python``: Python version that release needs (e.g. ``3.14``)
- ``matrix``: newest patch of each of the last ``--months`` monthly releases,
  as ``[{"ha": "2026.10.4", "python": "3.14"}, ...]``
- ``beta``: newest pre-release newer than ``latest``, or empty string
- ``beta_python``: Python version for ``beta``

Only the standard library is used so the script runs before any ``pip install``.
"""

import argparse
import json
import os
import re
import urllib.request

PYPI = "https://pypi.org/pypi/homeassistant"
STABLE = re.compile(r"^(\d{4})\.(\d+)\.(\d+)$")
BETA = re.compile(r"^(\d{4})\.(\d+)\.(\d+)b(\d+)$")


def _get(url):
    with urllib.request.urlopen(url, timeout=30) as resp:  # nosec B310 - fixed https URL
        return json.load(resp)


def _key(version):
    """Sort key: stable releases sort after their betas."""
    if m := STABLE.match(version):
        return (*map(int, m.groups()), 1_000)
    m = BETA.match(version)
    return (*map(int, m.groups()[:3]), int(m.group(4)))


def _python_for(version):
    """Return the minimum ``major.minor`` Python a HA release requires."""
    requires = _get(f"{PYPI}/{version}/json")["info"].get("requires_python") or ""
    m = re.search(r"3\.(\d+)", requires)
    return f"3.{m.group(1)}" if m else "3.14"


def resolve(months):
    """Collect the versions to test."""
    releases = _get(f"{PYPI}/json")["releases"]
    # Ignore yanked releases and versions with no files.
    published = [v for v, files in releases.items() if files and not all(f.get("yanked") for f in files)]
    stable = sorted((v for v in published if STABLE.match(v)), key=_key)
    betas = sorted((v for v in published if BETA.match(v)), key=_key)

    newest_per_month = {}
    for version in stable:
        year, month, _ = version.split(".")
        newest_per_month[(int(year), int(month))] = version
    recent = [newest_per_month[k] for k in sorted(newest_per_month)[-months:]]

    latest = stable[-1]
    beta = betas[-1] if betas and _key(betas[-1]) > _key(latest) else ""

    return {
        "latest": latest,
        "latest_python": _python_for(latest),
        "matrix": [{"ha": v, "python": _python_for(v)} for v in recent],
        "beta": beta,
        "beta_python": _python_for(beta) if beta else "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--months", type=int, default=3, help="monthly releases to include in the matrix")
    result = resolve(parser.parse_args().months)

    print(json.dumps(result, indent=2))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as fh:
            for name, value in result.items():
                fh.write(f"{name}={json.dumps(value) if isinstance(value, list) else value}\n")


if __name__ == "__main__":
    main()
