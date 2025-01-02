# home-assistant-csnet-home
CSNet Home to control Hitachi heaters using the atw-iot-01 module

## Why?
Has hitachi is [explaining](https://device.report/manual/12211094) the ATW-IOT-01 device is now replacing the old version going through Hi-Kumo. This is blocking any way to recover the Hitachi devices data and control them.
This integration is making this possible connecting directly to the "Cloud" application.

## How to use it?
Yu can install the integration like any other custom components.

Just download the code and put inside your `configuration/custom_components` folder.
```
git clone https://github.com/mmornati/home-assistant-csnet-home
cp -r home-assistant-csnet-home/custom_components/csnet_home config/custom_components
```

## Is not working for me, what to do?
I was able to test the application only with my configuration: 1 heater with 2 zones. Hitachi is not providing APIs for this part and I just inspect how the website is working and what calls are done to retrieve the data and execute the base operations.
This mainly means that I'm not sure with different device or configuration that the information are returned in the same way.
So feel free to test the integration and share any information that can help to fix your problems creating an issue on this repository

### Get information for sensor
The sensor/climate are created using the `/elements` call (I prefer not to name it as API becasue is far from well code API)
* Access to your browser developer console
* Look within the Network data for the `elements` call
* share the JSON in the Response

![Elements](images/elements.png)

> **WARNING**
There are not critical information inside the response, but feel free to clean anything you want to keep private.