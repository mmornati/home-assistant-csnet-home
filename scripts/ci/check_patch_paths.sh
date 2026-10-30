#!/usr/bin/env bash
# Fail unless every staged change stays inside the paths the fix workflow may
# touch: custom_components/csnet_home/ (except manifest.json) and tests/.
#
# --no-renames lists both sides of a move, so a file cannot be renamed in or
# out of the allowed paths unnoticed; symlinks and submodules are refused.

set -euo pipefail

ALLOWED='^(custom_components/csnet_home/|tests/)'
MANIFEST='custom_components/csnet_home/manifest.json'

PATHS=$(git diff --cached --no-renames --name-only)
OUTSIDE=$(printf '%s\n' "$PATHS" | grep -v '^$' | grep -Ev "$ALLOWED" || true)
if [ -n "$OUTSIDE" ] || printf '%s\n' "$PATHS" | grep -qx "$MANIFEST"; then
  BLOCKED=$(printf '%s\n' "$OUTSIDE" "$(printf '%s\n' "$PATHS" | grep -x "$MANIFEST" || true)" | grep -v '^$' | tr '\n' ' ')
  echo "::error::Changes outside the allowed paths: ${BLOCKED}"
  exit 1
fi
# Mode 120000 is a symlink, 160000 a submodule.
if git diff --cached --no-renames --raw | awk '{print $1, $2}' | grep -Eq '(^|[ :])(120000|160000)'; then
  echo "::error::The patch adds a symlink or submodule"
  exit 1
fi
echo "Patch paths OK: $(printf '%s\n' "$PATHS" | grep -vc '^$') file(s)"
