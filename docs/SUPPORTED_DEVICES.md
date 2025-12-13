# Supported Devices & Compatibility Matrix

This document tracks which Hitachi devices have been tested with this integration and what features work for each configuration. 

**If you're using this integration, please contribute by adding your device configuration below!** This helps the community understand what works and what doesn't.

---

## How to Contribute Your Testing Results

1. **Fork this repository** or **edit this file directly** (click the pencil icon on GitHub)
2. **Add your device** to the appropriate table below
3. **Fill in all columns** with your test results
4. **Submit a pull request** or create an issue with your findings

---

## Quick Reference: Device Types

Based on the CSNet Manager system, devices are categorized by **Unit Model** and **Zone Types**:

### Unit Models
- **Yutaki S** - Standard model
- **Yutaki SC** - Comfort model
- **Yutaki S80** - 80°C high-temperature model
- **Yutaki M** - Monobloc model
- **Yutaki SC Lite** - Lite version
- **Yutampo** - Specific regional model

### Zone Types
- **Zone 1 (C1 Air)** - Air circuit 1 (room thermostats)
- **Zone 2 (C2 Air)** - Air circuit 2 (room thermostats)
- **Zone 3 (DHW)** - Domestic Hot Water
- **Zone 5 (C1 Water)** - Water circuit 1 (floor heating, radiators)

---

## Compatibility Matrix

### Legend
- ✅ **Working** - Feature fully functional
- ⚠️ **Partial** - Feature works with limitations (see notes)
- ❌ **Not Working** - Feature not functional
- ➖ **N/A** - Not applicable for this configuration
- ❓ **Unknown** - Not tested yet

---

## Yutaki S Models

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Thermostats | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-------------|-----|---------------------|--------------|
| @mmornati | Yutaki S | H-0302 | 2 (C1, C2 - Floor Heating) | 2 (1 per floor) | ➖ N/A | Latest | 2025-10-24 |
| @Aparenty-1977 | Yutaki S2 | ❓ Unknown | ✅ | ❓ Unknown | ✅ Yutampo | Latest | 2025-10-26 |

| *Add your config* | | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Silent Mode | Fan Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------|-------------|---------------|-------------|------------|
| @mmornati | ✅ | ✅ | ✅ Heat/Cool/Auto/Off | ✅ Eco/Comfort | ➖ N/A | ❓ Unknown | ➖ N/A | ❓ Unknown | ✅ | ✅ 2 zones/2 thermostats |
| @Aparenty-1977 | ✅ | ✅ | ❓ Unknown | ❓ Unknown | ✅ Yutampo | ❓ Unknown | ❓ Not tested | ❓ Not tested | ❓ Unknown | ❓ Unknown |
| *Add your results* | | | | | | | | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| @mmornati | - **Working perfectly**: C1 and C2 circuits for floor heating (1 circuit per floor)<br>- **Thermostats**: 2 separate room thermostats, one per floor<br>- - **Temperature control**: Responsive, range 8-55°C for heating<br>- **Sensors**: All system sensors reporting correctly |
| *Add your notes* | |

---

## Yutaki SC Models

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Thermostats | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-------------|-----|---------------------|--------------|
| *Add your config* | Yutaki SC | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Silent Mode | Fan Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------|-------------|---------------|-------------|------------|
| *Add your results* | | | | | | | | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| *Add your notes* | |

---

## Yutaki S80 Models

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Thermostats | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-------------|-----|---------------------|--------------|
| *Add your config* | Yutaki S80 | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Silent Mode | Fan Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------|-------------|---------------|-------------|------------|
| *Add your results* | | | | | | | | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| *Add your notes* | |

---

## Yutaki M Models

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Thermostats | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-------------|-----|---------------------|--------------|
| *Add your config* | Yutaki M | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Silent Mode | Fan Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------|-------------|---------------|-------------|------------|
| *Add your results* | | | | | | | | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| *Add your notes* | |

---

## Yutaki SC Lite Models

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Thermostats | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-------------|-----|---------------------|--------------|
| *Add your config* | Yutaki SC Lite | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Silent Mode | Fan Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------|-------------|---------------|-------------|------------|
| *Add your results* | | | | | | | | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| *Add your notes* | |

---

## Yutampo Models

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Thermostats | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-------------|-----|---------------------|--------------|
| *Add your config* | Yutampo | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Silent Mode | Fan Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------|-------------|---------------|-------------|------------|
| *Add your results* | | | | | | | | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| *Add your notes* | |

---

## Fan Coil Systems

These systems support fan speed control (off, low, medium, auto) instead of silent mode.

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Fan Coils | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-----------|-----|---------------------|--------------|
| *Add your config* | | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Fan Speed Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------------|---------------|-------------|------------|
| *Add your results* | | | | | | ✅ Off/Low/Med/Auto | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| *Add your notes* | |

---

## Other Hitachi Models

If your model isn't listed above, please add it here!

### Configuration Details

| Tester | Unit Model | Firmware | Heat Circuits | Thermostats | DHW | Integration Version | Last Updated |
|--------|------------|----------|---------------|-------------|-----|---------------------|--------------|
| *Add your config* | Your Model | | | | | | |

### Feature Compatibility

| Tester | Climate Control | Temperature Set | HVAC Modes | Preset Modes | DHW Control | Silent Mode | Fan Control | Alarm Monitor | OTC Support | Multi-Zone |
|--------|----------------|-----------------|------------|--------------|-------------|-------------|-------------|---------------|-------------|------------|
| *Add your results* | | | | | | | | | | |

### Known Issues & Notes

| Tester | Issues / Notes |
|--------|----------------|
| *Add your notes* | |

---

## Feature Descriptions

### Climate Control
Full control of your heat pump system through Home Assistant climate entities. One climate entity per zone/thermostat.

### Temperature Set
Ability to set target temperature. Range varies by mode and configuration (typically 8-55°C).

### HVAC Modes
- **Heat** - Heating mode
- **Cool** - Cooling mode (if supported by your system)
- **Auto** - Automatic heating/cooling based on temperature
- **Off** - System off

### Preset Modes
- **Comfort** - Normal comfort temperature
- **Eco** - Energy-saving mode with reduced temperature

### DHW Control
Control of Domestic Hot Water heater with modes:
- **Off** - DHW off
- **Eco** - Standard DHW heating
- **Performance** - Boost mode for faster heating

### Silent Mode
Reduces outdoor unit noise (not available on fan coil systems).

### Fan Control
For fan coil systems only. Speeds: Off, Low, Medium, Auto.

### Alarm Monitor
Displays alarm codes and messages from the system with persistent notifications.

### OTC Support
Outdoor Temperature Compensation - automatic adjustment based on outdoor temperature.

### Multi-Zone
Support for multiple heating circuits (C1, C2) and multiple room thermostats.

---

## Additional Sensors

The integration provides additional sensors for system monitoring:

### Device-Level Sensors
- Current temperature
- Target temperature  
- Operating mode
- On/Off status
- Alarm status
- WiFi signal strength
- Connectivity status
- Last communication timestamp

### Installation-Level Sensors (if supported)
- Pump speed
- Water flow
- Water inlet/outlet temperature
- Water pressure
- Gas/liquid temperature
- Defrost status
- Mix valve position
- Outdoor temperature
- Weather temperature (from cloud)
- LCD software version
- Central control configuration
- System configuration bits
- OTC type settings

---

## How to Find Your Device Information

### Finding Your Unit Model
1. Open the CSNet Manager app or website
2. Go to **Settings** → **System Information**
3. Look for **Unit Model** field

### Finding Your Firmware Version
1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Find your Hitachi device
3. Look at device information for firmware version

### Finding Your Zone Configuration
1. In the CSNet Manager app, check how many thermostats/zones are configured
2. In Home Assistant, count the number of climate entities created
3. Check if you have a DHW (water heater) entity

---

## Troubleshooting & Debug Information

If you're experiencing issues:

1. **Enable debug logging** in `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

2. **Capture the elements response** from CSNet Manager:
   - Open browser Developer Tools (F12)
   - Navigate to CSNet Manager website
   - Go to Network tab
   - Find the `elements` API call
   - Copy the JSON response

3. **Report the issue** on [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues) with:
   - Your device configuration
   - Debug logs
   - Elements JSON response (redact personal info)

---

## Contributing

**Your feedback is valuable!** Even if everything works perfectly, please add your configuration to help others with similar setups.

### Quick Contribution Steps:
1. Click the **Edit** button (pencil icon) on this file in GitHub
2. Add your device to the appropriate table
3. Fill in your test results
4. Submit a pull request with description: "Add device compatibility: [Your Model]"

### What to Include:
- ✅ **DO** include firmware version
- ✅ **DO** note specific configuration (number of circuits, thermostats)
- ✅ **DO** mention any workarounds you found
- ✅ **DO** update integration version
- ❌ **DON'T** include personal information (addresses, names, etc.)

---

## Discussion

Join the discussion about device compatibility:
- [Discussion #21 - Mode and preset mappings](https://github.com/mmornati/home-assistant-csnet-home/discussions/21)
- [GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions)

---

## License

This document is part of the home-assistant-csnet-home project and is licensed under the Apache License 2.0.

---

**Last Updated:** 2025-01-24
**Document Version:** 1.0

