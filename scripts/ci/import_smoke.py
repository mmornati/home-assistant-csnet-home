#!/usr/bin/env python3
"""Import every integration module against the installed Home Assistant.

Runs without the test harness, so it works on HA betas too. It catches removed
HA APIs and Python packages HA no longer ships (e.g. ``async_timeout``).
Exits non-zero on the first failure.
"""

import importlib
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from homeassistant.const import __version__ as ha_version  # noqa: E402

PACKAGE = "custom_components.csnet_home"


def main():
    package_path = ROOT / PACKAGE.replace(".", "/")
    modules = [PACKAGE] + [f"{PACKAGE}.{m.name}" for m in pkgutil.iter_modules([str(package_path)])]

    failed = []
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"ok   {name}")
        except Exception as err:  # pylint: disable=broad-except
            print(f"FAIL {name}: {type(err).__name__}: {err}")
            failed.append(name)

    if failed:
        print(f"\n{len(failed)} module(s) failed to import on Home Assistant {ha_version}")
        sys.exit(1)
    print(f"\nAll {len(modules)} modules import on Home Assistant {ha_version}")


if __name__ == "__main__":
    main()
