#!/usr/bin/env bash
# Fail unless every change stays inside the paths the fix workflow may touch:
# custom_components/csnet_home/ (except manifest.json) and tests/.
#
# Usage: scripts/ci/check_patch_paths.sh               check the staged changes
#        scripts/ci/check_patch_paths.sh --patch FILE  check a patch file before
#                                                      it is applied
#
# Patch mode applies the patch to a throwaway index (`git apply --cached` with
# GIT_INDEX_FILE), never to the work tree or the real index, then checks that
# index like staged mode: git itself resolves renames, copies, deletions, mode
# changes and binary files. --no-renames lists both sides of a move, so a file
# cannot be renamed in or out of the allowed paths unnoticed. Symlinks and
# submodules are refused.
#
# Workflows run a copy of this script saved before the patch exists, so the
# patch cannot change the check that validates it.

set -euo pipefail

ALLOWED='^(custom_components/csnet_home/|tests/)'
MANIFEST='custom_components/csnet_home/manifest.json'

if [ "${1:-}" = "--patch" ]; then
  PATCH="${2:?usage: check_patch_paths.sh --patch FILE}"
  PATCH=$(cd "$(dirname "$PATCH")" && pwd)/$(basename "$PATCH")
  TMP_INDEX_DIR=$(mktemp -d)
  trap 'rm -rf "$TMP_INDEX_DIR"' EXIT
  export GIT_INDEX_FILE="$TMP_INDEX_DIR/index"
  git read-tree HEAD
  # Fails on a patch git cannot parse or apply cleanly to HEAD.
  git apply --cached "$PATCH"
  # Mode 120000 is a symlink, 160000 a submodule (also caught below).
  if git apply --summary "$PATCH" | grep -Eq '(^|[ >])(120000|160000)( |$)'; then
    echo "::error::The patch adds a symlink or submodule"
    exit 1
  fi
fi

# Paths with unusual characters are quoted by git, which the allowlist refuses.
PATHS=$(git diff --cached --no-renames --name-only HEAD)
if git diff --cached --no-renames --raw HEAD | awk '{print $1, $2}' | grep -Eq '(^|[ :])(120000|160000)'; then
  echo "::error::The patch adds a symlink or submodule"
  exit 1
fi

OUTSIDE=$(printf '%s\n' "$PATHS" | grep -v '^$' | grep -Ev "$ALLOWED" || true)
# Refuse ".." components outright rather than reason about them.
ODD=$(printf '%s\n' "$PATHS" | grep -E '(^|/)\.\.(/|$)' || true)
if [ -n "$OUTSIDE" ] || [ -n "$ODD" ] || printf '%s\n' "$PATHS" | grep -qx "$MANIFEST"; then
  BLOCKED=$(printf '%s\n' "$OUTSIDE" "$ODD" "$(printf '%s\n' "$PATHS" | grep -x "$MANIFEST" || true)" | grep -v '^$' | sort -u | tr '\n' ' ')
  echo "::error::Changes outside the allowed paths: ${BLOCKED}"
  exit 1
fi
echo "Patch paths OK: $(printf '%s\n' "$PATHS" | grep -vc '^$') file(s)"
