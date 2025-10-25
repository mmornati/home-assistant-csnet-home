# Hitachi CSNet Home Integration - User Documentation

Welcome to the complete user documentation for the **Hitachi CSNet Home Integration** for Home Assistant!

## About This Integration

This custom integration connects your Hitachi heat pump and air conditioning systems with Home Assistant using the **ATW-IOT-01 module** through the **CSNet Manager** cloud service.

### Why This Integration?

As Hitachi transitioned from the older Hi-Kumo system to the new ATW-IOT-01 module, previous integration methods stopped working. This integration was developed by reverse-engineering the CSNet Manager web interface to provide full control of your Hitachi climate systems directly from Home Assistant.

---

## Quick Navigation

### 🚀 Getting Started
- **[Installation Guide](Installation-Guide.md)** - Step-by-step installation instructions
- **[Configuration Guide](Configuration-Guide.md)** - Setting up your integration

### 📚 Features & Usage
- **[Climate Control](Climate-Control.md)** - Control your heating and cooling zones
- **[Water Heater Control](Water-Heater-Control.md)** - Manage your DHW system
- **[Sensors Reference](Sensors-Reference.md)** - Complete list of available sensors
- **[Advanced Features](Advanced-Features.md)** - Silent mode, fan control, OTC, and more

### ⚙️ Configuration Types
- **[Multi-Zone Configuration](Multi-Zone-Configuration.md)** - C1 and C2 circuits setup
- **[Water Heater Setup](Water-Heater-Control.md)** - DHW integration and management
- **[Fan Control](Advanced-Features.md#fan-speed-control-fan-coil-systems)** - Fan coil system configuration

### 🔧 Help & Support
- **[Troubleshooting](Troubleshooting.md)** - Common issues and solutions
- **[FAQ](FAQ.md)** - Frequently asked questions

### 🤝 Community
- **[Supported Devices](../SUPPORTED_DEVICES.md)** - Compatible devices and configurations
- **[Contributing](../CONTRIBUTING.md)** - Help improve this integration
- **[GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions)** - Ask questions

---

## What You Can Control

### Climate Entities (One per zone/thermostat)
✅ Turn on/off  
✅ Set target temperature  
✅ Change HVAC mode (Heat, Cool, Auto, Off)  
✅ Switch preset mode (Comfort, Eco)  
✅ Monitor current temperature  
✅ View operation status and alarms  
✅ Control fan modes (silent or speed control depending on system)

### Water Heater Entity (If you have DHW)
✅ Turn on/off  
✅ Set target temperature  
✅ Change operation mode (Off, Eco, Performance)  
✅ Monitor current temperature

### Sensors (Comprehensive monitoring)
✅ Temperature sensors (current, target, water, outdoor)  
✅ System status sensors  
✅ Alarm monitoring with notifications  
✅ Water pressure and flow (if applicable)  
✅ WiFi signal strength  
✅ Connectivity status  
✅ OTC (Outdoor Temperature Compensation) settings  
✅ System configuration details

---

## Supported Systems

### Unit Models
- **Yutaki S** - Standard model
- **Yutaki SC** - Comfort model
- **Yutaki S80** - 80°C high-temperature model
- **Yutaki M** - Monobloc model
- **Yutaki SC Lite** - Lite version
- **Yutampo** - Regional model

### Zone Types
- **C1 Air** - Zone 1 air circuit (room thermostats)
- **C2 Air** - Zone 2 air circuit (room thermostats)
- **C1 Water** - Zone 1 water circuit (floor heating, radiators)
- **C2 Water** - Zone 2 water circuit (floor heating, radiators)
- **DHW** - Domestic Hot Water

### Special Configurations
- Single zone systems
- Multi-zone systems (up to 2 circuits)
- With or without DHW (water heater)
- Fan coil compatible systems
- OTC (Outdoor Temperature Compensation) systems

---

## Key Features

### 🌡️ Full Climate Control
- Precise temperature control (typically 8°C to 55°C range)
- Multiple HVAC modes: Heat, Cool, Auto, Off
- Eco and Comfort preset modes
- Real-time temperature monitoring

### 💧 Water Heater Management
- Three operation modes: Off, Eco, Performance (Boost)
- Temperature control (typically 30°C to 55°C)
- Current temperature monitoring

### 🔔 Intelligent Alarm System
- Real-time alarm monitoring
- Persistent Home Assistant notifications
- Detailed alarm information (code, origin, description)
- Alarm history tracking
- Statistics and analytics

### 📊 Comprehensive Sensors
- **Zone Sensors**: Current temp, target temp, operating mode, status
- **System Sensors**: Water flow, pressure, pump speed, outdoor temp
- **Device Sensors**: WiFi signal, connectivity, last communication
- **Diagnostic Sensors**: OTC settings, system configuration, firmware info

### 🎯 Advanced Features
- **Silent Mode**: Reduce outdoor unit noise (non-fan coil systems)
- **Fan Speed Control**: Off, Low, Medium, Auto (fan coil systems)
- **Multi-Zone Support**: Manage multiple heating circuits independently
- **OTC Support**: Outdoor Temperature Compensation monitoring
- **Dynamic Temperature Limits**: Automatically adjusts based on mode and configuration

---

## System Requirements

### Home Assistant
- **Version**: 2023.1.0 or newer recommended
- **Installation Method**: Any (Core, Container, Supervised, OS)

### Hitachi Equipment
- Heat pump with **ATW-IOT-01 module** installed
- Active **CSNet Manager** account
- Internet connection for cloud communication

### Integration Installation
- Can be installed via:
  - **HACS** (recommended - easiest updates)
  - **Manual installation** from releases
  - **Manual installation** from source

---

## Documentation Structure

This documentation is organized into focused pages:

1. **Installation & Setup** - Get the integration installed and configured
2. **Feature Guides** - Learn how to use each feature
3. **Configuration Examples** - Setup guides for different system types
4. **Advanced Topics** - Automations, dashboards, and customization
5. **Reference** - Complete sensor and attribute listings
6. **Troubleshooting** - Solutions to common problems

Each page includes:
- Clear explanations
- Step-by-step instructions
- Screenshots and examples (where applicable)
- Tips and best practices
- Links to related topics

---

## Getting Help

### Documentation
Start here! This documentation covers most common scenarios and questions.

### GitHub Discussions
Ask questions, share configurations, and discuss with the community:
👉 [GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions)

### GitHub Issues
Report bugs or request features:
👉 [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues)

### Debug Logging
Enable detailed logging for troubleshooting:
```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

---

## Contributing to Documentation

Found an error? Have a suggestion? Want to add an example?

This documentation is part of the project repository. You can:
1. **Edit directly on GitHub** - Click the "Edit" button
2. **Submit a Pull Request** - Fork and create a PR
3. **Open an Issue** - Report documentation problems

We appreciate all contributions! 🙏

---

## Quick Start

Ready to get started? Jump to the [Installation Guide](Installation-Guide.md)!

Already installed? Check out the [Configuration Guide](Configuration-Guide.md).

Need help? Visit [Troubleshooting](Troubleshooting.md) or [FAQ](FAQ.md).

---

## Version Information

- **Current Integration Version**: 2.1.0
- **Documentation Version**: 1.0
- **Last Updated**: January 2025

For version history and release notes, see the [GitHub Releases](https://github.com/mmornati/home-assistant-csnet-home/releases) page.

---

## License

This integration is licensed under the Apache License 2.0.  
See the [LICENSE](https://github.com/mmornati/home-assistant-csnet-home/blob/main/LICENSE) file for details.

---

**Made with ❤️ for the Home Assistant community**

