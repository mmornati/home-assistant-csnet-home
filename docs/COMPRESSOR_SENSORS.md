# Compressor and Outdoor Unit Sensors

## Overview

The CSNet Home integration monitors your heat pump's compressor and outdoor unit through a dedicated device with 28 sensors (17 for the primary cycle, 11 for the secondary cycle). They let you track the real-time performance and health of the refrigerant cycle.

The sensors are created when the CSNet installation devices data is available, and read the `heatingStatus` (primary cycle) and `secondCycle` (secondary cycle) blocks of the first indoor unit.

## Device Structure

All compressor-related sensors are grouped under a dedicated device:

- **Device Name**: `Compressor Outdoor Unit`
- **Manufacturer**: Hitachi
- **Model**: `{type} Outdoor Unit`, where the type comes from the outdoor unit code (`RAS-1`, `RAS-2`, `Yutaki`, `RAD`, or `Unknown`)
- **Software version**: outdoor unit PCB software, shown in hex

Entity IDs follow the pattern `sensor.compressor_outdoor_unit_{sensor_name}`, for example `sensor.compressor_outdoor_unit_compressor_frequency`.

## Primary Compressor Sensors

### Operational Metrics

| Sensor | Description | Unit |
|--------|-------------|------|
| **Compressor Frequency** | Current operating frequency of the compressor (`ouHz`) | Hz |
| **Compressor Current** | Electrical current draw (`ouCurrent`) | A |
| **Compressor Capacity** | Unit capacity value (`unitCapacity`) | - |
| **Operation Status** | Current operational state, as text | - |

**Operation Status** values: `Off`, `Cooling Demand Off`, `Cooling Thermostat Off`, `Cooling Thermostat On`, `Heating Demand Off`, `Heating Thermostat Off`, `Heating Thermostat On`, `Domestic Hot Water Off`, `Domestic Hot Water On`, `Swimming Pool Off`, `Swimming Pool On`, `Alarm` (unknown codes show as `Unknown (n)`). Its attributes are `raw_value`, `status_text` and `defrosting`.

### Temperature Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| **Discharge Temperature** | Temperature of refrigerant leaving the compressor | °C |
| **Evaporator Temperature** | Temperature at the evaporator | °C |
| **Outdoor Ambient Temperature** | Outside air temperature measured at the outdoor unit | °C |

These three values are sent by the API as unsigned bytes; the integration converts them so that sub-zero temperatures are shown correctly.

### Pressure Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| **Discharge Pressure** | High-side refrigerant pressure | bar |
| **Suction Pressure** | Low-side refrigerant pressure | bar |
| **Suction Pressure Correction** | Correction value reported by the unit | - |

### Control & Valve Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| **Expansion Valve Opening (EVI)** | Electronic expansion valve position (`evi`) | % |
| **Expansion Valve Opening (EVO)** | Outdoor expansion valve position (`ouEvo1`) | % |
| **Outdoor Fan RPM** | Speed of the outdoor unit fan | RPM |

### System Information

| Sensor | Description | Values |
|--------|-------------|--------|
| **System Status Flags** | Bitfield of system status (`systemStatus2Flags`) | Hex string, with decoded attributes |
| **Outdoor Unit Code** | Type of outdoor unit | `Unknown`, `RAS-1`, `RAS-2`, `Yutaki`, `RAD`, or `Code n` |
| **Outdoor Unit Capacity Code** | Capacity identifier | Numeric code |
| **Outdoor Unit PCB Software** | Software version of the outdoor unit PCB | Numeric value (the device info shows it in hex) |

## Secondary Cycle Sensors

For systems with a second refrigerant cycle, additional sensors read the `secondCycle` data:

| Sensor | Description | Unit |
|--------|-------------|------|
| **Secondary Discharge Temperature** | Secondary cycle discharge temperature | °C |
| **Secondary Suction Temperature** | Secondary cycle suction temperature | °C |
| **Secondary Discharge Pressure** | Secondary cycle high pressure | bar |
| **Secondary Suction Pressure** | Secondary cycle low pressure | bar |
| **Secondary Compressor Frequency** | Secondary compressor speed | Hz |
| **Secondary Compressor Current** | Secondary compressor current draw | A |
| **Secondary Current** | Additional current measurement | A |
| **Secondary Expansion Valve** | Secondary expansion valve position | - |
| **Secondary Superheat** | Superheat value (`teSH`) | - |
| **Secondary Stop Code** | Secondary cycle stop reason (`Running` when 0) | Code |
| **Secondary Retry Code** | Secondary cycle retry status (`Normal` when 0) | Code |

## Using the Sensors

### Performance Monitoring

Monitor your heat pump by tracking:

- **Compressor Frequency** vs **Outdoor Ambient Temperature** - how hard the compressor works for the conditions
- **Discharge Temperature** - should stay within the manufacturer's operating range
- **Compressor Current** - electrical load of the compressor

For estimated power, energy and COP, use the calculated sensors described in [Energy and Performance Sensors](wiki/Sensors-Reference.md#energy-and-performance-sensors). Instant Consumption is derived from these compressor readings.

### Diagnostic Use

Signs worth investigating:

- **High Discharge Temperature** for long periods
- **Abnormal Pressures** compared with the manufacturer's specifications
- **Operation Status** stuck in unusual states
- **Frequent defrost** (see the `defrosting` attribute of Operation Status)

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

# Track compressor starts
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
```

## System Status Flags Decoder

The **System Status Flags** sensor provides decoded attributes:

- `cascade_slave`: bit `0x1000`
- `fan_coil_mode`: bit `0x2000`
- `c1_thermostat`: bit `0x40`
- `c2_thermostat`: bit `0x80`
- `raw_value`: decimal value of the flags
- `hex_value`: hexadecimal representation

## Data Availability

### Primary Cycle

Primary cycle sensors are populated from `heatingStatus`. Some values only change while the compressor is running.

### Secondary Cycle

Secondary cycle sensors only show values when the unit reports a `secondCycle` block. If they show `Unknown`, your system most likely has no secondary cycle, or it is inactive.

## Technical Notes

### Pressure Units

Pressure values are shown in **bar**. To convert:

- **bar to PSI**: multiply by 14.5038
- **bar to kPa**: multiply by 100

### Invalid Values

Some sensors treat specific raw values as "not available" and report no value instead:

| Sensor | Ignored values |
|--------|----------------|
| Expansion Valve Opening (EVO) | `255`, `-1` |
| Outdoor Fan RPM | `-1` |
| Outdoor Unit PCB Software | `-1` |
| Secondary Discharge / Suction Pressure | `127` |
| Secondary Expansion Valve | `255` |

## Troubleshooting

### Sensors Show "Unknown" or "Unavailable"

- Wait for at least one full refresh cycle
- Check that the System Controller sensors are reporting (same data source)
- Some sensors only change when the system is actively heating/cooling

### Secondary Cycle Sensors Not Populating

- This is normal if your system doesn't have a second refrigerant cycle
- You can disable these sensors in Home Assistant if not applicable

### Pressure Values Seem Wrong

- Compare with the values shown by the unit's own service menu or the manufacturer's specifications for your model
- Report a mismatch on [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues) with a debug log
