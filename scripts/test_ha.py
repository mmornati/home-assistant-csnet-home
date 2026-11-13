#!/usr/bin/env python3
"""Drive the local test Home Assistant (docker-compose.yml) without a browser.

Commands:
  seed    Onboard the test instance and add the CSNet Home integration.
          CSNet credentials are read from a .env file (CSNET_USERNAME,
          CSNET_PASSWORD); they are sent only to the local test instance and
          are never printed. Safe to re-run: finished steps are skipped.
  states  Print the state of every csnet_home entity as JSON.
  diagnostics
          Print the integration's diagnostics download: the redacted data it
          last received from CSNet Manager, to compare entity values against.
  status  Say what is set up (onboarding, integration, entity count).

The local test user and its refresh token are stored in the repository's git
directory (csnet-test-ha.env, mode 600), which git never tracks and every
worktree shares. Only the standard library is used.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DOMAIN = "csnet_home"
DEFAULT_URL = "http://localhost:8123"
TEST_ENV_NAME = "csnet-test-ha.env"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
TEST_USER = "csnet-test"
REPO_ROOT = Path(__file__).resolve().parent.parent


class TestHaError(Exception):
    """A step failed in a way the user has to look at."""


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------


def git_common_dir() -> Path | None:
    """Return the repository's shared .git directory (the same for every worktree)."""
    try:
        common = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = (REPO_ROOT / common_path).resolve()
    return common_path if common_path.is_dir() else None


def test_env_file() -> Path:
    """Return where the test-instance values live: never inside the work tree."""
    common = git_common_dir()
    if common is None:
        raise TestHaError("Not inside a git checkout: cannot pick a safe place for the test-instance token.")
    return common / TEST_ENV_NAME


def find_env_file(explicit: str | None) -> Path | None:
    """Return the .env file: explicit path, this checkout, or the main checkout."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    candidates = [REPO_ROOT / ".env"]
    common = git_common_dir()
    if common is not None:
        # A worktree shares the main checkout's .env.
        candidates.append(common.parent / ".env")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def read_env(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines. Values are never logged."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def write_test_env(path: Path, values: dict[str, str]) -> None:
    """Write the test-instance values with owner-only permissions."""
    lines = ["# Local test Home Assistant only. Written by scripts/test_ha.py."]
    lines += [f"{key}={value}" for key, value in sorted(values.items())]
    # Create the file owner-only from the start, not world-readable then chmod.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.chmod(path, 0o600)


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


class Client:
    """Tiny Home Assistant REST client."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = self.base_url + "/"
        self.access_token: str | None = None

    def request(self, method: str, path: str, *, body=None, form=None, auth: bool = True):
        """Send a request and return (status, parsed body)."""
        headers = {}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        elif form is not None:
            data = urllib.parse.urlencode(form).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        req = urllib.request.Request(self.base_url + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status, raw = resp.status, resp.read()
        except urllib.error.HTTPError as err:
            status, raw = err.code, err.read()
        text = raw.decode("utf-8", errors="replace")
        try:
            return status, json.loads(text) if text else None
        except json.JSONDecodeError:
            return status, text

    def wait_ready(self, timeout: int) -> None:
        """Wait until the HTTP API answers."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                status, _ = self.request("GET", "/api/onboarding", auth=False)
                if status in (200, 404):
                    return
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                pass
            time.sleep(3)
        raise TestHaError(f"Home Assistant did not answer at {self.base_url} within {timeout}s. Start it with: make start")

    def login_with_refresh_token(self, refresh_token: str) -> bool:
        """Exchange the stored refresh token for an access token."""
        status, data = self.request(
            "POST",
            "/auth/token",
            form={"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": self.client_id},
            auth=False,
        )
        if status == 200 and isinstance(data, dict) and data.get("access_token"):
            self.access_token = data["access_token"]
            return True
        return False


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------


def pending_onboarding_steps(client: Client) -> list[str]:
    """Return onboarding steps not done yet (empty once onboarding is over)."""
    status, data = client.request("GET", "/api/onboarding", auth=False)
    if status == 404:  # the view is removed once onboarding is complete
        return []
    if status != 200 or not isinstance(data, list):
        raise TestHaError(f"Unexpected answer from /api/onboarding: HTTP {status}")
    return [step["step"] for step in data if not step.get("done")]


def onboard(client: Client, test_env_path: Path, test_env: dict[str, str]) -> None:
    """Create the local user and finish onboarding."""
    pending = pending_onboarding_steps(client)

    if "user" in pending:
        password = secrets.token_urlsafe(24)
        status, data = client.request(
            "POST",
            "/api/onboarding/users",
            body={"client_id": client.client_id, "name": "CSNet Test", "username": TEST_USER, "password": password, "language": "en"},
            auth=False,
        )
        if status != 200 or not isinstance(data, dict) or "auth_code" not in data:
            raise TestHaError(f"Creating the local test user failed: HTTP {status}")
        status, tokens = client.request(
            "POST",
            "/auth/token",
            form={"grant_type": "authorization_code", "code": data["auth_code"], "client_id": client.client_id},
            auth=False,
        )
        if status != 200 or not isinstance(tokens, dict) or "access_token" not in tokens or "refresh_token" not in tokens:
            raise TestHaError(f"Token exchange failed: HTTP {status}. Wipe the test instance with 'make clean' and seed again.")
        client.access_token = tokens["access_token"]
        test_env.update(
            {
                "HA_TEST_URL": client.base_url,
                "HA_TEST_USERNAME": TEST_USER,
                "HA_TEST_PASSWORD": password,
                "HA_TEST_REFRESH_TOKEN": tokens["refresh_token"],
            }
        )
        write_test_env(test_env_path, test_env)
        print(f"  created local user '{TEST_USER}' (details in {test_env_path})")
        pending.remove("user")
    else:
        authenticate(client, test_env)
        print("  local user already exists")

    for step in ("core_config", "analytics"):
        if step in pending:
            status, _ = client.request("POST", f"/api/onboarding/{step}", body={})
            if status != 200:
                raise TestHaError(f"Onboarding step '{step}' failed: HTTP {status}")
    if "integration" in pending:
        status, _ = client.request(
            "POST",
            "/api/onboarding/integration",
            body={"client_id": client.client_id, "redirect_uri": client.client_id},
        )
        if status != 200:
            raise TestHaError(f"Onboarding step 'integration' failed: HTTP {status}")
    print("  onboarding complete")


def authenticate(client: Client, test_env: dict[str, str]) -> None:
    """Log in to the test instance with the stored refresh token."""
    token = test_env.get("HA_TEST_REFRESH_TOKEN")
    if not token or not client.login_with_refresh_token(token):
        raise TestHaError(
            "The test instance is already onboarded but no valid token is stored. Wipe it with 'make clean' and run the seed again. "
            f"(Tokens are tied to the URL used at seed time: {test_env.get('HA_TEST_URL', 'unknown')}.)"
        )


def integration_entries(client: Client) -> list[dict]:
    """Return the csnet_home config entries."""
    status, data = client.request("GET", f"/api/config/config_entries/entry?domain={DOMAIN}")
    if status != 200 or not isinstance(data, list):
        raise TestHaError(f"Listing config entries failed: HTTP {status}")
    return data


def add_integration(client: Client, env_file: Path | None, scan_interval: int | None) -> None:
    """Run the csnet_home config flow with the credentials from .env."""
    if integration_entries(client):
        print("  integration already configured")
        return
    if env_file is None:
        raise TestHaError("No .env file found. Create one with CSNET_USERNAME and CSNET_PASSWORD, or pass --env-file.")
    creds = read_env(env_file)
    username, password = creds.get("CSNET_USERNAME"), creds.get("CSNET_PASSWORD")
    if not username or not password:
        raise TestHaError(f"{env_file} must define CSNET_USERNAME and CSNET_PASSWORD.")

    status, flow = client.request("POST", "/api/config/config_entries/flow", body={"handler": DOMAIN, "show_advanced_options": False})
    if status != 200 or not isinstance(flow, dict) or flow.get("type") != "form" or "flow_id" not in flow:
        detail = f"type={flow.get('type')}, reason={flow.get('reason')}" if isinstance(flow, dict) else "no details"
        raise TestHaError(f"Starting the config flow failed: HTTP {status} ({detail}). Is custom_components/{DOMAIN} mounted?")

    user_input: dict[str, object] = {"username": username, "password": password}
    if scan_interval is not None:
        user_input["scan_interval"] = scan_interval
    status, result = client.request("POST", f"/api/config/config_entries/flow/{flow['flow_id']}", body=user_input)
    if status == 200 and isinstance(result, dict) and result.get("type") == "create_entry":
        print("  integration added")
        return
    # Never echo the submitted input: report only what Home Assistant says.
    errors = result.get("errors") if isinstance(result, dict) else None
    client.request("DELETE", f"/api/config/config_entries/flow/{flow['flow_id']}")  # do not leave the flow open
    raise TestHaError(f"The config flow did not create an entry (HTTP {status}, errors: {errors}).")


def csnet_states(client: Client) -> list[dict]:
    """Return state objects of every entity that belongs to csnet_home."""
    status, rendered = client.request("POST", "/api/template", body={"template": "{{ integration_entities('" + DOMAIN + "') | tojson }}"})
    if status != 200:
        raise TestHaError(f"Listing integration entities failed: HTTP {status}")
    entity_ids = set(json.loads(rendered) if isinstance(rendered, str) else rendered)
    status, states = client.request("GET", "/api/states")
    if status != 200 or not isinstance(states, list):
        raise TestHaError(f"Reading states failed: HTTP {status}")
    return sorted((s for s in states if s["entity_id"] in entity_ids), key=lambda s: s["entity_id"])


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def cmd_seed(args, client: Client, env_file: Path | None, test_env_path: Path, test_env: dict[str, str]) -> None:
    print(f"Waiting for Home Assistant at {client.base_url} ...")
    client.wait_ready(args.wait)
    print("Onboarding:")
    onboard(client, test_env_path, test_env)
    if args.skip_integration:
        print("Integration: skipped (--skip-integration)")
        return
    print("Integration:")
    add_integration(client, env_file, args.scan_interval)
    states: list[dict] = []
    entry_state = None
    for _ in range(40):  # setup and first poll
        entries = integration_entries(client)
        entry_state = entries[0].get("state") if entries else None
        states = csnet_states(client)
        if entry_state == "loaded" and states:
            break
        time.sleep(3)
    if entry_state != "loaded" or not states:
        raise TestHaError(f"The integration did not finish setting up (state: {entry_state}, entities: {len(states)}). Check 'make logs'.")
    print(f"  {len(states)} entities created")


def cmd_states(args, client: Client, test_env: dict[str, str]) -> None:
    client.wait_ready(args.wait)
    authenticate(client, test_env)
    states = csnet_states(client)
    if args.table:
        for state in states:
            unit = state["attributes"].get("unit_of_measurement", "")
            print(f"{state['entity_id']:<75} {state['state']} {unit}".rstrip())
        return
    slim = [{"entity_id": s["entity_id"], "state": s["state"], "attributes": s["attributes"]} for s in states]
    json.dump(slim, sys.stdout, indent=2, ensure_ascii=False)
    print()


def cmd_diagnostics(args, client: Client, test_env: dict[str, str]) -> None:
    client.wait_ready(args.wait)
    authenticate(client, test_env)
    entries = integration_entries(client)
    if not entries:
        raise TestHaError("The integration is not configured. Run the seed first.")
    status, data = client.request("GET", f"/api/diagnostics/config_entry/{entries[0]['entry_id']}")
    if status != 200 or not isinstance(data, dict):
        raise TestHaError(f"Downloading diagnostics failed: HTTP {status}")
    json.dump(data.get("data", data), sys.stdout, indent=2, ensure_ascii=False)
    print()


def cmd_status(args, client: Client, test_env: dict[str, str]) -> None:
    client.wait_ready(args.wait)
    pending = pending_onboarding_steps(client)
    print(f"onboarding: {'pending ' + ', '.join(pending) if pending else 'done'}")
    if pending:
        return
    authenticate(client, test_env)
    entries = integration_entries(client)
    print(f"integration entries: {len(entries)}" + (f" (state: {entries[0].get('state')})" if entries else ""))
    print(f"entities: {len(csnet_states(client))}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=None, help=f"Test instance URL (default: {DEFAULT_URL})")
    parser.add_argument("--env-file", default=None, help="Path to the .env with CSNET_USERNAME / CSNET_PASSWORD")
    parser.add_argument("--wait", type=int, default=300, help="Seconds to wait for Home Assistant to answer")
    parser.add_argument("--allow-remote", action="store_true", help="Allow a test instance that is not on this machine")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="Onboard the test instance and add the integration")
    seed.add_argument("--skip-integration", action="store_true", help="Only create the local user; does not read CSNet credentials")
    seed.add_argument("--scan-interval", type=int, default=None, help="Polling interval in seconds (default: integration default)")

    states = sub.add_parser("states", help="Print csnet_home entity states")
    states.add_argument("--table", action="store_true", help="One line per entity instead of JSON")

    sub.add_parser("diagnostics", help="Print the integration's redacted diagnostics download")
    sub.add_parser("status", help="Show what is set up")
    args = parser.parse_args()

    try:
        env_file = find_env_file(args.env_file)
        test_env_path = test_env_file()
        test_env = read_env(test_env_path)
        client = Client(args.url or test_env.get("HA_TEST_URL") or DEFAULT_URL)
        host = urllib.parse.urlsplit(client.base_url).hostname
        if host not in LOOPBACK_HOSTS and not args.allow_remote:
            # The seed sends the CSNet login to this URL: keep it on this machine.
            raise TestHaError(f"{client.base_url} is not a local address. Pass --allow-remote if that is intended.")
        if args.command == "seed":
            cmd_seed(args, client, None if args.skip_integration else env_file, test_env_path, test_env)
        elif args.command == "states":
            cmd_states(args, client, test_env)
        elif args.command == "diagnostics":
            cmd_diagnostics(args, client, test_env)
        else:
            cmd_status(args, client, test_env)
    except TestHaError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, OSError) as err:
        print(f"error: lost the connection to Home Assistant ({err}). Is it restarting? Try again.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
