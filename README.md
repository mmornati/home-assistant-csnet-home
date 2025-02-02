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

## Contributing

Contributions are welcome! You are encouraged to submit PRs, bug reports, feature requests. What coded here is tested with few home installation/configuration and it may have problems when testing in new ones. If we want to let it working for the most of us, we need to share together :)
If you want to contributing developing new features or fixing bugs, please see this [README](CONTRIBUTING.md) for setting up a development environment and running tests.

Even if you aren't a developer, please participate in our
[discussions community](https://github.com/mmornati/home-assistant-csnet-home/discussions).