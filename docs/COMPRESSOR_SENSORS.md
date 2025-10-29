# Compressor and Outdoor Unit Sensors

## Overview

The CSNet Home integration now provides comprehensive monitoring of your heat pump's compressor and outdoor unit through a dedicated device with 30+ sensors. This allows you to track the real-time performance, efficiency, and health of your system.

## Device Structure

All compressor-related sensors are grouped under a dedicated device:
- **Device Name**: `Compressor Outdoor Unit`
- **Manufacturer**: Hitachi
- **Model**: Automatically detected (Yutaki, RAS-1, RAS-2, RAD)

## Primary Compressor Sensors

### Operational Metrics

| Sensor | Description | Unit | Usage |
|--------|-------------|------|-------|
| **Compressor Frequency** | Current operating frequency of the compressor | Hz | Monitor compressor speed (0-120 Hz typical) |
| **Compressor Current** | Electrical current draw | A | Track power consumption |
| **Compressor Capacity** | Current capacity setting | - | System capacity indicator |
| **Operation Status** | Current operational state | - | Standby, Heating, Cooling, DHW, Idle, Defrost, Stop |

### Temperature Sensors

| Sensor | Description | Unit | Importance |
|--------|-------------|------|------------|
| **Discharge Temperature** | Temperature of refrigerant leaving compressor | °C | **Critical** - High values may indicate issues |
| **Evaporator Temperature** | Temperature at the evaporator | °C | Monitor heat exchange efficiency |
| **Outdoor Ambient Temperature** | Outside air temperature at the unit | °C | Context for system performance |

### Pressure Sensors

| Sensor | Description | Unit | Usage |
|--------|-------------|------|-------|
| **Discharge Pressure** | High-side refrigerant pressure | bar | Monitor compression performance |
| **Suction Pressure** | Low-side refrigerant pressure | bar | Monitor evaporation performance |
| **Suction Pressure Correction** | Correction factor applied | - | Diagnostic information |

### Control & Valve Sensors

| Sensor | Description | Unit | Usage |
|--------|-------------|------|-------|
| **Expansion Valve Opening (EVI)** | Electronic expansion valve position | % | Monitor refrigerant flow control (0-100%) |
| **Outdoor Fan RPM** | Speed of outdoor unit fan | RPM | Track cooling/ventilation |

### System Information

| Sensor | Description | Values |
|--------|-------------|--------|
| **System Status Flags** | Bitfield of system configuration | Hex value with decoded attributes |
| **Outdoor Unit Code** | Type of outdoor unit | Yutaki, RAS-1, RAS-2, RAD |
| **Outdoor Unit Capacity Code** | Capacity identifier | Numeric code |
| **Outdoor Unit PCB Software** | Software version of outdoor unit | Hex version |

## Secondary Cycle Sensors

For systems with dual-cycle configuration (e.g., cascade systems, advanced Yutaki models), additional sensors are available:

### Secondary Compressor Metrics

| Sensor | Description | Unit |
|--------|-------------|------|
| **Secondary Discharge Temperature** | Secondary cycle discharge temp | °C |
| **Secondary Suction Temperature** | Secondary cycle suction temp | °C |
| **Secondary Discharge Pressure** | Secondary cycle high pressure | bar |
| **Secondary Suction Pressure** | Secondary cycle low pressure | bar |
| **Secondary Compressor Frequency** | Secondary compressor speed | Hz |
| **Secondary Compressor Current** | Secondary compressor current draw | A |
| **Secondary Current** | Additional current measurement | A |
| **Secondary Expansion Valve** | Secondary EV position | - |
| **Secondary Superheat** | Superheat measurement | - |
| **Secondary Stop Code** | Secondary cycle stop reason | Code |
| **Secondary Retry Code** | Secondary cycle retry status | Code |

## Using the Sensors

### Performance Monitoring

Monitor your heat pump's efficiency by tracking:
- **Compressor Frequency** vs **Outdoor Temperature** - Lower frequency at moderate temps = good efficiency
- **Discharge Temperature** - Should stay within safe operating range (typically 40-80°C)
- **Current Draw** - Lower current = more efficient operation

### Diagnostic Use

Detect potential issues early:
- **High Discharge Temperature** (>85°C) may indicate low refrigerant or blockage
- **Abnormal Pressures** - Discharge and suction pressures should be within normal ranges
- **Operation Status** stuck in unusual states
- **Frequent Defrost Cycles** may indicate sensor or airflow issues

### Home Automation Examples

```yaml
# Alert on high discharge temperature
automation:
  - alias: "Heat Pump High Discharge Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.compressor_outdoor_unit_discharge_temperature
        above: 80
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Heat pump discharge temperature is high: {{ states('sensor.compressor_outdoor_unit_discharge_temperature') }}°C"

# Track compressor runtime
automation:
  - alias: "Log Compressor Runtime"
    trigger:
      - platform: state
        entity_id: sensor.compressor_outdoor_unit_compressor_frequency
        from: "0"
    action:
      - service: logbook.log
        data:
          name: "Compressor Started"
          message: "Compressor frequency: {{ states('sensor.compressor_outdoor_unit_compressor_frequency') }} Hz"

# Efficiency monitoring
template:
  - sensor:
      - name: "Heat Pump Efficiency"
        unit_of_measurement: "Hz/°C"
        state: >
          {% set freq = states('sensor.compressor_outdoor_unit_compressor_frequency') | float(0) %}
          {% set outdoor = states('sensor.compressor_outdoor_unit_outdoor_ambient_temperature') | float(0) %}
          {% set indoor = states('sensor.system_controller_outdoor_temperature') | float(0) %}
          {% set delta = indoor - outdoor %}
          {% if delta > 0 and freq > 0 %}
            {{ (freq / delta) | round(2) }}
          {% else %}
            0
          {% endif %}
```

## Energy Dashboard Integration

Use compressor sensors to track energy consumption patterns:
- **Compressor Frequency** correlates directly with power usage
- **Compressor Current** provides instantaneous power draw
- Track operation patterns to optimize scheduling

## System Status Flags Decoder

The **System Status Flags** sensor provides decoded attributes:
- `cascade_slave`: System is in cascade slave mode
- `fan_coil_mode`: Fan coil control is active
- `c1_thermostat`: Circuit 1 has thermostat
- `c2_thermostat`: Circuit 2 has thermostat
- `raw_value`: Decimal value of flags
- `hex_value`: Hexadecimal representation

## Data Availability

### Always Available (Primary Cycle)
- Compressor frequency, current, capacity
- Discharge and evaporator temperatures
- Pressures and expansion valve data
- Operation status and outdoor unit information

### Conditionally Available (Secondary Cycle)
- Secondary cycle sensors only populate when:
  - System has dual-cycle configuration
  - Secondary cycle is active
  - Data is being reported by the hardware

**Note**: If secondary sensors show `None` or `Unknown`, your system likely doesn't have a secondary cycle, or it's currently inactive.

## Technical Notes

### Pressure Units
Pressure values are reported in **bar**. To convert:
- **bar to PSI**: multiply by 14.5038
- **bar to kPa**: multiply by 100

### Frequency Range
- **0 Hz**: Compressor is off or idle
- **10-30 Hz**: Low speed operation (mild conditions)
- **40-80 Hz**: Normal operation
- **80-120 Hz**: High demand operation (extreme conditions)

### Invalid Values
The integration automatically filters invalid values:
- `-1` typically means "not available" or "not configured"
- `255` or `127` may indicate uninitialized or invalid readings
- These are returned as `None` in Home Assistant

## Troubleshooting

### Sensors Show "Unknown" or "Unavailable"
- Ensure your system has been running for at least one full refresh cycle
- Check that the CSNet API is responding (check System Controller sensors)
- Some sensors only populate when the system is actively heating/cooling

### Secondary Cycle Sensors Not Populating
- This is normal if your system doesn't have a dual-cycle configuration
- Only advanced Yutaki models typically have secondary cycles
- These sensors can be hidden in Home Assistant if not applicable

### Pressure Values Seem Wrong
- Verify the pressure unit conversion is correct for your region
- Compare with manufacturer specifications for your model
- Pressure sensors may report raw values that need calibration

## Future Enhancements

Potential future additions:
- Historical trending graphs
- Efficiency calculations and COP estimates
- Predictive maintenance alerts
- Cascade system specific metrics
- Power consumption estimates based on frequency/current

---

**Last Updated**: October 2025
**Integration Version**: Compatible with CSNet Home v2.0+

