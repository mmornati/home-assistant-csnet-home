#!/usr/bin/env python3
"""Download shared samples of real units, to replay them in the tests.

    python scripts/fetch_samples.py --list           # what is available
    python scripts/fetch_samples.py --meter          # the samples with a meter
    python scripts/fetch_samples.py --all
    pytest -m replay

Samples come from https://github.com/mmornati/csnet-home-samples and go to
tests/samples/ (not tracked by git). A file already there with the right
checksum is not downloaded again. Only the standard library is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

INDEX_URL = "https://mmornati.github.io/csnet-home-samples/index.json"
TARGET = Path(__file__).resolve().parent.parent / "tests" / "samples"


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "csnet-home-fetch-samples"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed https URLs
        return response.read()


def _matches(sample: dict, args) -> bool:
    unit = sample.get("unit_info") or {}
    if args.unit and args.unit not in sample["unit"]:
        return False
    if args.power_supply and unit.get("power_supply") != args.power_supply:
        return False
    if args.meter and sample.get("meter_kwh") is None:
        return False
    if args.defrost and not sample.get("defrosts"):
        return False
    if args.source and sample.get("source") != args.source:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="list the samples and download nothing")
    parser.add_argument("--all", action="store_true", help="every sample")
    parser.add_argument("--unit", help="units whose folder name contains this")
    parser.add_argument("--power-supply", choices=["single_phase", "three_phase"])
    parser.add_argument("--meter", action="store_true", help="only samples with a meter")
    parser.add_argument("--defrost", action="store_true", help="only samples with defrosts")
    parser.add_argument("--source", choices=["recorder", "ha-history"])
    parser.add_argument("--index", default=INDEX_URL, help="catalog to read (default: %(default)s)")
    args = parser.parse_args()

    index = json.loads(_get(args.index))
    chosen = [s for s in index["samples"] if _matches(s, args)]
    if args.list or not (args.all or args.unit or args.power_supply or args.meter or args.defrost or args.source):
        for sample in chosen:
            unit = sample.get("unit_info") or {}
            print(
                f"{sample['file']:<60} {sample['days']:>5} d  {unit.get('power_supply', '?'):<12} "
                f"meter={'yes' if sample.get('meter_kwh') is not None else 'no ':<3}  defrosts={sample.get('defrosts', 0)}"
            )
        if not args.list:
            print("\nChoose with --all, --unit, --power-supply, --meter, --defrost or --source.")
        return 0

    for sample in chosen:
        target = TARGET / sample["file"].removeprefix("samples/")
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == sample["sha256"]:
            print(f"up to date  {target.relative_to(TARGET.parent.parent)}")
            continue
        data = _get(sample["url"])
        if hashlib.sha256(data).hexdigest() != sample["sha256"]:
            print(f"checksum mismatch, skipped: {sample['url']}", file=sys.stderr)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"downloaded  {target.relative_to(TARGET.parent.parent)} ({len(data) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
