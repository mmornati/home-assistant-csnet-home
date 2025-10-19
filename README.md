[![GitHub Release](https://img.shields.io/github/v/release/mmornati/home-assistant-csnet-home.svg?style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/mmornati/home-assistant-csnet-home?label=Last%20Release&style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home)
[![GitHub Commit Activity](https://img.shields.io/github/commit-activity/y/mmornati/home-assistant-csnet-home.svg?style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home/commits/main)
[![GitHub last commit](https://img.shields.io/github/last-commit/mmornati/home-assistant-csnet-home?style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/mmornati/home-assistant-csnet-home/validate.yaml?branch=main&style=for-the-badge)](https://github.com/mmornati/home-assistant-csnet-home)
[![License](https://img.shields.io/github/license/mmornati/home-assistant-csnet-home.svg?style=for-the-badge)](LICENSE)

# home-assistant-csnet-home
CSNet Home to control Hitachi heaters using the atw-iot-01 module

## Why?
Has hitachi is [explaining](https://device.report/manual/12211094) the ATW-IOT-01 device is now replacing the old version going through Hi-Kumo. This is blocking any way to recover the Hitachi devices data and control them.
This integration is making this possible connecting directly to the "Cloud" application.

## Features

- Climate entities per zone with:
  - HVAC modes: off, heat, cool
  - Presets: comfort, eco (mapped from `ecocomfort`)
  - Target temperature control
  - On/Off support
  - Action reporting: heating, cooling, idle
  - Extra attributes from the elements endpoint: `real_mode`, `operation_status`, `timer_running`, `alarm_code`, `c1_demand`, `c2_demand`, `doingBoost`
- Water heater entity (DHW) with temperature and modes (off/eco/performance)
- Basic sensors for current/target temperatures and state fields

Notes about modes/presets mapping are being refined based on community findings in the discussion: [Add new sensors getting from all remaining device data #21](https://github.com/mmornati/home-assistant-csnet-home/discussions/21).

## Installation

### Option 1: HACS

Under HACS -> Integrations, select "+", search for `csnet home` and install it.

### Option 2: Manual

From the [latest release](https://github.com/mmornati/home-assistant-csnet-home/releases) download the zip file `hass-custom-csnet-home.zip`
```bash
cd YOUR_HASS_CONFIG_DIRECTORY    # same place as configuration.yaml
mkdir -p custom_components/csnet_home
cd custom_components/csnet_home
unzip hass-custom-csnet-home.zip
```

Alternatively, you can install the current GitHub master version by cloning and copying:
```bash
mkdir SOME_LOCAL_WORKSPACE
cd SOME_LOCAL_WORKSPACE
git clone https://github.com/mmornati/home-assistant-csnet-home.git
mkdir -p YOUR_HASS_CONFIG_DIRECTORY/custom_components
cp -pr home-assistant-csnet-home/custom_components/csnet_home YOUR_HASS_CONFIG_DIRECTORY/custom_components
```

After the Home Assistant restart, go to the Integrations dashboard (`/config/integrations/dashboard`) and click on the "add new integration button".
Look for "Hitachi" integration and if everything went well you should find this one.
![Add Integration](images/add_integration.png)

Then you will be asked for your login credentials and is everything is OK with the installation and your configuration, you will have new entities in Home Assistant.

### Quick start checklist

1. Install the integration (HACS or Manual)
2. Restart Home Assistant
3. Add the integration from Settings → Devices & Services → Add Integration → "Hitachi"
4. Enter your CSNet credentials and submit
5. Verify entities are created:
   - Climate entities per zone: names follow `device_name-room_name`
   - DHW water heater entity if available
   - Temperature sensors
6. Test controls:
   - Change climate target temperature
   - Toggle heat/cool/off
   - Switch preset between comfort/eco
   - For DHW, try eco/performance/off

If a control has no effect, open your browser DevTools on the CSNet web app and confirm the same action works there; report mismatches as issues with a snippet from the `elements` response (see below).

### Install a release ZIP locally (official release)

1. Download `hass-custom-csnet-home.zip` from the latest release page.
2. Stop Home Assistant.
3. Extract the ZIP contents into `YOUR_HASS_CONFIG_DIRECTORY/custom_components/csnet_home`.
   - The directory structure should be: `custom_components/csnet_home/__init__.py`, `api.py`, `manifest.json`, etc.
4. Start Home Assistant and reload the integration (or restart HA).

### Install a preview ZIP from a Pull Request (PR)

Each PR creates a downloadable preview ZIP as an Actions artifact.

1. Open the PR and find the bot comment with a link to the workflow run.
2. Download the artifact named `csnet_home-pr-preview`.
3. Stop Home Assistant.
4. Extract the ZIP contents into `YOUR_HASS_CONFIG_DIRECTORY/custom_components/csnet_home` (overwrite existing files).
5. Start Home Assistant and reload the integration (or restart HA).

Notes
- If you installed via HACS, disable automatic updates while testing a preview ZIP to avoid overwrites.
- After testing, you can restore by re-installing from HACS or re-extracting the official release ZIP.

## Is not working for me, what to do?
I was able to test the application only with my configuration: 1 heater with 2 zones. Hitachi is not providing APIs for this part and I just inspect how the website is working and what calls are done to retrieve the data and execute the base operations.
This mainly means that I'm not sure with different device or configuration that the information are returned in the same way.
So feel free to test the integration and share any information that can help to fix your problems creating an issue on this repository

### Get information for sensor
The sensor/climate are created using the `/elements` call (I prefer not to name it as API because is far from well code API)
* Access to your browser developer console
* Look within the Network data for the `elements` call
* share the JSON in the Response

![Elements](images/elements.png)

> **WARNING**
There are not critical information inside the response, but feel free to clean anything you want to keep private.

Please also consider commenting in the discussion that tracks additional parameters and meanings: [#21](https://github.com/mmornati/home-assistant-csnet-home/discussions/21).

## Development and testing locally

This repo ships a basic test suite you can run without Home Assistant Supervisor:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r custom_components/csnet_home/requirements-dev.txt -r custom_components/csnet_home/requirements.txt
pytest -q
```

What the tests cover:
- API parsing of the `/data/elements` response
- Coordinator update wiring
- Climate entity behavior (hvac modes, presets, hvac_action, attributes, on/off, set temperature)

If you want to validate end-to-end in your HA instance:
- Install the integration (HACS or manual)
- Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

- Restart HA and watch logs for `custom_components.csnet_home`

## Known limitations

- AUTO mode is not exposed as a settable HA hvac mode due to server-side semantics; the entity reports heating/cooling/idle actions based on temperatures and `mode`.
- Some fields from the elements endpoint are device-specific and undocumented; we are progressively surfacing them. See [#21](https://github.com/mmornati/home-assistant-csnet-home/discussions/21).

## Contributing

Contributions are welcome! You are encouraged to submit PRs, bug reports, feature requests. What coded here is tested with few home installation/configuration and it may have problems when testing in new ones. If we want to let it working for the most of us, we need to share together :)
If you want to contributing developing new features or fixing bugs, please see this [README](CONTRIBUTING.md) for setting up a development environment and running tests.

Even if you aren't a developer, please participate in our
[discussions community](https://github.com/mmornati/home-assistant-csnet-home/discussions).