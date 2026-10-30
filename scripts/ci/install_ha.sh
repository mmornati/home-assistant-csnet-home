#!/usr/bin/env bash
# Install an exact Home Assistant version for CI and fail if pip picked another.
#
# Usage: scripts/ci/install_ha.sh <ha_version> [runtime|tests]
#
#   runtime  HA only (enough for import smoke tests). Default.
#   tests    HA plus the matching pytest-homeassistant-custom-component.
#            That package pins an exact HA version and is usually published a
#            day or so after a HA release. Until it exists this prints
#            "harness=pending" to $GITHUB_OUTPUT and exits 0 instead of letting
#            pip fall back to an ancient harness or a different HA version.

set -euo pipefail

HA_VERSION="${1:?usage: install_ha.sh <ha_version> [runtime|tests]}"
MODE="${2:-runtime}"
OUTPUT="${GITHUB_OUTPUT:-/dev/null}"

python -m pip install --upgrade pip

if [ "$MODE" = "tests" ]; then
  # The newest harness pins the newest HA it supports. If the requested HA is
  # newer, no harness exists yet: say so now instead of letting pip backtrack
  # through hundreds of harness releases before failing.
  HARNESS_HA=$(python - <<'EOF'
import json, re, urllib.request
url = "https://pypi.org/pypi/pytest-homeassistant-custom-component/json"
with urllib.request.urlopen(url, timeout=30) as resp:  # nosec B310 - fixed https URL
    reqs = json.load(resp)["info"]["requires_dist"] or []
print(next((m.group(1) for r in reqs if (m := re.match(r"homeassistant==(\S+)", r))), ""))
EOF
  )
  NEWEST=$(printf '%s\n%s\n' "$HARNESS_HA" "$HA_VERSION" | sort -V | tail -1)
  if [ -n "$HARNESS_HA" ] && [ "$HARNESS_HA" != "$HA_VERSION" ] && [ "$NEWEST" = "$HA_VERSION" ]; then
    echo "::warning::pytest-homeassistant-custom-component supports up to HA ${HARNESS_HA}; unit tests for ${HA_VERSION} skipped until it is published"
    echo "harness=pending" >> "$OUTPUT"
    python -m pip install "homeassistant==${HA_VERSION}"
  elif ! python -m pip install \
      "homeassistant==${HA_VERSION}" \
      "pytest-homeassistant-custom-component>=0.13" \
      pytest-asyncio pytest-cov; then
    echo "::warning::No pytest-homeassistant-custom-component release for HA ${HA_VERSION} yet; unit tests skipped"
    echo "harness=pending" >> "$OUTPUT"
    python -m pip install "homeassistant==${HA_VERSION}"
  else
    echo "harness=ready" >> "$OUTPUT"
  fi
else
  python -m pip install "homeassistant==${HA_VERSION}"
fi

INSTALLED=$(python -c 'from homeassistant.const import __version__; print(__version__)')
if [ "$INSTALLED" != "$HA_VERSION" ]; then
  echo "::error::Requested Home Assistant ${HA_VERSION} but ${INSTALLED} is installed"
  exit 1
fi
echo "Installed Home Assistant ${INSTALLED}"
