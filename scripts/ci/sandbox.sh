#!/usr/bin/env bash
# Run code Claude wrote (tests, integration modules) as an unprivileged user with
# no network, so it cannot read the API key from the environment of the process
# that started it (/proc/<pid>/environ is readable only by the same user), write
# the runner's files ($GITHUB_OUTPUT, the workspace) or reach the internet.
#
# Usage: scripts/ci/sandbox.sh setup        create the user, grant read access to
#                                           the workspace, check the isolation
#        scripts/ci/sandbox.sh run CMD...   run CMD in the sandbox
#        scripts/ci/sandbox.sh cleanup      kill what the sandbox left running
#
# Needs passwordless sudo (GitHub-hosted Ubuntu runners), unshare, runuser and
# ip (iproute2).
# `run` passes only PATH, LD_LIBRARY_PATH (setup-python), LANG and a private
# HOME/TMPDIR: the sandbox user can read the workspace and the Python install,
# and write only to its own temporary directory. Run the workflow's copy of this
# script saved before any Claude-written code exists, not the workspace's.

set -euo pipefail

SANDBOX_USER=angelia-sandbox
SANDBOX_HOME=/tmp/angelia-sandbox

run() {
  local env=(PATH="$PATH" HOME="$SANDBOX_HOME" TMPDIR="$SANDBOX_HOME" LANG=C.UTF-8 PYTHONDONTWRITEBYTECODE=1)
  if [ -n "${LD_LIBRARY_PATH:-}" ]; then
    env+=(LD_LIBRARY_PATH="$LD_LIBRARY_PATH")
  fi
  # The new network namespace has only its own loopback, brought up for tests
  # that serve on 127.0.0.1 (aiohttp test server, websocket client): no route
  # out, and not the host's loopback services.
  # shellcheck disable=SC2016 # expanded by the inner shell
  exec sudo -n /usr/bin/unshare --net -- /bin/sh -c \
    '/usr/sbin/ip link set lo up && exec /usr/sbin/runuser -u "$0" -- "$@"' \
    "$SANDBOX_USER" /usr/bin/env -i "${env[@]}" "$@"
}

setup() {
  local workspace="${GITHUB_WORKSPACE:-$PWD}" dir
  if ! id -u "$SANDBOX_USER" > /dev/null 2>&1; then
    sudo -n useradd --system --no-create-home --shell /usr/sbin/nologin "$SANDBOX_USER"
  fi
  sudo -n install -d -o "$SANDBOX_USER" -g "$SANDBOX_USER" -m 700 "$SANDBOX_HOME"
  if ! command -v setfacl > /dev/null; then
    sudo -n apt-get install -y -qq acl > /dev/null
  fi
  # Traverse (not list) the parents of the workspace, read the workspace. The
  # default ACL makes files Claude creates later readable too.
  dir=$(dirname "$workspace")
  while [ "$dir" != / ]; do
    sudo -n setfacl -m "u:${SANDBOX_USER}:x" "$dir"
    dir=$(dirname "$dir")
  done
  sudo -n setfacl -R -m "u:${SANDBOX_USER}:rX" "$workspace"
  sudo -n find "$workspace" -type d -exec setfacl -d -m "u:${SANDBOX_USER}:rX" {} +
  # Traversing the runner's home must not open its other files (runner config,
  # _actions, _diag, dotfiles): every sibling along the path from $HOME down to
  # the workspace gets an explicit no-access entry, except the Python install
  # the sandbox runs (setup-python or a venv may live under the home).
  local python_dirs keep sibling
  python_dirs=$(python3 -c 'import sys; print(sys.prefix); print(sys.base_prefix)')
  if [ -n "${HOME:-}" ] && [ "$HOME" != / ]; then
    dir=$(dirname "$workspace")
    while [ "${dir#"$HOME"}" != "$dir" ] || [ "$dir" = "$HOME" ]; do
      for sibling in "$dir"/* "$dir"/.[!.]* "$dir"/..?*; do
        [ -e "$sibling" ] || continue
        case "$workspace/" in "$sibling"/*) continue ;; esac
        keep=no
        while IFS= read -r p; do
          case "$p/" in "$sibling"/*) keep=yes ;; esac
        done <<< "$python_dirs"
        [ "$keep" = yes ] && continue
        sudo -n setfacl -m "u:${SANDBOX_USER}:---" "$sibling"
      done
      [ "$dir" = "$HOME" ] && break
      dir=$(dirname "$dir")
    done
  fi
  # The runner's temp dir sits next to the workspace and holds the step
  # scripts, $GITHUB_OUTPUT/$GITHUB_ENV and the artifacts: a named ACL entry
  # with no permissions overrides the "other" bits for the sandbox user.
  if [ -n "${RUNNER_TEMP:-}" ]; then
    sudo -n setfacl -m "u:${SANDBOX_USER}:---" "$RUNNER_TEMP"
  fi

  # Fail closed if the isolation does not hold.
  if [ "$("$0" run /usr/bin/id -u)" = "$(id -u)" ]; then
    echo "::error::The sandbox runs as the runner user"; exit 1
  fi
  # Fail closed: only an explicit "blocked" answer counts, not a missing Python.
  local net
  net=$("$0" run python3 -c '
import socket
try:
    socket.create_connection(("1.1.1.1", 443), 5)
    print("open")
except OSError:
    print("blocked")' 2> /dev/null || true)
  if [ "$net" != blocked ]; then
    echo "::error::The sandbox network check did not report blocked (${net:-no answer})"; exit 1
  fi
  if "$0" run /usr/bin/touch "$workspace/.sandbox-write-test" 2> /dev/null; then
    rm -f "$workspace/.sandbox-write-test"
    echo "::error::The sandbox can write the workspace"; exit 1
  fi
  if "$0" run /usr/bin/cat "/proc/$$/environ" > /dev/null 2>&1; then
    echo "::error::The sandbox can read the runner's process environment"; exit 1
  fi
  if [ -n "${HOME:-}" ] && "$0" run /usr/bin/ls -A "$HOME" > /dev/null 2>&1; then
    echo "::error::The sandbox can list the runner's home directory"; exit 1
  fi
  for f in "${HOME:-/nonexistent}"/.gitconfig "${HOME:-/nonexistent}"/runners "${HOME:-/nonexistent}"/actions-runner; do
    if [ -e "$f" ] && "$0" run /usr/bin/test -r "$f" 2> /dev/null; then
      echo "::error::The sandbox can read ${f}"; exit 1
    fi
  done
  for file in "${GITHUB_OUTPUT:-}" "${GITHUB_ENV:-}" "${GITHUB_PATH:-}" "${GITHUB_STEP_SUMMARY:-}"; do
    if [ -n "$file" ] && "$0" run /usr/bin/test -e "$file" 2> /dev/null; then
      echo "::error::The sandbox can reach ${file}"; exit 1
    fi
  done
  echo "Sandbox ready: user ${SANDBOX_USER}, no network, read-only workspace"
}

case "${1:-}" in
  setup) setup ;;
  run)
    shift
    [ "$#" -gt 0 ] || { echo "usage: sandbox.sh run CMD..." >&2; exit 2; }
    run "$@"
    ;;
  cleanup) sudo -n pkill -KILL -u "$SANDBOX_USER" || true ;;
  *) echo "usage: sandbox.sh setup | run CMD... | cleanup" >&2; exit 2 ;;
esac
