---
description: User documentation for the Hitachi CSNet Home integration for Home Assistant.
---

# Documentation

The **Hitachi CSNet Home** integration connects Hitachi heat pumps fitted with the **ATW-IOT-01** module to Home Assistant, through the **CSNet Manager** cloud service. It creates climate entities for each zone, a water heater for domestic hot water (and the swimming pool, if you have one), and sensors for the water loop, the outdoor unit, energy use and alarms.

!!! unofficial "Unofficial integration"
    Not affiliated with, endorsed by or supported by Hitachi. Hitachi offers no public API, so the integration works the way the CSNet Manager web app does, and it can break when Hitachi changes its website. Read [How it works & disclaimer](How-It-Works.md).

## Start here

| Step | Page | What it covers |
|---|---|---|
| 1 | [Installation Guide](Installation-Guide.md) | HACS, release zip, or from source |
| 2 | [Configuration Guide](Configuration-Guide.md) | Account, polling interval, language, options, reconfiguring |
| 3 | [Climate Control](Climate-Control.md) | HVAC modes, presets, temperature limits, dashboards |

## Reference

- [Multi-Zone Configuration](Multi-Zone-Configuration.md): C1 and C2 circuits, air and water zones
- [Water Heater Control](Water-Heater-Control.md): domestic hot water modes and boost
- [Sensors Reference](Sensors-Reference.md): every sensor, its unit and where it comes from
- [Compressor Sensors](../COMPRESSOR_SENSORS.md): outdoor unit internals
- [Advanced Features](Advanced-Features.md): silent mode, fan coils, OTC, alarms, services
- [How it works & disclaimer](How-It-Works.md): the API, network traffic, privacy, known limitations

## Help

- [Troubleshooting](Troubleshooting.md) and [FAQ](FAQ.md)
- [Supported devices](../SUPPORTED_DEVICES.md): what owners have tested, and how to add yours
- [GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions) for questions, [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues) for bugs

## Supported systems

**Unit models:** Yutaki S, Yutaki SC, Yutaki S80, Yutaki M, Yutaki SC Lite, Yutampo.

**Circuits:** C1 and C2 air circuits (room thermostats), C1 and C2 water circuits (underfloor, radiators), domestic hot water (DHW), swimming pool (SWP), fan-coil systems, outdoor temperature compensation (OTC).

## Requirements

- A Hitachi unit with the **ATW-IOT-01** module, connected to the internet
- A working **CSNet Manager** account (the one you use on [csnetmanager.com](https://www.csnetmanager.com))
- Home Assistant, ideally with [HACS](https://hacs.xyz/)

## Debug logging

When something looks wrong, enable debug logs before opening an issue:

```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

Debug logs can contain raw responses from CSNet Manager. Read them before posting them publicly.

## Contributing to the docs

Every page has an edit button that opens the source on GitHub. Corrections, examples and screenshots from your own installation are welcome as pull requests.
