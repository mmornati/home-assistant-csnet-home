# Sensors Reference

Complete reference of all sensors provided by the Hitachi CSNet Home integration.

## Overview

The integration creates numerous sensors to monitor your Hitachi heat pump system. Sensors are organized into several categories:

- **🌡️ Zone Sensors** - Per-zone temperature and status
- **💧 Water System Sensors** - Hydraulic system monitoring
- **🌤️ Environmental Sensors** - Outdoor and weather data
- **⚙️ System Status Sensors** - Equipment operation status
- **📡 Device Sensors** - WiFi and connectivity
- **🔔 Alarm Sensors** - Alarm monitoring and history
- **⚙️ Configuration Sensors** - System configuration details
- **🔧 Diagnostic Sensors** - Technical system information

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
**Entity**: `sensor.{device}_{zone}_doingBoost`  
**Values**: `on`, `off`  
**Device Class**: `binary`  
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
**Device Class**: `binary`  
**Description**: Boolean indicator if any alarm is active

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
**Description**: Alarm code formatted for display (hex or decimal)

### Alarm Origin
**Entity**: `sensor.{device}_{zone}_alarm_origin`  
**Values**: Origin description  
**Device Class**: `enum`  
**Description**: Where the alarm originated (for Yutaki systems)

**Possible Origins**:
- Indoor Unit
- Outdoor Unit
- Compressor
- Inverter
- Refrigerant Cycle
- Communication
- etc.

### Unit Type
**Entity**: `sensor.{device}_{zone}_unit_type`  
**Values**: System type identifier  
**Device Class**: `enum`  
**Description**: Type of unit (standard, yutaki, water_heater, fan_coil)

---

## Device Sensors

Monitor WiFi and connectivity for each device.

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

**Example**: `sensor.remote_living_room_wifi_signal`

### Connectivity
**Entity**: `sensor.{device}_connectivity`  
**Values**: `on` (online), `off` (offline)  
**Device Class**: `binary`  
**Description**: Device online status (based on last communication < 10 minutes)

**Usage**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.remote_living_room_connectivity
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
**Description**: ISO 8601 timestamp of last successful communication

**Example Value**: `2025-01-24T15:30:45+00:00`

---

## Water System Sensors

Monitor hydraulic system operation (installation-wide).

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
**Note**: Value is automatically divided by 50 from API response

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
**Description**: Rolling average of outdoor temperature

**Note**: Used for OTC (Outdoor Temperature Compensation) calculations

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
**Device Class**: `binary`  
**Description**: Indicates if defrost cycle is active

**Note**: Heat pump enters defrost periodically in heating mode when outdoor coil ices up

### Mix Valve Position
**Entity**: `sensor.system_controller_mix_valve_position`  
**Unit**: % (0-100)  
**Device Class**: `percentage`  
**Description**: Mixing valve opening percentage

**Purpose**: Mixes return water with supply to achieve target temperature

### Central Control Enabled
**Entity**: `sensor.system_controller_central_control_enabled`  
**Values**: `on`, `off`  
**Device Class**: `binary`  
**Description**: Indicates if central control is properly configured

**Requirements for "On"**:
- Central config ≥ 3 (Total Control), OR
- LCD software version ≥ 0x0222 (for non-S80 models)

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

**Example Value**: `0x0222` (version 2.34)

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
**Device Class**: `binary`  
**Description**: Indicates if system supports fan coil control

**Determined by**: `systemConfigBits & 0x2000`

### C1 Thermostat Present
**Entity**: `sensor.system_controller_c1_thermostat_present`  
**Values**: `on`, `off`  
**Device Class**: `binary`  
**Description**: Indicates if C1 circuit thermostat is installed

**Determined by**: `systemConfigBits & 0x40`

### C2 Thermostat Present
**Entity**: `sensor.system_controller_c2_thermostat_present`  
**Values**: `on`, `off`  
**Device Class**: `binary`  
**Description**: Indicates if C2 circuit thermostat is installed

**Determined by**: `systemConfigBits & 0x80`

### Cascade Slave Mode
**Entity**: `sensor.system_controller_cascade_slave_mode`  
**Values**: `on`, `off`  
**Device Class**: `binary`  
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

## Alarm Sensors

Monitor system alarms and history.

### Alarm History
**Entity**: `sensor.alarm_history`  
**State**: Number of alarms in history  
**Description**: Count and details of recent alarms

**Attributes**:
```yaml
recent_alarms:
  - code: 42
    description: "Alarm description"
    timestamp: "2025-01-24T10:30:00"
    device: "Remote"
total_alarms: 5
last_updated: "2025-01-24T15:00:00"
```

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
**Entity**: `sensor.total_alarm_count`  
**State**: Count of currently active alarms  
**Description**: Total number of active alarm conditions

**Attributes**:
```yaml
active_devices:
  - device: "Remote"
    room: "Living Room"
    code: 42
    formatted_code: "42"
```

### Active Alarms
**Entity**: `sensor.active_alarm_count`  
**State**: Number of active alarms  
**Description**: Count of currently active alarms

**Attributes**:
```yaml
devices_with_alarms:
  - "Remote - Living Room"
  - "Remote - Bedroom"
```

### Alarms by Origin
**Entity**: `sensor.alarm_by_origin`  
**State**: Count of most common alarm origin  
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
      - sensor.remote_living_room_connectivity
      - sensor.remote_living_room_wifi_signal
      - sensor.system_controller_water_pressure
      - sensor.total_alarm_count
      - sensor.active_alarm_count
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
        entity_id: sensor.remote_living_room_wifi_signal
        below: -75
        for: "00:10:00"
    action:
      - service: notify.mobile_app
        data:
          message: "Device WiFi signal weak: {{ states('sensor.remote_living_room_wifi_signal') }} dBm"
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
- Reduce scan interval if needed
- Check Home Assistant logs

---

## Best Practices

### ✅ DO

- **Group related sensors** for easier dashboard organization
- **Use template sensors** to derive useful metrics
- **Monitor alarm sensors** for system health
- **Track connectivity** to detect communication issues
- **Create notifications** for critical sensor values
- **Use statistics sensors** for trend analysis

### ❌ DON'T

- **Don't poll individual sensors** separately (use integration update)
- **Don't create duplicate sensors** (use existing ones)
- **Don't ignore alarm sensors** (they indicate real issues)
- **Don't set unrealistic thresholds** in automations
- **Don't assume all sensors** exist on all systems

---

## Next Steps

Explore related documentation:
- **[Advanced Features](Advanced-Features)** - Silent mode, fan control, OTC
- **[Climate Control](Climate-Control)** - Using sensors in climate control
- **[Water Heater Control](Water-Heater-Control)** - DHW management
- **[Troubleshooting](Troubleshooting)** - Sensor issues and solutions

---

**[← Back to Water Heater](Water-Heater-Control)** | **[Next: Advanced Features →](Advanced-Features)**

