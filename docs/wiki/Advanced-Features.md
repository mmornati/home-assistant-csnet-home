# Advanced Features Guide

Explore advanced capabilities of the Hitachi CSNet Home integration.

## Overview

Beyond basic climate control, the integration provides several advanced features:

- 🔇 **Silent Mode** - Reduce outdoor unit noise
- 🌀 **Fan Speed Control** - Control fan coil speeds (system dependent)
- 🌡️ **OTC (Outdoor Temperature Compensation)** - Monitor automatic temperature adjustments
- 📊 **Extended Attributes** - Access detailed system information
- ⚙️ **Dynamic Temperature Limits** - Automatic range adjustment based on mode
- 🔔 **Advanced Alarm System** - Comprehensive fault monitoring

---

## Silent Mode

### What is Silent Mode?

Silent mode reduces the noise level of the outdoor unit by limiting compressor and fan speeds. Ideal for nighttime operation or noise-sensitive environments.

**Availability**: Non-fan coil systems only (standard heat pumps)

### How It Works

When silent mode is enabled:
- Outdoor unit operates at reduced capacity
- Fan speeds are limited
- Compressor speed is constrained
- May take longer to reach target temperature
- Energy efficiency may be slightly reduced

### Using Silent Mode

Silent mode is controlled through the climate entity's **fan_mode** attribute.

**Fan Modes** (non-fan coil systems):
- `auto` - Normal operation
- `on` - Silent mode enabled

#### Via UI

1. Open climate entity
2. Click **Fan** button
3. Toggle between Auto and On

**[PLACEHOLDER: Screenshot showing fan mode toggle]**

#### Via Service Call

```yaml
# Enable silent mode
service: climate.set_fan_mode
target:
  entity_id: climate.remote_living_room
data:
  fan_mode: "on"

# Disable silent mode (normal operation)
service: climate.set_fan_mode
target:
  entity_id: climate.remote_living_room
data:
  fan_mode: auto
```

### Automation Examples

#### Automatic Night Silent Mode

```yaml
automation:
  - alias: "Enable Silent Mode at Night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_fan_mode
        target:
          entity_id: all
        data:
          fan_mode: "on"
          
  - alias: "Disable Silent Mode in Morning"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: climate.set_fan_mode
        target:
          entity_id: all
        data:
          fan_mode: auto
```

#### Silent Mode When Home

```yaml
automation:
  - alias: "Silent Mode When Someone Home"
    trigger:
      - platform: state
        entity_id: binary_sensor.someone_home
        to: "on"
    action:
      - service: climate.set_fan_mode
        target:
          entity_id: climate.remote_living_room
        data:
          fan_mode: "on"
```

### Monitoring Silent Mode

Check current silent mode status:

```yaml
# In templates or automations
{{ state_attr('climate.remote_living_room', 'silent_mode') }}
# Returns: 0 (off) or 1 (on)

# Or check fan_mode
{{ state_attr('climate.remote_living_room', 'fan_mode') }}
# Returns: 'auto' or 'on'
```

### Tips for Silent Mode

✅ **Use silent mode when**:
- Sleeping (nighttime)
- Working from home (daytime quiet needed)
- Outdoor unit near windows or neighbors
- Noise sensitivity is priority

❌ **Avoid silent mode when**:
- Quick heating/cooling needed
- Extreme outdoor temperatures
- Maximum efficiency required
- Rapid temperature recovery needed

---

## Fan Speed Control (Fan Coil Systems)

### What is Fan Coil Control?

Some Hitachi systems support fan coil units with controllable fan speeds. These systems can adjust indoor fan speed independently from the heat pump.

**Availability**: Fan coil compatible systems only

### Checking Compatibility

Check if your system supports fan coil control:

```yaml
{{ state_attr('climate.remote_living_room', 'is_fan_coil_compatible') }}
# Returns: true or false
```

Or check sensor:
```yaml
sensor.system_controller_fan_coil_compatible
# State: on or off
```

### Fan Speed Options

Fan coil systems have four speed settings:

| Speed | Description | When to Use |
|-------|-------------|-------------|
| **Off** (0) | Fan off | Not recommended during heating/cooling |
| **Low** (1) | Quiet operation | Sleeping, quiet activities |
| **Medium** (2) | Balanced | Normal operation |
| **Auto** (3) | Automatic control | Let system decide based on demand |

### Using Fan Speed Control

#### Via Service Call

```yaml
service: climate.set_fan_mode
target:
  entity_id: climate.remote_living_room
data:
  fan_mode: medium  # or: off, low, medium, auto
```

### Fan Control Availability

Fan control availability depends on:
- Current HVAC mode (Heat/Cool)
- Circuit configuration
- System settings

Check availability in attributes:

```yaml
fan1_control_available: true
fan2_control_available: false
```

### Automation Examples

#### Auto Speed Based on Temperature Difference

```yaml
automation:
  - alias: "Adjust Fan Speed Based on Temp Difference"
    trigger:
      - platform: template
        value_template: >
          {{ (state_attr('climate.remote_living_room', 'temperature') | float - 
              state_attr('climate.remote_living_room', 'current_temperature') | float) | abs > 3 }}
    action:
      - service: climate.set_fan_mode
        target:
          entity_id: climate.remote_living_room
        data:
          fan_mode: medium
```

#### Low Speed at Night

```yaml
automation:
  - alias: "Low Fan Speed at Night"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('climate.remote_living_room', 'is_fan_coil_compatible') }}
    action:
      - service: climate.set_fan_mode
        target:
          entity_id: climate.remote_living_room
        data:
          fan_mode: low
```

### Monitoring Fan Speed

Check current fan speeds:

```yaml
# For Circuit 1
{{ state_attr('climate.remote_living_room', 'fan1_speed') }}
# Returns: 0-3

# For Circuit 2
{{ state_attr('climate.remote_living_room', 'fan2_speed') }}
# Returns: 0-3
```

### Fan Coil vs Silent Mode

**Important**: Fan coil systems use fan speed control INSTEAD of silent mode.

| System Type | Control Method | Modes |
|-------------|---------------|-------|
| **Standard** | Silent mode | auto, on |
| **Fan Coil** | Fan speed | off, low, medium, auto |

---

## OTC (Outdoor Temperature Compensation)

### What is OTC?

OTC automatically adjusts the water supply temperature based on outdoor temperature to optimize comfort and efficiency.

**Purpose**:
- Maintain consistent indoor temperature
- Improve energy efficiency
- Reduce cycling
- Better comfort in varying weather

### How OTC Works

As outdoor temperature changes:
- **Colder outside** → Higher water temperature
- **Warmer outside** → Lower water temperature

This prevents overheating/overcooling and improves efficiency.

### OTC Types

#### Heating OTC Types

- **None** (0) - No compensation, fixed temperature
- **Points** (1) - Temperature based on defined curve points
- **Gradient** (2) - Linear gradient calculation
- **Fixed** (3) - Fixed water temperature

#### Cooling OTC Types

- **None** (0) - No compensation
- **Points** (1) - Point-based curve
- **Fixed** (2) - Fixed temperature

### Monitoring OTC Settings

Check OTC configuration via sensors:

```yaml
# For C1 Circuit
sensor.system_controller_otc_heating_type_c1
sensor.system_controller_otc_cooling_type_c1

# For C2 Circuit (if applicable)
sensor.system_controller_otc_heating_type_c2
sensor.system_controller_otc_cooling_type_c2
```

Or via climate entity attributes:

```yaml
{{ state_attr('climate.remote_living_room', 'otc_heating_type') }}
{{ state_attr('climate.remote_living_room', 'otc_heating_type_name') }}
```

### OTC Configuration

**Note**: OTC is configured in CSNet Manager, not through Home Assistant. The integration provides monitoring only.

To configure OTC:
1. Open CSNet Manager app/website
2. Go to system settings
3. Find OTC/curve settings
4. Adjust according to your preference

### Dashboard Example

Display OTC status:

```yaml
type: entities
title: OTC Configuration
entities:
  - entity: sensor.system_controller_otc_heating_type_c1
    name: "C1 Heating OTC"
  - entity: sensor.system_controller_otc_cooling_type_c1
    name: "C1 Cooling OTC"
  - entity: sensor.system_controller_otc_heating_type_c2
    name: "C2 Heating OTC"
  - entity: sensor.system_controller_otc_cooling_type_c2
    name: "C2 Cooling OTC"
```

### Understanding OTC Impact

Monitor how OTC affects your system:

```yaml
type: history-graph
title: Temperature Compensation Effect
entities:
  - entity: sensor.system_controller_outdoor_temperature
    name: Outdoor Temp
  - entity: sensor.system_controller_set_water_temperature
    name: Target Water Temp
  - entity: sensor.system_controller_out_water_temperature
    name: Actual Water Temp
hours_to_show: 24
```

---

## Extended Attributes

### Accessing Extended Data

Climate entities expose numerous attributes beyond basic temperature:

```yaml
{{ state_attr('climate.remote_living_room', 'operation_status_text') }}
{{ state_attr('climate.remote_living_room', 'c1_demand') }}
{{ state_attr('climate.remote_living_room', 'alarm_code') }}
```

### Complete Attribute List

**Operation Information**:
- `operation_status` - Numeric status code
- `operation_status_text` - Human-readable status
- `real_mode` - Actual operating mode
- `hvac_action` - Current action (heating/cooling/idle)

**Demand Status**:
- `c1_demand` - Circuit 1 calling for heat/cool
- `c2_demand` - Circuit 2 calling for heat/cool

**System Status**:
- `timer_running` - Timer active
- `doingBoost` - Boost mode active (DHW)
- `silent_mode` - Silent mode status

**Alarm Information**:
- `alarm_code` - Current alarm code (0 = none)
- `alarm_active` - Boolean alarm status
- `alarm_origin` - Where alarm originated
- `alarm_code_formatted` - Formatted for display

**Fan Control** (if applicable):
- `is_fan_coil_compatible` - System supports fan control
- `fan1_speed` - Circuit 1 fan speed (0-3)
- `fan2_speed` - Circuit 2 fan speed (0-3)
- `fan1_control_available` - C1 fan controllable now
- `fan2_control_available` - C2 fan controllable now

**OTC Information**:
- `otc_heating_type` - OTC type code
- `otc_heating_type_name` - OTC type description
- `otc_cooling_type` - Cooling OTC code
- `otc_cooling_type_name` - Cooling OTC description

### Using Attributes in Automations

```yaml
automation:
  - alias: "Alert When Heating Demand Active"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('climate.remote_living_room', 'c1_demand') == true }}
    action:
      - service: notify.mobile_app
        data:
          message: "Zone calling for heat"
```

### Custom Sensors from Attributes

Create dedicated sensors from attributes:

```yaml
# configuration.yaml
sensor:
  - platform: template
    sensors:
      living_room_operation_status:
        friendly_name: "Living Room Operation"
        value_template: >
          {{ state_attr('climate.remote_living_room', 'operation_status_text') }}
      
      living_room_c1_demand:
        friendly_name: "C1 Demand Status"
        value_template: >
          {{ state_attr('climate.remote_living_room', 'c1_demand') }}
```

---

## Dynamic Temperature Limits

### Adaptive Range Control

The integration automatically adjusts temperature limits based on:
- Current HVAC mode (Heat/Cool)
- Zone type (Air/Water circuit)
- System configuration from API

### How It Works

Temperature limits are fetched from CSNet Manager API:

**For Air Circuits** (Zones 1, 2):
- Heating: `heatAirMinC1`/`heatAirMaxC1` (typically 8-55°C)
- Cooling: `coolAirMinC1`/`coolAirMaxC1` (typically 18-30°C)

**For Water Circuits** (Zone 5):
- Heating: `heatMinC1`/`heatMaxC1`
- Cooling: `coolMinC1`/`coolMaxC1`

**For DHW** (Zone 3):
- Min: 30°C (constant)
- Max: `dhwMax` from API (typically 55°C)

### Checking Current Limits

```yaml
{{ state_attr('climate.remote_living_room', 'min_temp') }}
{{ state_attr('climate.remote_living_room', 'max_temp') }}
```

Limits change automatically when you switch between Heat and Cool modes.

### Benefits

✅ **Safety**: Prevents setting temperatures outside safe ranges  
✅ **Efficiency**: Respects system capabilities  
✅ **Flexibility**: Adapts to your specific configuration  
✅ **Accuracy**: Uses actual limits from your system

---

## Advanced Alarm Monitoring

### Alarm System Features

The integration provides comprehensive alarm monitoring:

**Per-Zone Alarms**:
- `alarm_code` - Numeric code
- `alarm_active` - Boolean status
- `alarm_message` - Translated description
- `alarm_code_formatted` - Display format
- `alarm_origin` - Component source

**System-Wide Alarms**:
- `sensor.alarm_history` - Recent alarm log
- `sensor.total_alarm_count` - Active alarm count
- `sensor.active_alarm_count` - Currently active
- `sensor.alarms_by_origin` - Grouped by source

### Enhanced Alarm Notifications

Create sophisticated alarm handling:

```yaml
automation:
  - alias: "Smart Alarm Notification"
    trigger:
      - platform: state
        entity_id: sensor.remote_living_room_alarm_active
        to: "on"
        for: "00:02:00"  # Wait 2 minutes to avoid transients
    action:
      - variables:
          alarm_code: "{{ state_attr('climate.remote_living_room', 'alarm_code') }}"
          alarm_origin: "{{ state_attr('climate.remote_living_room', 'alarm_origin') }}"
          alarm_message: "{{ states('sensor.remote_living_room_alarm_message') }}"
      
      - service: notify.mobile_app
        data:
          title: "Heat Pump Alarm"
          message: >
            Alarm {{ alarm_code }} detected
            Origin: {{ alarm_origin }}
            {{ alarm_message }}
          data:
            priority: high
            tag: hitachi_alarm
      
      - service: persistent_notification.create
        data:
          title: "System Alarm"
          message: >
            **Alarm Code**: {{ alarm_code }}
            **Origin**: {{ alarm_origin }}
            **Description**: {{ alarm_message }}
            **Time**: {{ now().strftime('%Y-%m-%d %H:%M') }}
          notification_id: hitachi_alarm_{{ alarm_code }}
```

### Alarm History Dashboard

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Current Alarms
    entities:
      - sensor.total_alarm_count
      - sensor.active_alarm_count
      
  - type: markdown
    title: Recent Alarm History
    content: >
      {% set alarms = state_attr('sensor.alarm_history', 'recent_alarms') %}
      {% if alarms %}
      {% for alarm in alarms[:5] %}
      - **{{ alarm.code }}**: {{ alarm.description }}
        *{{ alarm.timestamp }}*
      {% endfor %}
      {% else %}
      No recent alarms
      {% endif %}
```

### Alarm Statistics

Track alarm patterns:

```yaml
sensor:
  - platform: history_stats
    name: "Alarms Today"
    entity_id: sensor.total_alarm_count
    state: "on"
    type: count
    start: "{{ now().replace(hour=0, minute=0, second=0) }}"
    end: "{{ now() }}"
```

---

## Performance Optimization

### Scan Interval Tuning

Balance responsiveness vs API load:

```yaml
# In configuration
# Default: 60 seconds

# More responsive (minimum recommended):
scan_interval: 30

# Less API calls:
scan_interval: 120

# Minimal updates:
scan_interval: 300
```

**Recommendations**:
- **Active monitoring**: 30-60 seconds
- **Normal use**: 60-90 seconds  
- **Background**: 120-180 seconds
- **Vacation**: 300+ seconds

### Conditional Updates

Update more frequently when heating:

```yaml
automation:
  - alias: "Faster Updates When Heating"
    trigger:
      - platform: state
        entity_id: climate.remote_living_room
        attribute: hvac_action
        to: "heating"
    action:
      - service: csnet_home.set_scan_interval
        data:
          scan_interval: 30
          
  - alias: "Normal Updates When Idle"
    trigger:
      - platform: state
        entity_id: climate.remote_living_room
        attribute: hvac_action
        to: "idle"
        for: "00:05:00"
    action:
      - service: csnet_home.set_scan_interval
        data:
          scan_interval: 120
```

---

## Best Practices

### ✅ DO

- **Monitor system health** via extended attributes
- **Use silent mode** appropriately (nighttime)
- **Check OTC configuration** for your climate
- **Set up alarm notifications** for important issues
- **Tune scan_interval** based on needs
- **Leverage extended attributes** in automations

### ❌ DON'T

- **Don't use silent mode** when maximum heating needed
- **Don't ignore alarms** - they indicate real issues
- **Don't modify OTC** without understanding impact
- **Don't set scan_interval < 30 seconds**
- **Don't rely solely on one monitoring method**

---

## Next Steps

Explore related documentation:
- **[Multi-Zone Configuration](Multi-Zone-Configuration)** - Managing multiple circuits
- **[Sensors Reference](Sensors-Reference)** - Complete sensor list
- **[Climate Control](Climate-Control)** - Climate entity control with automation examples
- **[Troubleshooting](Troubleshooting)** - Issue resolution

---

**[← Back to Sensors](Sensors-Reference)** | **[Next: Multi-Zone Config →](Multi-Zone-Configuration)**

