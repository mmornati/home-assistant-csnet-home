# Integration Testing Guide

Complete guide for testing the CSNet Home custom component in a real Home Assistant environment on your local machine.

---

## Table of Contents

- [What This Tests](#what-this-tests)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [All Available Commands](#all-available-commands)
- [Development Workflow](#development-workflow)
- [First Time Setup](#first-time-setup)
- [Testing Code Changes](#testing-code-changes)
- [Debugging](#debugging)
- [Verification](#verification)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Tips & Best Practices](#tips--best-practices)

---

## What This Tests

### 🔑 Important: Testing YOUR Local Code

This integration testing environment tests your **LOCAL development code** from `custom_components/csnet_home/`, NOT a downloaded or released version.

**You ARE testing:**
- ✅ Your current code in `custom_components/csnet_home/`
- ✅ Uncommitted changes in your working directory
- ✅ Work-in-progress features
- ✅ Code before you commit or release it

**You are NOT testing:**
- ❌ Downloaded versions
- ❌ Released versions from GitHub
- ❌ Versions from HACS
- ❌ Committed code (unless it's in your working directory)

### How It Works

The `docker-compose.yml` mounts your local directory directly into the Home Assistant container:

```yaml
volumes:
  # Your local development code is mounted here:
  - ./custom_components/csnet_home:/config/custom_components/csnet_home
```

This means:
1. Home Assistant runs inside Docker
2. It loads your local `custom_components/csnet_home/` code
3. Any changes you make are available after `make restart`
4. No need to copy files, create releases, or download anything!

---

## Prerequisites

- **Docker** and **Docker Compose** installed and running
- Your **CSNet Home account credentials** (username and password)

---

## Quick Start

### Start Testing (One Command!)

```bash
make start
```

Or:

```bash
./scripts/integration-test.sh start
```

That's it! Your local code is now running in Home Assistant at **http://localhost:8123**

---

## All Available Commands

### Using Make (Recommended)

| Command | Description |
|---------|-------------|
| `make start` | Start Home Assistant with your local code |
| `make stop` | Stop Home Assistant |
| `make restart` | Restart to apply code changes |
| `make logs` | View logs in real-time (Ctrl+C to exit) |
| `make status` | Check status and verify local code is mounted |
| `make clean` | Remove all test data and start fresh |
| `make test-unit` | Run unit tests |
| `make test-integration` | Start integration testing (alias for start) |

### Using the Script Directly

| Command | Description |
|---------|-------------|
| `./scripts/integration-test.sh start` | Start Home Assistant |
| `./scripts/integration-test.sh stop` | Stop Home Assistant |
| `./scripts/integration-test.sh restart` | Restart to apply changes |
| `./scripts/integration-test.sh logs` | Follow logs in real-time |
| `./scripts/integration-test.sh logs-tail` | Show last 100 lines of logs |
| `./scripts/integration-test.sh status` | Check status and verify code |
| `./scripts/integration-test.sh clean` | Remove all test data |
| `./scripts/integration-test.sh open` | Open browser (macOS) |
| `./scripts/integration-test.sh test` | Run unit tests first |
| `./scripts/integration-test.sh help` | Show help message |

---

## Development Workflow

### Simple Workflow

This is the typical development cycle:

```bash
# 1. Start testing environment (once)
make start

# 2. Make changes to your code
vim custom_components/csnet_home/climate.py

# 3. Apply changes
make restart

# 4. Test in browser at http://localhost:8123

# 5. Check logs if needed
make logs

# 6. Repeat steps 2-5 as needed

# 7. Stop when done
make stop
```

### What Happens Behind the Scenes

#### When you run `make start`:
1. Verifies `custom_components/csnet_home/` exists
2. Shows which files will be tested
3. Starts Home Assistant in Docker
4. Mounts YOUR local code
5. Verifies the mount was successful
6. Confirms your code is ready to test

**Output:**
```
✓ Testing LOCAL development code (version: 2.1.0)

ℹ Files being tested from: custom_components/csnet_home/
  - __init__.py
  - api.py
  - climate.py
  - config_flow.py
  - const.py
  - coordinator.py
  - sensor.py
  - water_heater.py

✓ Home Assistant is ready!
✓ Local development code is properly mounted!
```

#### When you run `make restart`:
1. Stops Home Assistant container
2. Starts it again
3. Home Assistant reloads your code
4. Your changes are now active (takes ~10 seconds)

#### When you run `make status`:
1. Shows if Home Assistant is running
2. Checks if local code is mounted
3. Shows the version from your `manifest.json`
4. Confirms you're testing local code

---

## Automated Setup (no browser)

`scripts/test_ha.py` sets up the test instance through the Home Assistant API, so the browser steps under
"First Time Setup" are optional.

1. Put your CSNet Manager login in a `.env` file at the repository root (git-ignored):

   ```
   CSNET_USERNAME=you@example.com
   CSNET_PASSWORD=your-password
   ```

2. Run `make seed`. It starts the container, creates a local test user, finishes onboarding and adds the
   integration. Re-running it is safe: finished steps are skipped.
3. Run `make states` to print every entity of the integration, or `python3 scripts/test_ha.py states` for JSON.

Notes:

- The script only talks to a test instance on this machine (`localhost`) unless you pass `--allow-remote`,
  and it never prints the credentials.
- The local test user and its token are written to `csnet-test-ha.env` inside the repository's `.git`
  directory (mode 600): git never tracks it and every worktree shares it.
- The compose project has a fixed name (`csnet-home-test`), so all checkouts and git worktrees share one
  test instance and one storage volume. `make clean` in any of them wipes it; seed again afterwards.
- If you used this setup before the project name was fixed, remove the old container once with
  `docker rm -f home-assistant-csnet-test`. Its old volume (`<folder>_ha_config`) can be deleted with
  `docker volume rm`.
- Debug logging is on in `test_config/configuration.yaml`, so `make logs` shows the CSNet responses.
  Credentials, location and account ids are redacted there; names and hardware ids are not. Use
  `python3 scripts/test_ha.py diagnostics` for a fully redacted copy.

## First Time Setup

### Step-by-Step

1. **Ensure Docker is running**

2. **Start Home Assistant:**
   ```bash
   make start
   ```

3. **Wait for it to be ready** (usually 2-3 minutes on first start)
   
   You'll see: `✓ Home Assistant is ready!`

4. **Open your browser** and go to **http://localhost:8123**

5. **Create an admin account** (only needed the first time)

6. **Add the CSNet Home integration:**
   - Go to **Configuration** → **Integrations**
   - Click **"+ Add Integration"**
   - Search for **"Hitachi CSNet Home"**
   - Enter your CSNet account credentials
   - The integration will discover and load your devices

7. **Test your integration:**
   - Verify all your devices appear
   - Test climate controls (temperature, modes)
   - Test water heater controls
   - Check sensors
   - Verify status updates

---

## Testing Code Changes

### Quick Change Test

```bash
# Make a change
vim custom_components/csnet_home/api.py

# Apply it
make restart

# Test it
# Go to http://localhost:8123
```

### Adding Debug Logs

You can add debug statements directly to your code:

```python
# In any file, e.g., custom_components/csnet_home/api.py
import logging
_LOGGER = logging.getLogger(__name__)

async def async_get_elements_data(self):
    _LOGGER.warning("DEBUG: Testing my local code changes!")
    # ... rest of your code
```

Then:
```bash
make restart
make logs
# You'll see your debug message!
```

### Testing Multiple Changes

```bash
# Start once
make start

# Then iterate quickly:
vim custom_components/csnet_home/coordinator.py
make restart
# test in browser

vim custom_components/csnet_home/sensor.py
make restart
# test in browser

vim custom_components/csnet_home/climate.py
make restart
# test in browser

# Stop when done
make stop
```

---

## Debugging

### Enable Debug Logging

For detailed logs from your integration:

1. **Edit `test_config/configuration.yaml`:**

   ```yaml
   logger:
     default: info
     logs:
       custom_components.csnet_home: debug
   ```

2. **Restart:**
   ```bash
   make restart
   ```

3. **View logs:**
   ```bash
   make logs
   ```

Now you'll see detailed debug output from your code!

### Watch Logs in Real-Time

Keep logs open in a separate terminal while developing:

**Terminal 1:**
```bash
make logs
```

**Terminal 2:**
```bash
# Make changes and restart
vim custom_components/csnet_home/api.py
make restart
```

You'll see the logs update in real-time in Terminal 1!

### Check Container Contents

Verify what's inside the running container:

```bash
# List files in the mounted directory
docker exec home-assistant-csnet-test ls -la /config/custom_components/csnet_home/

# Check the manifest version
docker exec home-assistant-csnet-test cat /config/custom_components/csnet_home/manifest.json

# Check Home Assistant logs
docker exec home-assistant-csnet-test cat /config/home-assistant.log
```

---

## Verification

### Verify Local Code is Mounted

```bash
make status
```

**Expected output:**
```
✓ Home Assistant is running
✓ Local development code is mounted (version: 2.1.0)
ℹ Location: custom_components/csnet_home/
ℹ After making code changes, restart with: make restart
```

### Verify Files are Your Local Files

```bash
# Your local file
cat custom_components/csnet_home/manifest.json

# Container file (should be identical)
docker exec home-assistant-csnet-test cat /config/custom_components/csnet_home/manifest.json
```

They should be **identical** because it's the same file (via Docker mount)!

### Verify Changes Are Applied

After making changes:

```bash
# Check timestamp of your local file
ls -la custom_components/csnet_home/api.py

# Check inside container (should match)
docker exec home-assistant-csnet-test ls -la /config/custom_components/csnet_home/api.py
```

Timestamps should match!

---

## Examples

### Example 1: Testing a Bug Fix

```bash
# 1. Start the environment
make start

# 2. Reproduce the bug in the browser
# (Go to http://localhost:8123)

# 3. Fix the bug in your code
vim custom_components/csnet_home/api.py
# Make your fix...

# 4. Apply the fix
make restart

# 5. Verify the fix works
# (Test in the browser)

# 6. Check logs for any errors
make logs

# 7. If more fixes needed, repeat steps 3-6
```

### Example 2: Testing a New Feature

```bash
# 1. Implement the feature
vim custom_components/csnet_home/climate.py
# Add your feature...

# 2. Start testing
make start

# 3. Add the integration in Home Assistant
# (http://localhost:8123)

# 4. Test the new feature

# 5. Make adjustments
vim custom_components/csnet_home/climate.py

# 6. Restart to apply changes
make restart

# 7. Test again
# Repeat steps 5-7 until perfect
```

### Example 3: Testing First-Time Setup Flow

```bash
# Start completely fresh
make clean
make start

# Go through the setup wizard
# This tests your config_flow.py changes

# Test with your CSNet credentials
# Verify device discovery works
# Check all entities are created correctly
```

### Example 4: Testing with Debug Logs

```bash
# 1. Add debug log to your code
vim custom_components/csnet_home/__init__.py
# Add: _LOGGER.warning("TESTING: My custom code is running!")

# 2. Enable debug logging
vim test_config/configuration.yaml
# Uncomment the logger section

# 3. Start or restart
make restart

# 4. Watch for your log message
make logs | grep "TESTING"
# You should see your message!
```

---

## Troubleshooting

### Home Assistant Won't Start

```bash
# Check the logs
make logs

# Common issues:
# - Port 8123 already in use
# - Docker not running
# - Invalid configuration.yaml syntax
```

**Fix port conflict:**
Edit `docker-compose.yml`:
```yaml
ports:
  - "8124:8123"  # Use 8124 instead
```

Then access at http://localhost:8124

### Integration Not Showing Up

```bash
# 1. Verify component is mounted
docker exec home-assistant-csnet-test ls -la /config/custom_components/csnet_home

# 2. Check manifest.json is valid
cat custom_components/csnet_home/manifest.json

# 3. Restart Home Assistant
make restart

# 4. Check logs for errors
make logs
```

### Changes Not Taking Effect

**Problem:** You edited code but don't see changes

**Solution:**
```bash
# ALWAYS restart after code changes
make restart

# If still not working, do a clean restart
make stop
make start

# Or completely fresh start
make clean
make start
```

### Port Already in Use

**Error:** `port is already allocated`

**Solution:**
1. Edit `docker-compose.yml`
2. Change the port:
   ```yaml
   ports:
     - "8124:8123"  # Use 8124 or any other free port
   ```
3. Restart: `make start`
4. Access at: http://localhost:8124

### Docker Not Running

**Error:** `Cannot connect to Docker daemon`

**Solution:**
1. Start Docker Desktop (macOS/Windows)
2. Or start Docker service (Linux): `sudo systemctl start docker`
3. Try again: `make start`

### Can't Access Home Assistant

**Problem:** Container runs but http://localhost:8123 doesn't work

**Solution:**
```bash
# Check if container is running
docker ps | grep home-assistant-csnet-test

# Check container logs
make logs

# Wait longer (first start takes 2-3 minutes)

# Check from inside container
docker exec home-assistant-csnet-test curl -s http://localhost:8123
```

---

## Advanced Usage

### Running Unit Tests Before Integration Testing

```bash
# Run unit tests first
make test-unit

# If they pass, start integration testing
make start
```

Or use the script:
```bash
./scripts/integration-test.sh test
# This runs unit tests and stops if they fail
```

### Accessing from Another Machine

To access the test instance from other machines on your network:

1. **Edit `test_config/configuration.yaml`:**

   ```yaml
   http:
     server_host: 0.0.0.0  # Allow all connections
   ```

2. **Restart:**
   ```bash
   make restart
   ```

3. **Find your IP:**
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "
   
   # Or
   hostname -I
   ```

4. **Access from other machines:**
   ```
   http://<your-ip>:8123
   ```

### Using in CI/CD Pipelines

Example for automated testing:

```bash
# Start Home Assistant
make start

# Wait for it to be ready
timeout 180 bash -c 'until curl -sf http://localhost:8123 > /dev/null; do sleep 2; done'

# Run your automated tests here
# ...

# Clean up
make stop
make clean
```

### Custom Configuration

You can modify `test_config/configuration.yaml` to:
- Add test automations
- Configure additional test integrations
- Adjust recorder settings
- Add test devices/entities

After changes:
```bash
make restart
```

---

## Tips & Best Practices

### 1. Use `make restart` Liberally

Don't be afraid to restart frequently. It only takes ~10 seconds:

```bash
# Make a small change
vim custom_components/csnet_home/climate.py

# Test it immediately
make restart
```

### 2. Keep Logs Open

Keep logs running in a separate terminal for instant feedback:

```bash
# Terminal 1
make logs

# Terminal 2
# Make changes, restart, watch Terminal 1 for results
```

### 3. Test with Real Devices

Use your actual CSNet Home credentials to test with real devices. This catches issues that mocks might miss.

### 4. Test the Setup Flow

Before releasing, always test the first-time setup:

```bash
make clean
make start
# Go through the complete setup wizard
```

### 5. Verify Your Changes Are Active

Add a temporary log to confirm:

```python
_LOGGER.warning(f"TESTING: My code version {VERSION} is running!")
```

You should see this in logs after `make restart`.

### 6. Test Error Conditions

Test how your code handles errors:
- Wrong credentials
- Network issues (disconnect your internet briefly)
- API errors
- Invalid data

### 7. Check All Entity Types

Make sure to test:
- Climate entities (all modes and presets)
- Water heater entity
- All sensors
- State updates

### 8. Use Clean Start for Setup Testing

```bash
# Test first-time setup flow
make clean
make start

# Test upgrade scenarios
# (Don't clean, just restart with new code)
make restart
```

---

## What Gets Tested

Integration testing allows you to verify:

- ✅ **Config Flow**: Setup wizard works correctly
- ✅ **API Connection**: Authentication with CSNet servers
- ✅ **Device Discovery**: All your devices are discovered
- ✅ **Climate Controls**: Temperature, modes, presets work
- ✅ **Water Heater**: DHW controls work
- ✅ **Sensors**: All sensor values are correct and update
- ✅ **State Updates**: Data refresh cycle works
- ✅ **Error Handling**: Connection errors handled gracefully
- ✅ **UI Integration**: Everything looks good in Home Assistant UI
- ✅ **Real Devices**: Test with your actual Hitachi equipment!

---

## File Structure

```
home-assistant-csnet-hitachi/
├── custom_components/csnet_home/    # Your integration code (THIS IS WHAT YOU'RE TESTING)
│   ├── __init__.py
│   ├── api.py
│   ├── climate.py
│   ├── config_flow.py
│   ├── const.py
│   ├── coordinator.py
│   ├── manifest.json
│   ├── sensor.py
│   └── water_heater.py
├── test_config/                      # Test Home Assistant configuration
│   ├── configuration.yaml           # Main HA config
│   ├── automations.yaml
│   ├── scripts.yaml
│   ├── scenes.yaml
│   └── .storage/                    # HA internal data (auto-generated, gitignored)
├── scripts/
│   └── integration-test.sh          # Integration testing script
├── docker-compose.yml               # Docker setup
└── Makefile                         # Convenient shortcuts
```

---

## Comparison: Before vs After

### Before (Manual Process)
1. Copy files to production Home Assistant server
2. Restart production Home Assistant
3. Hope nothing breaks
4. If broken, fix and repeat
5. **Risk of breaking production system**
6. **Slow iteration cycle**

### After (Automated Testing)
1. Run `make start` once
2. Edit code locally
3. Run `make restart` (10 seconds)
4. Test immediately
5. **No risk to production**
6. **Fast iteration cycle!**

---

## Summary

### Quick Command Reference

| Task | Command |
|------|---------|
| Start testing | `make start` |
| Apply code changes | `make restart` |
| View logs | `make logs` |
| Check status | `make status` |
| Stop testing | `make stop` |
| Clean everything | `make clean` |

### Remember

- ✅ You're ALWAYS testing your LOCAL code
- ✅ NO need to commit, release, or download
- ✅ Just edit and `make restart`
- ✅ Fast, safe, isolated testing
- ✅ Test with real devices

---

## Questions or Issues?

If you encounter problems with the integration testing setup:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Run `./scripts/integration-test.sh help` for command help
3. Check `make logs` for error messages
4. Open an issue on GitHub if you find a bug

---

**Happy Testing!** 🚀

Your local development code is ready to test immediately with `make start`!
