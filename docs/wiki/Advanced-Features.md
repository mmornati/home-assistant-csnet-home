# Advanced Features Guide

Explore advanced capabilities of the Hitachi CSNet Home integration.

## Overview

Beyond basic climate control, the integration provides several advanced features:

- **Silent Mode** - Reduce outdoor unit noise
- **Fan Speed Control** - Control fan coil speeds (system dependent)
- **OTC (Outdoor Temperature Compensation)** - Monitor compensation settings, set fixed water temperatures
- **Swimming Pool** - Pool circuit on/off and temperature
- **Energy and COP Estimates** - Calculated power, energy and COP sensors
- **Extended Attributes** - Access detailed system information
- **Dynamic Temperature Limits** - Automatic range adjustment based on mode
- **Alarm Monitoring** - Notifications, filtering, history and alarm deletion

---

## Silent Mode

### What is Silent Mode?

Silent mode switches the unit's silent setting, which reduces outdoor unit noise. Ideal for nighttime operation or noise-sensitive environments.

**Availability**: Climate entities that are not in fan coil mode

### How It Works

The integration only turns the unit's silent mode on or off. How much the unit limits compressor and fan speed is defined by the unit; expect it to take longer to reach the target temperature.

### Using Silent Mode

Silent mode is controlled through the climate entity's **fan_mode** attribute.

**Fan Modes** (non-fan coil systems):
- `auto` - Normal operation
- `on` - Silent mode enabled

#### Via UI

1. Open climate entity
2. Click **Fan** button
3. Toggle between Auto and On


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

Both read bit `0x2000` of the unit's `systemConfigBits`.

### Fan Coil Control Model

The **Fan Coil Control Model** option ([Configuration Guide](Configuration-Guide.md#field-details)) selects how fan modes map to the unit's fan speed values:

| API value | `standard` (default) | `legacy` |
|-----------|----------------------|----------|
| 0 | `off` | `low` |
| 1 | `low` | `medium` |
| 2 | `medium` | `high` |
| 3 | `auto` | `auto` |

| | `standard` | `legacy` |
|--|-----------|----------|
| Fan coil detection | From the unit (`systemConfigBits`) | Every climate entity is treated as fan coil |
| Availability check before setting a speed | Yes (`fanXControlledOnLCD`) | Skipped |
| Fan mode when the unit reports `auto` | Shown as `auto` | Last speed set from Home Assistant is kept |

Use `legacy` only if fan speeds appear shifted or missing with `standard`.

### Fan Speed Options

With the `standard` model, fan coil systems have four speed settings:

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

Fan control availability depends on the unit's `fanXControlledOnLCD` setting for the circuit and the current HVAC mode:

| `fanXControlledOnLCD` | Heat | Cool | Heat/Cool |
|-----------------------|------|------|-----------|
| 0 | No | No | No |
| 1 | Yes | No | No |
| 2 | No | Yes | No |
| 3 | Yes | Yes | Yes |

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
| **No fan coil** | Silent mode | auto, on |
| **Fan coil, `standard` model** | Fan speed | off, low, medium, auto |
| **Fan coil, `legacy` model** | Fan speed | low, medium, high, auto |

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

**Note**: The OTC type and curve are configured in CSNet Manager, not through Home Assistant. When a circuit's OTC type is **Fixed**, Home Assistant can set its fixed water temperature (`fixTempHeatC{n}` / `fixTempCoolC{n}`) through number entities; see [Fixed Water Temperature Control](Climate-Control.md#fixed-water-temperature-control-water-circuits-only).

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

## Swimming Pool

If CSNet Manager reports a swimming pool circuit (zone 4, SWP), the integration creates a **water_heater** entity for it.

| Property | Value |
|----------|-------|
| Entity ID | `water_heater.{zone_name}` (named after the pool zone in CSNet Manager) |
| Device | `{Device Name}-{Zone Name}` |
| Operation modes | `off`, `on` (no eco/performance) |
| Temperature range | 24-33°C, fixed (Maximum Temperature Override does not apply) |
| Setpoint | Whole degrees, sent as `settingTempSWP` |
| On/off | Sent as `runStopSWP` |

The pool zone also gets the usual zone sensors (`sensor.{device}_{zone}_current_temperature`, `_setting_temperature`, `_on_off`, alarm sensors, …), with `unit_type` = `swimming_pool`. The operation status values `Swimming Pool Off` (9) and `Swimming Pool On` (10) show when the unit is working on the pool.

```yaml
# Turn the pool heating on and set 28°C
- service: water_heater.set_operation_mode
  target:
    entity_id: water_heater.pool
  data:
    operation_mode: "on"
- service: water_heater.set_temperature
  target:
    entity_id: water_heater.pool
  data:
    temperature: 28
```

---

## Energy and COP Estimates

The integration calculates electrical consumption, thermal output (heating and cooling) and COP from the unit's telemetry, and accumulates daily energy and COP values that reset at midnight. These are estimates — CSNet Manager does not report metered power.

See [Energy and Performance Sensors](Sensors-Reference.md#energy-and-performance-sensors) for the formulas and the list of sensors.

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

Alarm status, origin, formatted code and message are separate zone sensors (`sensor.{device}_{zone}_alarm_active`, `_alarm_origin`, `_alarm_code_formatted`, `_alarm_message`).

**Fan Control**:
- `fan_coil_model` - Configured fan coil model (`standard` or `legacy`)
- `is_fan_coil_compatible` - Entity is in fan coil mode
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

| Zone | Heating keys | Cooling keys | Defaults (heat / cool) |
|------|--------------|--------------|------------------------|
| C1 air (1) | `heatAirMinC1` / `heatAirMaxC1` | `coolAirMinC1` / `coolAirMaxC1` | 11-35°C / 11-35°C |
| C2 air (2) | `heatAirMinC2` / `heatAirMaxC2` | `coolAirMinC2` / `coolAirMaxC2` | 11-35°C / 11-35°C |
| C1 water (5) | `heatMinC1` / `heatMaxC1` | `coolMinC1` / `coolMaxC1` | 20-80°C / 5-22°C |
| C2 water (6) | `heatMinC2` / `heatMaxC2` | `coolMinC2` / `coolMaxC2` | 20-80°C / 5-22°C |
| DHW (3) | min 30°C (constant), max `dhwMax` | – | 30-80°C |
| Swimming pool (4) | fixed | – | 24-33°C |

- Heating keys are used in Heat mode; Cool **and Heat/Cool** modes use the cooling keys.
- Missing or invalid values fall back to the defaults. Air circuit values above 200 are treated as tenths of a degree (e.g. `350` → 35.0°C).
- If the resulting minimum is not below the maximum, the defaults are used.
- [Maximum Temperature Override](Configuration-Guide.md#field-details) replaces the maximum of every climate entity and of the DHW water heater.

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
- `sensor.alarm_history` - Recent alarm log from CSNet Manager
- `sensor.total_alarms` - Number of zones in alarm
- `sensor.active_alarms` - Zones in alarm, listed in attributes
- `sensor.alarms_by_origin` - Grouped by source

### Built-in Alarm Notifications

Unless disabled, the integration creates Home Assistant persistent notifications on its own — no automation needed:

| Source | When | Title | `notification_id` |
|--------|------|-------|-------------------|
| Zone alarm | A zone's alarm code changes to a new non-zero value | Hitachi Device Alarm | `csnet_home_alarm_{device_id}-{room_id}-{zone_id}` |
| Installation alarm | An installation alarm is active (not yet recovered) | CSNet Home Installation Alarm | `csnet_home_inst_alarm_{alarm_id}` |

Two options control this ([Configuration Guide](Configuration-Guide.md#field-details)):

- **Enable Alarm Notifications** - turn all of the above off
- **Filtered Alarm Codes** - comma-separated codes that never notify (default `-1`, communication errors); applies to both sources

!!! note
    Notifications are not dismissed automatically when the alarm clears; dismiss them yourself, or use the automation in [Auto-Delete on Notification Dismiss](#auto-delete-on-notification-dismiss).

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
          alarm_code: "{{ states('sensor.remote_living_room_alarm_code_formatted') }}"
          alarm_origin: "{{ states('sensor.remote_living_room_alarm_origin') }}"
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
      - sensor.total_alarms
      - sensor.active_alarms
      
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

### Deleting Alarms

The integration provides a service to delete resolved alarms from CSNet Manager.

#### Via Service Call

```yaml
# Delete a specific alarm by ID
service: csnet_home.delete_alarm
data:
  alarm_id: 138670
```

| Field | Required | Description |
|-------|----------|-------------|
| `alarm_id` | Yes | Installation alarm ID, as an integer or a template that renders to one |

To find alarm IDs, check the **Alarm History** sensor's attributes (`recent_alarms` list contains the `id` field). After a successful deletion the integration refreshes its data. Errors (invalid ID, no active session) are written to the Home Assistant log; the service call itself does not fail.

#### Auto-Delete on Notification Dismiss

When an alarm notification is dismissed in Home Assistant, you can automatically delete it from CSNet Manager.

**Note**: Due to file locking issues in some environments, it's recommended to add this automation manually to your `automations.yaml` file rather than using the UI.

```yaml
# Add to your automations.yaml file
- id: delete_csnet_alarm_on_dismiss
  alias: "Delete CSNet alarm when notification is dismissed"
  description: "Delete CSNet alarm when notification is dismissed"
  mode: single
  triggers:
    - trigger: persistent_notification
      update_type:
        - removed
  conditions:
    - condition: template
      value_template: "{{ 'csnet_home_inst_alarm_' in trigger.notification.notification_id }}"
  actions:
    - action: csnet_home.delete_alarm
      data:
        alarm_id: "{{ trigger.notification.notification_id.split('_')[-1] | int }}"
```

**How it works**:
1. The integration creates persistent notifications with ID `csnet_home_inst_alarm_{alarm_id}`
2. When the notification is dismissed (update_type: removed), this automation triggers
3. It extracts the alarm_id from the notification_id
4. Calls the delete_alarm service to remove it from CSNet Manager

---

## Performance Optimization

### Scan Interval Tuning

The scan interval is set in the setup or reconfigure form (default 60 seconds). Each poll makes 3 requests to CSNet Manager.

**Recommendations**:
- **Normal use**: 60-90 seconds
- **Background**: 120-180 seconds
- **Vacation**: 300+ seconds

!!! warning
    Keep it at 60 seconds or more; see [Scan Interval](Configuration-Guide.md#scan-interval). There is no service to change the scan interval at runtime.

---

## Best Practices

### Do

- **Monitor system health** via extended attributes
- **Use silent mode** appropriately (nighttime)
- **Check OTC configuration** for your climate
- **Set up alarm notifications** for important issues
- **Tune scan_interval** based on needs
- **Leverage extended attributes** in automations

### Don't

- **Don't use silent mode** when maximum heating needed
- **Don't ignore alarms** - they indicate real issues
- **Don't modify OTC** without understanding impact
- **Don't set scan_interval below 60 seconds**
- **Don't rely solely on one monitoring method**

---

## Next Steps

Explore related documentation:
- **[Multi-Zone Configuration](Multi-Zone-Configuration.md)** - Managing multiple circuits
- **[Sensors Reference](Sensors-Reference.md)** - Complete sensor list
- **[Climate Control](Climate-Control.md)** - Climate entity control with automation examples
- **[Troubleshooting](Troubleshooting.md)** - Issue resolution

---

**[← Back to Sensors](Sensors-Reference.md)** | **[Next: Multi-Zone Config →](Multi-Zone-Configuration.md)**

