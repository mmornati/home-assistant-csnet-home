# Sensors Reference

Complete reference of all sensors provided by the Hitachi CSNet Home integration.

## Overview

The integration creates numerous sensors to monitor your Hitachi heat pump system. Sensors are organized into several categories:

- **Zone Sensors** - Per-zone temperature and status
- **Device Sensors** - WiFi and connectivity
- **Water System Sensors** - Hydraulic system and DHW tank monitoring
- **Environmental Sensors** - Outdoor and weather data
- **System Status Sensors** - Equipment operation status
- **Configuration Sensors** - System configuration details
- **OTC Sensors** - Outdoor Temperature Compensation settings
- **Energy and Performance Sensors** - Estimated power, energy and COP
- **Compressor / Outdoor Unit Sensors** - Refrigerant cycle telemetry (see [Compressor Sensors](../COMPRESSOR_SENSORS.md))
- **Alarm Sensors** - Alarm monitoring and history

!!! note "Entity IDs"
    Home Assistant builds entity IDs from the entity name, which comes from your CSNet Manager device and room names. The IDs on this page are patterns: `{device}` is the CSNet device name (often `Remote`) and `{zone}` is the room/zone name. Examples such as `sensor.remote_living_room_current_temperature` are placeholders. If you renamed an entity, or it was created by an older version, your ID may differ — check **Settings → Devices & Services → Entities**.

The integration also creates **number** entities for the fixed water temperature of water circuits; they are described in [Climate Control](Climate-Control.md#number-entities-for-fixed-water-temperature).

---

## Zone Sensors

Created for **each zone/thermostat** in your system.

### Current Temperature
**Entity**: `sensor.{device}_{zone}_current_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: The actual measured temperature in the zone  
**Update Frequency**: Every scan interval (default: 60s)

**Example**: `sensor.remote_living_room_current_temperature`

**Usage in Automations**:
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.remote_living_room_current_temperature
    below: 18
action:
  - service: climate.turn_on
    target:
      entity_id: climate.remote_living_room
```

### Target/Setting Temperature
**Entity**: `sensor.{device}_{zone}_setting_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: The target temperature setpoint  
**Update Frequency**: Every scan interval

**Example**: `sensor.remote_living_room_setting_temperature`

### Operating Mode
**Entity**: `sensor.{device}_{zone}_mode`  
**Values**: `heat`, `cool`, `off`  
**Device Class**: `enum`  
**Description**: Current operating mode of the zone

**Possible Values**:
- `heat` - Heating mode
- `cool` - Cooling mode  
- `off` - System off

### On/Off Status
**Entity**: `sensor.{device}_{zone}_on_off`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Whether the zone is powered on or off

### Doing Boost
**Entity**: `sensor.{device}_{zone}_doingboost`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Indicates if boost mode is active

**Note**: Primarily used for DHW water heater

### Alarm Code
**Entity**: `sensor.{device}_{zone}_alarm_code`  
**Values**: Numeric code (0 = no alarm)  
**Device Class**: `enum`  
**Description**: Current alarm code if any alarm is active

**Values**:
- `0` - No alarm
- `>0` - Alarm code (see alarm code reference)

### Alarm Active
**Entity**: `sensor.{device}_{zone}_alarm_active`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: `on` when the zone's alarm code is non-zero

**Usage**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.remote_living_room_alarm_active
    to: "on"
action:
  - service: notify.mobile_app
    data:
      message: "Alarm detected: {{ state_attr('climate.remote_living_room', 'alarm_code') }}"
```

### Alarm Message
**Entity**: `sensor.{device}_{zone}_alarm_message`  
**Values**: Translated alarm description or null  
**Device Class**: `enum`  
**Description**: Human-readable alarm message in selected language

### Alarm Code Formatted
**Entity**: `sensor.{device}_{zone}_alarm_code_formatted`  
**Values**: Formatted code string  
**Device Class**: `enum`  
**Description**: Alarm code formatted for display. Codes that carry a letter (BCD-encoded) are shown in hexadecimal, others in decimal; `0` means no alarm.

### Alarm Origin
**Entity**: `sensor.{device}_{zone}_alarm_origin`  
**Values**: Origin description  
**Device Class**: `enum`  
**Description**: Component the alarm comes from, translated into the configured language (for example indoor unit, outdoor unit, compressor, inverter, refrigerant cycle, communication). Only filled for `yutaki` and `water_heater` unit types; empty otherwise.

### Unit Type
**Entity**: `sensor.{device}_{zone}_unit_type`  
**Values**: System type identifier  
**Device Class**: `enum`  
**Description**: Type of unit derived from the zone type:

| Value | Zone |
|-------|------|
| `water_heater` | DHW (zone 3) |
| `swimming_pool` | Swimming pool (zone 4) |
| `yutaki` | C1 water circuit (zone 5) |
| `standard` | Everything else |

---

## Device Sensors

Monitor WiFi and connectivity for each device. These sensors are named after the CSNet device only (not the zone).

!!! note
    Device sensors are created once per zone, so a device with several zones gets several identical sensors, which Home Assistant suffixes `_2`, `_3`, and so on. You can disable the duplicates.

### WiFi Signal
**Entity**: `sensor.{device}_wifi_signal`  
**Unit**: dBm  
**Device Class**: `signal_strength`  
**Description**: WiFi signal strength in decibels-milliwatts

**Interpretation**:
- `-30 to -50 dBm` - Excellent
- `-50 to -60 dBm` - Good
- `-60 to -70 dBm` - Fair
- `-70+ dBm` - Poor

**Example**: `sensor.remote_wifi_signal`

### Connectivity
**Entity**: `sensor.{device}_connectivity`  
**Values**: `on` (online), `off` (offline)  
**Device Class**: `enum`  
**Description**: `on` if the device's last communication with CSNet Manager is at most 10 minutes old

**Usage**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.remote_connectivity
    to: "off"
    for: "00:05:00"
action:
  - service: notify.mobile_app
    data:
      message: "Device offline for 5 minutes"
```

### Last Communication
**Entity**: `sensor.{device}_last_communication`  
**Device Class**: `timestamp`  
**Description**: Timestamp (UTC) of the device's last communication with CSNet Manager

---

## Water System Sensors

Monitor hydraulic system operation (installation-wide). These sensors belong to the **System-Controller** device and are named `System Controller …`.

### Pump Speed
**Entity**: `sensor.system_controller_pump_speed`  
**Unit**: % (0-100)  
**Description**: Current water pump speed as percentage

**Example**: `sensor.system_controller_pump_speed`

### Water Flow
**Entity**: `sensor.system_controller_water_flow`  
**Unit**: m³/h (cubic meters per hour)  
**Description**: Water flow rate through the system

**Note**: Value is automatically divided by 10 from API response

### In Water Temperature
**Entity**: `sensor.system_controller_in_water_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Water inlet temperature (return from heating circuits)

### Out Water Temperature
**Entity**: `sensor.system_controller_out_water_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Water outlet temperature (supply to heating circuits)

### External Tank Temperature
**Entity**: `sensor.system_controller_external_tank_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Temperature reported by the third water outlet probe (`waterOutlet3Temp`, TWO3), typically an external tank

### Heat Exchanger Water Outlet Temperature
**Entity**: `sensor.system_controller_heat_exchanger_water_outlet_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Water temperature at the heat pump's heat exchanger outlet (`waterOutletHPTemp`). This is the dedicated DHW tank supply reading: while the unit is producing DHW, the [Output Power](#output-power) calculation uses it instead of the normal outlet temperature.

!!! note
    The DHW tank's own temperature is the `current_temperature` of the water heater entity (read from `tempDHW`). See [Water Heater Control](Water-Heater-Control.md).

### Set Water Temperature
**Entity**: `sensor.system_controller_set_water_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Target water temperature setpoint

**Usage**:
```yaml
trigger:
  - platform: template
    value_template: >
      {{ states('sensor.system_controller_out_water_temperature') | float - 
         states('sensor.system_controller_set_water_temperature') | float > 5 }}
```

### Water Pressure
**Entity**: `sensor.system_controller_water_pressure`  
**Unit**: bar  
**Device Class**: `pressure`  
**Description**: System water pressure

**Normal Range**: 1.0 - 2.5 bar  
**Note**: The raw API value is divided by 50

### Gas Temperature
**Entity**: `sensor.system_controller_gas_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Refrigerant gas temperature

### Liquid Temperature
**Entity**: `sensor.system_controller_liquid_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Refrigerant liquid temperature

---

## Environmental Sensors

Monitor outdoor conditions and weather.

### Outdoor Temperature
**Entity**: `sensor.system_controller_outdoor_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Current outdoor ambient temperature from heat pump sensor

**Also known as**: External temperature

### Outdoor Average Temperature
**Entity**: `sensor.system_controller_outdoor_average_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Average outdoor temperature as reported by the unit (`outdoorAmbientAverageTemp`)

### Weather Temperature
**Entity**: `sensor.system_controller_weather_temperature`  
**Unit**: °C  
**Device Class**: `temperature`  
**Description**: Temperature from CSNet Manager weather service (cloud-based)

**Comparison**:
```yaml
sensor:
  - platform: template
    sensors:
      temperature_difference:
        value_template: >
          {{ (states('sensor.system_controller_outdoor_temperature') | float - 
              states('sensor.system_controller_weather_temperature') | float) | round(1) }}
        unit_of_measurement: "°C"
```

---

## System Status Sensors

Monitor equipment operation.

### Defrost
**Entity**: `sensor.system_controller_defrost`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Indicates if defrost cycle is active

**Note**: Heat pump enters defrost periodically in heating mode when outdoor coil ices up

### Mix Valve Position
**Entity**: `sensor.system_controller_mix_valve_position`  
**Unit**: % (0-100)  
**Description**: Mixing valve opening percentage

**Purpose**: Mixes return water with supply to achieve target temperature

### Central Control Enabled
**Entity**: `sensor.system_controller_central_control_enabled`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Indicates if central control is properly configured

**Requirements for "On"**:
- Central config ≥ 3 (Total Control), OR
- LCD software version ≥ 0x0222, or not yet set (0), for non-S80 models

### Unit Model
**Entity**: `sensor.system_controller_unit_model`  
**Values**: Model name  
**Device Class**: `enum`  
**Description**: Heat pump model type

**Possible Values**:
- `Yutaki S` - Standard model (code 0)
- `Yutaki SC` - Comfort model (code 1)
- `Yutaki S80` - 80°C model (code 2)
- `Yutaki M` - Monobloc (code 3)
- `Yutaki SC Lite` - Lite version (code 4)
- `Yutampo` - Regional model (code 5)

### LCD Software Version
**Entity**: `sensor.system_controller_lcd_software_version`  
**Values**: Version in hex format  
**Description**: LCD controller software version

**Example Value**: `0x0222`

### Central Config
**Entity**: `sensor.system_controller_central_config`  
**Values**: Configuration description  
**Device Class**: `enum`  
**Description**: Central control configuration level

**Possible Values**:
- `Unit Only ⚠️` - Basic control (0)
- `RT Only ⚠️` - Remote only (1)
- `Unit & RT ⚠️` - Combined (2)
- `Total Control` - Full control (3)
- `Total Control+` - Enhanced (4)

**Note**: ⚠️ indicates insufficient control level

---

## Configuration Sensors

System configuration details.

### Fan Coil Compatible
**Entity**: `sensor.system_controller_fan_coil_compatible`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Indicates if system supports fan coil control

**Determined by**: `systemConfigBits & 0x2000`

### C1 Thermostat Present
**Entity**: `sensor.system_controller_c1_thermostat_present`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Indicates if C1 circuit thermostat is installed

**Determined by**: `systemConfigBits & 0x40`

### C2 Thermostat Present
**Entity**: `sensor.system_controller_c2_thermostat_present`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Indicates if C2 circuit thermostat is installed

**Determined by**: `systemConfigBits & 0x80`

### Cascade Slave Mode
**Entity**: `sensor.system_controller_cascade_slave_mode`  
**Values**: `on`, `off`  
**Device Class**: `enum`  
**Description**: Indicates if system is in cascade slave configuration

**Determined by**: `systemConfigBits & 0x1000`

**Note**: Used in multi-unit cascade systems

---

## OTC Sensors

Outdoor Temperature Compensation configuration.

### OTC Heating Type C1
**Entity**: `sensor.system_controller_otc_heating_type_c1`  
**Values**: OTC type name  
**Device Class**: `enum`  
**Description**: OTC type for C1 circuit heating

**Possible Values**:
- `None` (0) - No OTC
- `Points` (1) - Point-based curve
- `Gradient` (2) - Gradient-based
- `Fixed` (3) - Fixed temperature

### OTC Cooling Type C1
**Entity**: `sensor.system_controller_otc_cooling_type_c1`  
**Values**: OTC type name  
**Device Class**: `enum`  
**Description**: OTC type for C1 circuit cooling

**Possible Values**:
- `None` (0) - No OTC
- `Points` (1) - Point-based curve
- `Fixed` (2) - Fixed temperature

When a circuit's OTC type is `Fixed`, a fixed water temperature number entity is created for it. See [Fixed Water Temperature Control](Climate-Control.md#fixed-water-temperature-control-water-circuits-only).

### OTC Heating Type C2
**Entity**: `sensor.system_controller_otc_heating_type_c2`  
**Values**: OTC type name  
**Device Class**: `enum`  
**Description**: OTC type for C2 circuit heating

### OTC Cooling Type C2
**Entity**: `sensor.system_controller_otc_cooling_type_c2`  
**Values**: OTC type name  
**Device Class**: `enum`  
**Description**: OTC type for C2 circuit cooling

**What is OTC?**
Outdoor Temperature Compensation automatically adjusts water temperature based on outdoor conditions for optimal efficiency and comfort.

---

## Energy and Performance Sensors

Installation-wide sensors on the **System-Controller** device. The CSNet API does not report power or energy, so these values are **estimates calculated by the integration** from the unit's telemetry on every poll. Treat them as indicative, not as metered values.

| Sensor | Entity (pattern) | Unit | What it is |
|--------|------------------|------|------------|
| Instant Consumption | `sensor.system_controller_instant_consumption` | W | Estimated electrical input |
| Output Power | `sensor.system_controller_output_power` | W | Thermal output (heating **or** cooling) |
| Instant COP | `sensor.system_controller_instant_cop` | – | Output Power ÷ Instant Consumption |
| Daily Consumption | `sensor.system_controller_daily_consumption` | kWh | Estimated electrical energy today |
| Daily Output Energy | `sensor.system_controller_daily_output_energy` | kWh | Thermal energy today (heating and cooling) |
| Daily HVAC COP | `sensor.system_controller_daily_hvac_cop` | – | Today's COP for space heating/cooling |
| DHW Daily COP | `sensor.system_controller_dhw_daily_cop` | – | Today's COP for DHW production |

### Instant Consumption

Estimated from compressor frequency, discharge and suction pressures and discharge temperature, then clamped to the range given by the reported compressor current (current × 230 V up to (current + 0.99) × 230 V). It is `0` when the compressor runs at 0 Hz.

### Output Power

Thermal power = water flow (m³/h) × 1160 × ΔT, in watts.

| Operation status | ΔT used | Outlet temperature used |
|------------------|---------|-------------------------|
| Heating Thermostat On (6) | outlet − inlet | Out Water Temperature |
| Domestic Hot Water On (8) | outlet − inlet | Heat Exchanger Water Outlet Temperature |
| Cooling Thermostat On (3) | inlet − outlet | Out Water Temperature |
| Anything else | – | Output is 0 |

Output is also 0 when ΔT is not positive or the flow is below 0.01 m³/h.

### Instant COP

Output Power divided by Instant Consumption, rounded to 2 decimals. It reports `0` while consumption is below 50 W.

### Daily Sensors

- Integrated from the instant values on each update, reset at local midnight, and restored after a Home Assistant restart.
- **Daily Consumption** and **Daily Output Energy** use state class `total_increasing`, so they can be added to the Energy dashboard (remember they are estimates).
- **Daily HVAC COP** accumulates while the unit is heating or cooling, or defrosting outside DHW production.
- **DHW Daily COP** accumulates while the unit is producing DHW, or defrosting outside space heating.

!!! note "Renamed sensor"
    The daily space-heating COP sensor was renamed from **Daily COP** to **Daily HVAC COP** when cooling support was added. It now has a new unique ID, so Home Assistant creates a new entity; the old one is left orphaned and can be deleted.

---

## Compressor / Outdoor Unit Sensors

Refrigerant cycle telemetry (compressor frequency and current, discharge/evaporator temperatures, pressures, expansion valves, outdoor fan, secondary cycle) is grouped under a separate **Compressor Outdoor Unit** device, with entity IDs such as `sensor.compressor_outdoor_unit_compressor_frequency`.

See the full list in [Compressor Sensors](../COMPRESSOR_SENSORS.md).

---

## Alarm Sensors

Monitor system alarms and history.

### Alarm History
**Entity**: `sensor.alarm_history`  
**State**: Number of alarms returned by the CSNet installation alarms API  
**Description**: Count and details of recent alarms (up to 10 in attributes)

**Attributes**:
```yaml
recent_alarms:
  - id: 138670          # use with the csnet_home.delete_alarm service
    code: 42
    description: "Alarm description"
    timestamp: "<createdAtString from CSNet>"
    recovered: "<recoveredAtString from CSNet>"
    device: 12345        # unitId
total_alarms: 5
last_updated: "<timestamp from CSNet>"
```

An alarm whose `recovered` value is `1980-01-01 00:00:00` is still active. Code `-1` is reported as "System/Communication Error".

**Usage**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.alarm_history
action:
  - service: notify.mobile_app
    data:
      message: >
        New alarm detected: 
        {{ state_attr('sensor.alarm_history', 'recent_alarms')[0].description }}
```

### Total Alarms
**Entity**: `sensor.total_alarms`  
**State**: Number of zones with a non-zero alarm code  
**Description**: Count of zones currently in alarm

**Attributes**:
```yaml
active_devices:
  - device: "Remote"
    room: "Living Room"
    code: 42
    formatted_code: "42"
```

### Active Alarms
**Entity**: `sensor.active_alarms`  
**State**: Number of zones with a non-zero alarm code (same value as Total Alarms)  
**Description**: Count of zones currently in alarm, listed by name in the attributes

**Attributes**:
```yaml
devices_with_alarms:
  - "Remote - Living Room"
  - "Remote - Bedroom"
```

### Alarms by Origin
**Entity**: `sensor.alarms_by_origin`  
**State**: Number of active alarms sharing the most common origin  
**Description**: Alarms grouped by origin component

**Attributes**:
```yaml
origin_distribution:
  Indoor Unit: 2
  Compressor: 1
most_common_origin: "Indoor Unit"
```

---

## Sensor Groups for Dashboards

Organize sensors into useful groups:

### Temperature Monitoring Group

```yaml
# configuration.yaml
group:
  temperature_monitoring:
    name: Temperature Monitoring
    entities:
      - sensor.remote_living_room_current_temperature
      - sensor.remote_bedroom_current_temperature
      - sensor.system_controller_outdoor_temperature
      - sensor.system_controller_in_water_temperature
      - sensor.system_controller_out_water_temperature
```

### System Health Group

```yaml
group:
  system_health:
    name: System Health
    entities:
      - sensor.remote_connectivity
      - sensor.remote_wifi_signal
      - sensor.system_controller_water_pressure
      - sensor.total_alarms
      - sensor.active_alarms
```

### Water System Group

```yaml
group:
  water_system:
    name: Water System
    entities:
      - sensor.system_controller_pump_speed
      - sensor.system_controller_water_flow
      - sensor.system_controller_water_pressure
      - sensor.system_controller_in_water_temperature
      - sensor.system_controller_out_water_temperature
      - sensor.system_controller_set_water_temperature
```

---

## Using Sensors in Automations

### Temperature-Based Automation

```yaml
automation:
  - alias: "Alert if Zone Too Cold"
    trigger:
      - platform: numeric_state
        entity_id: sensor.remote_living_room_current_temperature
        below: 16
        for: "00:30:00"
    action:
      - service: notify.mobile_app
        data:
          message: "Living room temperature is {{ states('sensor.remote_living_room_current_temperature') }}°C"
```

### System Monitoring

```yaml
automation:
  - alias: "Alert on Low Water Pressure"
    trigger:
      - platform: numeric_state
        entity_id: sensor.system_controller_water_pressure
        below: 1.0
        for: "00:05:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Low Water Pressure"
          message: "System pressure is {{ states('sensor.system_controller_water_pressure') }} bar"
      - service: persistent_notification.create
        data:
          title: "System Alert"
          message: "Check water pressure - currently {{ states('sensor.system_controller_water_pressure') }} bar"
```

### WiFi Monitoring

```yaml
automation:
  - alias: "Alert on Weak WiFi"
    trigger:
      - platform: numeric_state
        entity_id: sensor.remote_wifi_signal
        below: -75
        for: "00:10:00"
    action:
      - service: notify.mobile_app
        data:
          message: "Device WiFi signal weak: {{ states('sensor.remote_wifi_signal') }} dBm"
```

---

## Creating Custom Sensors

### Template Sensors

Calculate derived values:

```yaml
# configuration.yaml
sensor:
  - platform: template
    sensors:
      water_temperature_delta:
        friendly_name: "Water Temperature Delta"
        unit_of_measurement: "°C"
        value_template: >
          {{ (states('sensor.system_controller_out_water_temperature') | float - 
              states('sensor.system_controller_in_water_temperature') | float) | round(1) }}
      
      heating_efficiency:
        friendly_name: "Heating Efficiency"
        unit_of_measurement: "%"
        value_template: >
          {% set delta = states('sensor.water_temperature_delta') | float %}
          {% set flow = states('sensor.system_controller_water_flow') | float %}
          {{ (delta * flow * 100 / 10) | round(0) }}
      
      all_zones_comfortable:
        friendly_name: "All Zones Comfortable"
        value_template: >
          {% set zones = [
            'sensor.remote_living_room_current_temperature',
            'sensor.remote_bedroom_current_temperature'
          ] %}
          {% set targets = [
            'sensor.remote_living_room_setting_temperature',
            'sensor.remote_bedroom_setting_temperature'
          ] %}
          {{ zones | zip(targets) | 
             map('map', 'states') | 
             map('map', 'float') | 
             map('apply', 'abs', 'difference') | 
             select('<=', 1.0) | 
             list | length == zones | length }}
```

### Statistics Sensors

Track sensor history:

```yaml
sensor:
  - platform: statistics
    name: "Average Outdoor Temperature"
    entity_id: sensor.system_controller_outdoor_temperature
    state_characteristic: mean
    max_age:
      hours: 24
      
  - platform: statistics
    name: "Water Pressure Statistics"
    entity_id: sensor.system_controller_water_pressure
    state_characteristic: mean
    max_age:
      hours: 168  # 1 week
```

---

## Sensor State Classes

For energy dashboard integration:

```yaml
# Sensors already have appropriate state classes
# But you can create custom ones:

sensor:
  - platform: template
    sensors:
      daily_heating_time:
        friendly_name: "Daily Heating Time"
        unit_of_measurement: "h"
        value_template: >
          {{ state_attr('climate.remote_living_room', 'hvac_action') == 'heating' }}
```

---

## Troubleshooting Sensors

### Sensor Shows "Unavailable"

**Causes**:
1. Integration not fully initialized
2. Device offline
3. Data not available from API

**Solutions**:
- Wait for next update cycle
- Check device connectivity
- Restart integration

### Sensor Shows "Unknown"

**Causes**:
1. Value not provided by your system configuration
2. Feature not supported
3. Initial sync not complete

**Solutions**:
- Check if feature applies to your system type
- Wait for first full data sync
- Some sensors only apply to specific configurations

### Sensor Not Updating

**Causes**:
1. Scan interval too long
2. Connection issues
3. CSNet Manager service problems

**Solutions**:
- Check last_communication timestamp
- Verify connectivity sensor
- Check Home Assistant logs
- Keep the scan interval at 60 seconds or more (see [Configuration Guide](Configuration-Guide.md#scan-interval))

---

## Best Practices

### Do

- **Group related sensors** for easier dashboard organization
- **Use template sensors** to derive useful metrics
- **Monitor alarm sensors** for system health
- **Track connectivity** to detect communication issues
- **Create notifications** for critical sensor values
- **Use statistics sensors** for trend analysis

### Don't

- **Don't poll individual sensors** separately (use integration update)
- **Don't create duplicate sensors** (use existing ones)
- **Don't ignore alarm sensors** (they indicate real issues)
- **Don't set unrealistic thresholds** in automations
- **Don't assume all sensors** exist on all systems

---

## Next Steps

Explore related documentation:
- **[Advanced Features](Advanced-Features.md)** - Silent mode, fan control, OTC
- **[Climate Control](Climate-Control.md)** - Using sensors in climate control
- **[Water Heater Control](Water-Heater-Control.md)** - DHW management
- **[Troubleshooting](Troubleshooting.md)** - Sensor issues and solutions

---

**[← Back to Water Heater](Water-Heater-Control.md)** | **[Next: Advanced Features →](Advanced-Features.md)**

