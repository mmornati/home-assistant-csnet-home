![logo](./docs/images/logo.png)

# Hitachi CSNet Home Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/mmornati/home-assistant-csnet-home.svg?style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/mmornati/home-assistant-csnet-home?label=Last%20Release&style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home)
[![GitHub Commit Activity](https://img.shields.io/github/commit-activity/y/mmornati/home-assistant-csnet-home.svg?style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home/commits/main)
[![GitHub last commit](https://img.shields.io/github/last-commit/mmornati/home-assistant-csnet-home?style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/mmornati/home-assistant-csnet-home/validate.yaml?branch=main&style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home)
[![License](https://img.shields.io/github/license/mmornati/home-assistant-csnet-home.svg?style=for-the-badge)](LICENSE)

A custom Home Assistant integration to control Hitachi heat pumps and air conditioning systems using the ATW-IOT-01 module through the CSNet Manager cloud service.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
  - [HACS (Recommended)](#hacs-recommended)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Climate Entities](#climate-entities)
  - [Water Heater Entity](#water-heater-entity)
  - [Sensors](#sensors)
- [Troubleshooting](#troubleshooting)
- [Developer Guide](#developer-guide)
  - [Development Setup](#development-setup)
  - [Running Tests](#running-tests)
  - [Workflow Testing](#workflow-testing)
  - [End-to-End Testing](#end-to-end-testing)
  - [Code Formatting](#code-formatting)
- [Known Limitations](#known-limitations)
- [Contributing](#contributing)
- [Documentation](#documentation)
- [License](#license)

---

## 📚 Documentation

**Complete user documentation is available at:** 

### 👉 **[https://mmornati.github.io/home-assistant-csnet-home](https://mmornati.github.io/home-assistant-csnet-home)**

The documentation includes:
- 📖 **[Installation Guide](https://mmornati.github.io/home-assistant-csnet-home/wiki/Installation-Guide/)** - Step-by-step installation (HACS, manual, from source)
- ⚙️ **[Configuration Guide](https://mmornati.github.io/home-assistant-csnet-home/wiki/Configuration-Guide/)** - Initial setup and configuration
- 🌡️ **[Climate Control](https://mmornati.github.io/home-assistant-csnet-home/wiki/Climate-Control/)** - Complete climate entity guide with examples
- 💧 **[Water Heater Control](https://mmornati.github.io/home-assistant-csnet-home/wiki/Water-Heater-Control/)** - DHW management
- 📊 **[Sensors Reference](https://mmornati.github.io/home-assistant-csnet-home/wiki/Sensors-Reference/)** - Complete sensor catalog
- 🚀 **[Advanced Features](https://mmornati.github.io/home-assistant-csnet-home/wiki/Advanced-Features/)** - Silent mode, fan control, OTC
- 🏠 **[Multi-Zone Configuration](https://mmornati.github.io/home-assistant-csnet-home/wiki/Multi-Zone-Configuration/)** - C1/C2 setup guide
- 🔧 **[Troubleshooting](https://mmornati.github.io/home-assistant-csnet-home/wiki/Troubleshooting/)** - Solutions to common issues
- ❓ **[FAQ](https://mmornati.github.io/home-assistant-csnet-home/wiki/FAQ/)** - Frequently asked questions

> 💡 **Quick Start:** New to the integration? Start with the [Installation Guide](https://mmornati.github.io/home-assistant-csnet-home/wiki/Installation-Guide/) and then follow the [Configuration Guide](https://mmornati.github.io/home-assistant-csnet-home/wiki/Configuration-Guide/).

---

## Overview

As Hitachi [explains](https://device.report/manual/12211094), the ATW-IOT-01 device has replaced the older Hi-Kumo system. This change blocked previous integration methods for retrieving data and controlling Hitachi devices through Home Assistant.

This custom integration solves that problem by connecting directly to the CSNet Manager cloud service, enabling full control of your Hitachi climate systems from Home Assistant.

**Supported Devices:**
- Hitachi heat pumps with ATW-IOT-01 module
- Multi-zone climate systems
- Domestic Hot Water (DHW) heaters

> 📋 **See [SUPPORTED_DEVICES.md](docs/SUPPORTED_DEVICES.md)** for detailed device compatibility matrix and community testing results

---

## Features

### Climate Control
- **Climate entities per zone** with full Home Assistant integration:
  - HVAC modes: `off`, `heat`, `cool`
  - Presets: `comfort`, `eco` (mapped from `ecocomfort`)
  - Target temperature control with dynamic limits based on device type
  - On/Off support
  - Action reporting: `heating`, `cooling`, `idle`
  - Extended attributes: `real_mode`, `operation_status`, `timer_running`, `alarm_code`, `c1_demand`, `c2_demand`, `doingBoost`
  - **Temperature Limits** (automatically detected):
    - Air circuits (standard heat pumps): 8-35°C
    - Water circuits (Yutaki/Hydro systems): 20-80°C
    - Optional manual override available in configuration

### Water Heater
- **DHW (Domestic Hot Water)** entity with:
  - Temperature control (30-80°C)
  - Operation modes: `off`, `eco`, `performance`
  - Optional maximum temperature override

### Sensors
- Temperature sensors (current and target)
- State and status sensors
- Alarm monitoring with persistent notifications
- Extended device information

> **Note:** Mode and preset mappings are being refined based on community feedback in [Discussion #21](https://github.com/mmornati/home-assistant-csnet-home/discussions/21).

---

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. In Home Assistant, go to **HACS** → **Integrations**
3. Click the **"+"** button in the bottom right
4. Search for **"csnet home"** or **"Hitachi"**
5. Click **Install**
6. Restart Home Assistant
7. Continue to [Configuration](#configuration)

### Manual Installation

#### Option 1: Install from Release (Recommended)

1. Download the latest `hass-custom-csnet-home.zip` from the [Releases page](https://github.com/mmornati/home-assistant-csnet-home/releases)
2. Navigate to your Home Assistant configuration directory (where `configuration.yaml` is located)
3. Extract the contents:

```bash
cd YOUR_HASS_CONFIG_DIRECTORY
mkdir -p custom_components/csnet_home
cd custom_components/csnet_home
unzip ~/Downloads/hass-custom-csnet-home.zip
```

4. Restart Home Assistant
5. Continue to [Configuration](#configuration)

#### Option 2: Install from Git

```bash
# Clone the repository
cd /tmp
git clone https://github.com/mmornati/home-assistant-csnet-home.git

# Copy to Home Assistant
mkdir -p YOUR_HASS_CONFIG_DIRECTORY/custom_components
cp -pr home-assistant-csnet-home/custom_components/csnet_home YOUR_HASS_CONFIG_DIRECTORY/custom_components/
```

#### Option 3: Install Preview from Pull Request

For testing unreleased features or bug fixes:

1. Open the Pull Request on GitHub
2. Find the bot comment with a link to the workflow run
3. Download the artifact named `csnet_home-pr-preview`
4. Stop Home Assistant
5. Extract the ZIP contents into `YOUR_HASS_CONFIG_DIRECTORY/custom_components/csnet_home` (overwrite existing files)
6. Start Home Assistant

> **Warning:** If you installed via HACS, disable automatic updates while testing a preview to avoid overwrites.

---

## Configuration

After installation and restart:

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **"+ Add Integration"** in the bottom right
3. Search for **"Hitachi"**
4. Enter your **CSNet Manager credentials** (same as used on the CSNet Manager website/app)
5. Click **Submit**

![Add Integration](docs/images/add_integration.png)

### Quick Start Checklist

✅ Install the integration (HACS or Manual)  
✅ Restart Home Assistant  
✅ Add the integration via Settings → Devices & Services  
✅ Enter CSNet credentials  
✅ Verify entities are created:
   - Climate entities per zone (named `device_name-room_name`)
   - DHW water heater entity (if available)
   - Temperature sensors

✅ Test controls:
   - Change climate target temperature
   - Toggle heat/cool/off modes
   - Switch preset between comfort/eco
   - For DHW, try eco/performance/off modes

---

## Usage

### Climate Entities

Each zone in your Hitachi system appears as a separate climate entity in Home Assistant.

**Entity naming:** `climate.{device_name}_{room_name}`

**Available controls:**
- **HVAC Mode:** Off / Heat / Cool
- **Preset Mode:** Comfort / Eco
- **Target Temperature:** Adjustable within the device's range
- **Current Temperature:** Read from the zone sensor

**Attributes:**
```yaml
hvac_modes:
  - 'off'
  - heat
  - cool
preset_modes:
  - comfort
  - eco
current_temperature: 20.5
target_temperature: 22.0
hvac_action: heating  # or cooling, idle
real_mode: heating
operation_status: running
alarm_code: 0
c1_demand: true
c2_demand: false
doingBoost: false
timer_running: false
```

### Water Heater Entity

If your system includes a Domestic Hot Water (DHW) heater, it appears as a `water_heater` entity.

**Entity naming:** `water_heater.{device_name}_dhw`

**Available controls:**
- **Operation Mode:** Off / Eco / Performance
- **Target Temperature:** Adjustable based on mode

### Sensors

The integration creates various sensors for monitoring:
- `sensor.{device_name}_{room_name}_temperature` - Current temperature
- `sensor.{device_name}_{room_name}_target_temperature` - Target temperature
- `sensor.{device_name}_alarm_code` - Active alarm code (0 = no alarm)
- Additional sensors based on available data

### Alarm Notifications

When an alarm is detected (non-zero `alarm_code`), the integration automatically creates a persistent notification in Home Assistant to alert you.

---

## Troubleshooting

### Integration Not Working?

This integration was developed by reverse-engineering the CSNet Manager web interface. While it works with many configurations, different devices or setups may behave differently.

**Please help improve this integration by reporting issues!**

### Getting Debug Information

To help diagnose issues:

1. **Enable debug logging** in `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

2. **Capture the elements response:**
   - Open your browser's Developer Tools (F12)
   - Navigate to the CSNet Manager website
   - Go to the **Network** tab
   - Look for the `elements` call
   - Copy the JSON response

   ![Elements](docs/images/elements.png)

3. **Create an issue** on [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues) with:
   - Your configuration (number of zones, device type)
   - Debug logs
   - Elements JSON response (feel free to redact any private information)

### Control Not Working?

If a control has no effect:
1. Open your browser DevTools on the CSNet web app
2. Confirm the same action works there
3. Report the mismatch as an issue with a snippet from the `elements` response

### Join the Discussion

Participate in our [discussions community](https://github.com/mmornati/home-assistant-csnet-home/discussions) to:
- Share your configuration
- Help identify additional parameters
- Contribute to improving the integration
- See discussion [#21](https://github.com/mmornati/home-assistant-csnet-home/discussions/21) for ongoing parameter mapping work

---

## Developer Guide

### Development Setup

**Prerequisites:**
- Python 3.11 or later
- Git
- Home Assistant development knowledge

**Setup steps:**

1. **Clone the repository:**

```bash
git clone https://github.com/mmornati/home-assistant-csnet-home.git
cd home-assistant-csnet-home
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies:**

```bash
pip install -r custom_components/csnet_home/requirements-dev.txt
pip install -r custom_components/csnet_home/requirements.txt
```

4. **Install pre-commit hooks:**

```bash
pre-commit install
```

### Running Tests

**Run all tests:**

```bash
pytest
```

**Run specific test file:**

```bash
pytest tests/test_api.py
pytest tests/test_climate.py
pytest tests/test_coordinator.py
```

**Run tests with coverage:**

```bash
pytest --cov=custom_components/csnet_home --cov-report term-missing
pytest --cov=custom_components/csnet_home --cov-report html
```

**Test with specific Home Assistant version:**

```bash
pip install homeassistant==2025.10.0
pytest tests/ -v
```

**Test coverage reports:**
- Terminal: Shows coverage percentage and missing lines
- HTML: Open `htmlcov/index.html` in your browser for detailed coverage report

**What the tests cover:**
- API parsing of `/data/elements` response
- Coordinator update and data flow
- Climate entity behavior (modes, presets, actions, attributes)
- Sensor creation and updates
- Alarm handling and notifications
- Water heater controls

**CI/CD Testing:**

This project includes comprehensive automated testing across multiple Home Assistant versions:
- ✅ Unit tests with pytest (Python 3.11-3.13, HA 2025.6, 2025.8, 2025.10)
- ✅ Smoke tests for quick compatibility validation (12 combinations)
- ✅ Docker-based integration tests (HA 2025.9, 2025.10, latest)
- ✅ 🔥 **Nightly auto-detection** of latest HA version (no manual updates needed!)
- ✅ Nightly compatibility checks with HA dev branch (preview future changes)
- ✅ Automatic alerts for breaking changes
- ✅ 32+ test combinations across 7+ HA versions (dynamic latest adjusts automatically)

📖 **See [CI/CD Testing Documentation](CI_CD_TESTING.md)** for complete details on:
- Testing workflows and what they check
- 🔥 Dynamic latest version testing (zero maintenance!)
- How to interpret test results
- Running tests locally with different HA versions
- Using test fixtures
- Troubleshooting test failures

### Workflow Testing

Test GitHub Actions workflows locally before pushing:

#### Quick Validation (Fast)

```bash
./scripts/test-workflows.sh
```

This validates:
- Workflow syntax and structure
- YAML formatting
- Shell scripts in workflows
- Zip creation process

#### Full Integration Testing (with act)

Test complete workflows locally using Docker:

```bash
# Install act (macOS)
brew install act

# Or on Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Test validation workflow
act pull_request -W .github/workflows/validate.yaml

# Test with custom event payload
act pull_request -e .github/act-events/pull_request.json

# Test release workflow (requires secrets)
act release -W .github/workflows/release.yaml --secret-file .secrets
```

**Comprehensive testing guides:**
- [Local Testing Guide](.github/LOCAL_TESTING.md) - Static validation tools
- [Integration Testing Guide](.github/INTEGRATION_TESTING.md) - Full workflow testing with `act`

### Integration Testing (Recommended)

**Test your LOCAL development code in a real Home Assistant environment with ONE command!**

This project includes a complete integration testing setup that spins up a local Home Assistant instance with **YOUR LOCAL CODE** from `custom_components/csnet_home/` automatically mounted.

🔑 **Key Feature:** Tests your current working directory code, NOT a downloaded or released version. Make changes and run `make restart` to test immediately!

#### Quick Start

```bash
# Start Home Assistant with your integration
./scripts/integration-test.sh start

# Open in browser (auto-opens on macOS)
./scripts/integration-test.sh open

# View logs
./scripts/integration-test.sh logs

# Stop when done
./scripts/integration-test.sh stop
```

#### Or using Make

```bash
make start    # Start Home Assistant
make logs     # View logs
make stop     # Stop Home Assistant
make clean    # Clean all test data
```

#### What It Does

The integration testing environment:
- ✅ Starts Home Assistant in Docker (port 8123)
- ✅ Mounts your custom component automatically
- ✅ Provides a clean test configuration
- ✅ Allows you to test the full user experience
- ✅ Hot-reloads on restart after code changes
- ✅ Isolated from your production Home Assistant

#### Testing Workflow

1. **Start the test environment:**
   ```bash
   ./scripts/integration-test.sh start
   ```

2. **Open http://localhost:8123** and create an admin account (first time only)

3. **Add your integration:**
   - Go to **Configuration** → **Integrations**
   - Click **"Add Integration"**
   - Search for **"Hitachi CSNet Home"**
   - Enter your CSNet credentials

4. **Test your integration** with real devices

5. **Make code changes**, then restart:
   ```bash
   ./scripts/integration-test.sh restart
   ```

6. **View detailed logs:**
   ```bash
   ./scripts/integration-test.sh logs
   ```

#### Available Commands

```bash
./scripts/integration-test.sh start      # Start Home Assistant
./scripts/integration-test.sh stop       # Stop Home Assistant
./scripts/integration-test.sh restart    # Restart after code changes
./scripts/integration-test.sh logs       # Follow logs (real-time)
./scripts/integration-test.sh status     # Check if running
./scripts/integration-test.sh clean      # Remove all test data
./scripts/integration-test.sh test       # Run unit tests first
```

📖 **Full documentation:** See [INTEGRATION_TESTING.md](INTEGRATION_TESTING.md) for the complete guide including:
- All commands (make and script)
- Debugging techniques
- Verification steps
- Troubleshooting solutions
- Examples and best practices

### End-to-End Testing (Alternative Methods)

#### Option 1: Your Production HA Instance

1. Install the integration (HACS or manual)
2. Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

3. Restart HA and watch logs for `custom_components.csnet_home`
4. Check **Settings** → **System** → **Logs** in Home Assistant UI

**⚠️ Warning:** Testing on production can break your setup. Use the integration testing environment instead!

### Code Formatting

This project uses `black` for code formatting and `isort` for import sorting.

**Format code:**

```bash
# Format all Python files
black custom_components/csnet_home tests

# Sort imports
isort custom_components/csnet_home tests
```

**Check formatting (without changes):**

```bash
black --check custom_components/csnet_home tests
isort --check-only custom_components/csnet_home tests
```

Pre-commit hooks will automatically format your code before commits.

### Project Structure

```
home-assistant-csnet-home/
├── custom_components/
│   └── csnet_home/
│       ├── __init__.py          # Integration setup and entry point
│       ├── api.py               # CSNet API client
│       ├── climate.py           # Climate entity implementation
│       ├── config_flow.py       # Configuration flow (UI)
│       ├── const.py             # Constants and configuration
│       ├── coordinator.py       # Data update coordinator
│       ├── manifest.json        # Integration metadata
│       ├── sensor.py            # Sensor entities
│       ├── water_heater.py      # Water heater entity
│       ├── requirements.txt     # Runtime dependencies
│       └── requirements-dev.txt # Development dependencies
├── tests/                       # Test suite
│   ├── test_api.py
│   ├── test_climate.py
│   ├── test_config_flow.py
│   ├── test_coordinator.py
│   └── test_sensor.py
├── .github/
│   └── workflows/               # CI/CD workflows
│       ├── validate.yaml        # PR validation
│       └── release.yaml         # Release automation
├── scripts/                     # Helper scripts
└── images/                      # Documentation images
```

---

## Known Limitations

- **AUTO mode** is not exposed as a settable HA HVAC mode due to server-side semantics; the entity reports heating/cooling/idle actions based on temperatures and `mode`
- Some fields from the elements endpoint are device-specific and undocumented; we are progressively surfacing them (see [#21](https://github.com/mmornati/home-assistant-csnet-home/discussions/21))
- The integration requires an active internet connection to communicate with the CSNet Manager cloud service
- Response times depend on the CSNet Manager service availability and response time

---

## Contributing

**Contributions are welcome!** 🎉

This integration is tested with a limited number of home installations and configurations. To make it work for everyone, we need your help!

**Ways to contribute:**
- 🐛 Report bugs and issues
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📖 Improve documentation
- 💬 Participate in discussions
- ✅ Test with your device configuration

**Getting started:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and ensure tests pass
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to your fork (`git push origin feature/amazing-feature`)
6. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:
- Setting up your development environment
- Running tests and linters
- Submitting bug reports
- Pull request process

**Not a developer?** You can still help!
- Share your device configuration in [SUPPORTED_DEVICES.md](docs/SUPPORTED_DEVICES.md)
- Report what works and what doesn't
- Answer questions in discussions
- Improve documentation

Join our [discussions community](https://github.com/mmornati/home-assistant-csnet-home/discussions) to connect with other users and contributors.

---

## Additional Documentation

Developer and technical documentation:

- **[User Documentation](https://mmornati.github.io/home-assistant-csnet-home)** - Complete user guide (installation, configuration, usage)
- **[CI/CD Testing](CI_CD_TESTING.md)** - Comprehensive testing infrastructure and Home Assistant compatibility testing
- **[Dynamic Version Testing](DYNAMIC_VERSION_TESTING.md)** - 🔥 Automatic latest HA version detection (zero maintenance!)
- **[SUPPORTED_DEVICES.md](docs/SUPPORTED_DEVICES.md)** - Device compatibility matrix and testing results from the community
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines, development setup, and bug reporting
- **[ALARM_API_IMPLEMENTATION.md](ALARM_API_IMPLEMENTATION.md)** - Technical details about the alarm API implementation
- **[tests/README.md](tests/README.md)** - Testing documentation and development setup
- **[Test Fixtures](tests/fixtures/README.md)** - Guide to using and creating test fixtures

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Support

- **📚 Documentation:** [User Guide](https://mmornati.github.io/home-assistant-csnet-home)
- **🐛 Issues:** [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues)
- **💬 Discussions:** [GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions)
- **📦 Releases:** [GitHub Releases](https://github.com/mmornati/home-assistant-csnet-home/releases)

---

**Made with ❤️ for the Home Assistant community**
