# Water Heater Control Guide

Learn how to control your Domestic Hot Water (DHW) system through Home Assistant.

## Overview

If your Hitachi system includes a DHW (Domestic Hot Water) heater, it appears as a **water_heater entity** in Home Assistant. This provides full control over your hot water production.

**Available Controls**:
- **Temperature** - Set target water temperature (whole degrees)
- **Operation Mode** - Off, Eco, Performance (Boost)
- **Status** - Current water temperature monitoring

!!! note "Swimming pool"
    A swimming pool circuit is also exposed as a water_heater entity, with only `off`/`on` modes and a 24-33°C range. See [Swimming Pool](Advanced-Features.md#swimming-pool).

---

## Entity Naming

The water heater entity is named after the DHW zone name reported by CSNet Manager:

**Format**: `water_heater.{zone_name}`

Its device is named `{Device Name}-{Zone Name}`.

!!! note
    The examples on this page use `water_heater.remote_dhw` as a placeholder. Replace it with the entity ID shown in **Settings → Devices & Services → Entities**.

---

## Operation Modes

The water heater supports three operation modes. They map to the unit's DHW run/stop (`runStopDHW`) and DHW boost (`boostDHW`) settings:

| Mode | runStopDHW | boostDHW |
|------|-----------|----------|
| `off` | 0 | unchanged |
| `eco` | 1 | 0 |
| `performance` | 1 | 1 |

The current mode is read back from the unit: `off` when DHW is stopped, `performance` while the unit reports a boost in progress (`doingBoost`), `eco` otherwise.

### Off Mode

**Description**: DHW heating is disabled

**When to use**:
- Extended periods away from home
- Summer when hot water not needed
- Maintenance or service

**Energy use**: None

```yaml
service: water_heater.set_operation_mode
target:
  entity_id: water_heater.remote_dhw
data:
  operation_mode: "off"
```

### Eco Mode (Standard)

**Description**: Normal energy-efficient hot water production

**When to use**:
- Normal daily operation
- Standard hot water needs
- Energy-conscious heating

**Energy use**: Standard/efficient

**Behavior**:
- Heats water to target temperature
- Maintains temperature efficiently
- Uses standard heating cycle

```yaml
service: water_heater.set_operation_mode
target:
  entity_id: water_heater.remote_dhw
data:
  operation_mode: "eco"
```

### Performance Mode (Boost)

**Description**: Requests the unit's DHW boost, for high hot water demand. What the boost does exactly is defined by the unit's configuration.

**When to use**:
- Filling a bath
- Multiple showers needed
- High hot water demand events
- Recovering from low temperature

**Energy use**: High/intensive

**Behavior** (depends on the unit's configuration):
- Starts a DHW boost on the unit
- Typically heats the tank faster, at a higher energy cost

```yaml
service: water_heater.set_operation_mode
target:
  entity_id: water_heater.remote_dhw
data:
  operation_mode: "performance"
```


---

## Temperature Control

### Setting Target Temperature

The water heater allows you to set your desired hot water temperature.

**Temperature Range**:
- **Minimum**: 30°C (fixed)
- **Maximum**, in order of priority:
  1. [Maximum Temperature Override](Configuration-Guide.md#field-details), if set
  2. The DHW maximum reported by the unit (`dhwMax`)
  3. 80°C
- **Recommended**: 50-55°C for domestic use

Setpoints are sent as whole degrees.

**Via UI**:
1. Open the water heater entity
2. Use temperature controls
3. Adjust to desired temperature

**Via Service Call**:
```yaml
service: water_heater.set_temperature
target:
  entity_id: water_heater.remote_dhw
data:
  temperature: 50
```

**Via Automation**:
```yaml
automation:
  - alias: "Morning Hot Water Boost"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.remote_dhw
        data:
          temperature: 55
```

### Current Temperature

Monitor the actual water temperature. It is read from the unit's DHW tank temperature (`tempDHW`):

```yaml
{{ state_attr('water_heater.remote_dhw', 'current_temperature') }}
```

### Target Temperature

Check the current setpoint:

```yaml
{{ state_attr('water_heater.remote_dhw', 'temperature') }}
```

---

## Complete Attributes

Water heater entities provide these attributes:

```yaml
water_heater.remote_dhw:
  state: eco  # or off, performance
  attributes:
    current_temperature: 48
    temperature: 50
    min_temp: 30
    max_temp: 55      # dhwMax from your unit, or the override
    operation_list:
      - "off"
      - eco
      - performance
    operation_mode: eco
    supported_features: 3   # target temperature + operation mode
```

### Related Sensors

| Sensor | Entity (pattern) | What it shows |
|--------|------------------|---------------|
| DHW zone sensors | `sensor.{device}_{zone}_current_temperature`, `_setting_temperature`, `_on_off`, `_doingboost` | Same values as the water heater entity |
| Heat Exchanger Water Outlet Temperature | `sensor.system_controller_heat_exchanger_water_outlet_temperature` | Water leaving the heat pump's exchanger; used for output power while producing DHW |
| External Tank Temperature | `sensor.system_controller_external_tank_temperature` | Third outlet probe (TWO3), if fitted |
| DHW Daily COP | `sensor.system_controller_dhw_daily_cop` | Estimated COP of DHW production today |

See [Sensors Reference](Sensors-Reference.md) for details.

---

## Lovelace UI Examples

### Basic Water Heater Card

```yaml
type: thermostat
entity: water_heater.remote_dhw
```


### Detailed Water Heater Card

```yaml
type: vertical-stack
cards:
  - type: thermostat
    entity: water_heater.remote_dhw
    name: Hot Water
    
  - type: entities
    title: DHW Status
    entities:
      - entity: water_heater.remote_dhw
        name: Operation Mode
      - type: attribute
        entity: water_heater.remote_dhw
        attribute: current_temperature
        name: Current Temperature
        suffix: "°C"
      - type: attribute
        entity: water_heater.remote_dhw
        attribute: temperature
        name: Target Temperature
        suffix: "°C"
```

### Mode Control Buttons

```yaml
type: horizontal-stack
cards:
  - type: button
    name: "Off"
    icon: mdi:water-off
    tap_action:
      action: call-service
      service: water_heater.set_operation_mode
      service_data:
        entity_id: water_heater.remote_dhw
        operation_mode: "off"
        
  - type: button
    name: "Eco"
    icon: mdi:leaf
    tap_action:
      action: call-service
      service: water_heater.set_operation_mode
      service_data:
        entity_id: water_heater.remote_dhw
        operation_mode: eco
        
  - type: button
    name: "Boost"
    icon: mdi:fire
    tap_action:
      action: call-service
      service: water_heater.set_operation_mode
      service_data:
        entity_id: water_heater.remote_dhw
        operation_mode: performance
```

### Custom Water Heater Dashboard

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "## Domestic Hot Water"
    
  - type: glance
    entities:
      - entity: water_heater.remote_dhw
        name: Mode
      - entity: water_heater.remote_dhw
        name: Current
        attribute: current_temperature
      - entity: water_heater.remote_dhw
        name: Target
        attribute: temperature
        
  - type: horizontal-stack
    cards:
      - type: button
        name: "Eco"
        icon: mdi:leaf
        icon_height: 40px
        tap_action:
          action: call-service
          service: water_heater.set_operation_mode
          service_data:
            entity_id: water_heater.remote_dhw
            operation_mode: eco
            
      - type: button
        name: "Boost"
        icon: mdi:fire
        icon_height: 40px
        tap_action:
          action: call-service
          service: water_heater.set_operation_mode
          service_data:
            entity_id: water_heater.remote_dhw
            operation_mode: performance
  
  - type: thermostat
    entity: water_heater.remote_dhw
```

---

## Automation Examples

### Morning Boost for Showers

```yaml
automation:
  - alias: "Morning DHW Boost"
    description: "Boost hot water before morning showers"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: performance
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.remote_dhw
        data:
          temperature: 55
      - delay: "01:00:00"
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: eco
```

### Temperature Schedule

```yaml
automation:
  - alias: "DHW Temperature Schedule"
    trigger:
      - platform: time
        at: "06:00:00"
        id: morning
      - platform: time
        at: "22:00:00"
        id: night
    action:
      - choose:
          - conditions:
              - condition: trigger
                id: morning
            sequence:
              - service: water_heater.set_temperature
                target:
                  entity_id: water_heater.remote_dhw
                data:
                  temperature: 55
                  
          - conditions:
              - condition: trigger
                id: night
            sequence:
              - service: water_heater.set_temperature
                target:
                  entity_id: water_heater.remote_dhw
                data:
                  temperature: 45
```

### Vacation Mode

```yaml
automation:
  - alias: "Vacation - Turn Off DHW"
    trigger:
      - platform: state
        entity_id: input_boolean.vacation_mode
        to: "on"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: "off"
          
  - alias: "Return From Vacation - Enable DHW"
    trigger:
      - platform: state
        entity_id: input_boolean.vacation_mode
        to: "off"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: eco
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.remote_dhw
        data:
          temperature: 50
```

### Energy Optimization

```yaml
automation:
  - alias: "DHW Heat During Cheap Electricity"
    trigger:
      - platform: time
        at: "02:00:00"  # Off-peak hours
    condition:
      - condition: numeric_state
        entity_id: water_heater.remote_dhw
        attribute: current_temperature
        below: 50
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: performance
      - wait_template: "{{ state_attr('water_heater.remote_dhw', 'current_temperature') >= 55 }}"
        timeout: "03:00:00"
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: eco
```

### Low Temperature Alert

```yaml
automation:
  - alias: "Alert on Low DHW Temperature"
    trigger:
      - platform: numeric_state
        entity_id: water_heater.remote_dhw
        attribute: current_temperature
        below: 40
        for: "00:30:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Hot Water Low"
          message: "DHW temperature is {{ state_attr('water_heater.remote_dhw', 'current_temperature') }}°C"
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: performance
```

### Boost Button (Helper)

Create an input_boolean helper for manual boost:

```yaml
# configuration.yaml
input_boolean:
  dhw_boost:
    name: DHW Boost Mode
    icon: mdi:fire

automation:
  - alias: "DHW Boost Button On"
    trigger:
      - platform: state
        entity_id: input_boolean.dhw_boost
        to: "on"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: performance
          
  - alias: "DHW Boost Button Off"
    trigger:
      - platform: state
        entity_id: input_boolean.dhw_boost
        to: "off"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: eco
          
  - alias: "DHW Auto-disable Boost After 2 Hours"
    trigger:
      - platform: state
        entity_id: input_boolean.dhw_boost
        to: "on"
        for: "02:00:00"
    action:
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.dhw_boost
```

---

## Monitoring & Notifications

### Temperature Tracking

Track water temperature over time:

```yaml
# configuration.yaml
sensor:
  - platform: history_stats
    name: DHW Heating Time Today
    entity_id: water_heater.remote_dhw
    state: "performance"
    type: time
    start: "{{ now().replace(hour=0, minute=0, second=0) }}"
    end: "{{ now() }}"
```

### Daily Report

```yaml
automation:
  - alias: "Daily DHW Report"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Daily Hot Water Report"
          message: >
            Current: {{ state_attr('water_heater.remote_dhw', 'current_temperature') }}°C
            Target: {{ state_attr('water_heater.remote_dhw', 'temperature') }}°C
            Mode: {{ states('water_heater.remote_dhw') }}
```

---

## Troubleshooting

### Water Not Heating

**Symptoms**: Temperature not increasing

**Possible Causes**:
1. **Mode is Off** - Check operation mode
2. **Target temperature reached** - Already at setpoint
3. **System prioritizing space heating** - Heat pump priority
4. **Alarm condition** - Check for system alarms

**Solutions**:
- Set mode to Performance for immediate heating
- Check that target > current temperature
- Verify no alarms on climate entities
- Check CSNet Manager app for status

### Temperature Dropping Quickly

**Symptoms**: Water temperature decreases rapidly

**Possible Causes**:
1. **High usage** - Multiple draws
2. **Insufficient capacity** - Tank size vs demand
3. **Mode set to Eco** - Not keeping up with demand

**Solutions**:
- Switch to Performance mode during high-demand periods
- Increase target temperature
- Schedule boost periods before known high usage
- Check for leaks or system issues

### Controls Not Responding

**Symptoms**: Commands sent but no effect

**Possible Causes**:
1. **Connection issue** - Network or API problem
2. **CSNet Manager offline** - Cloud service down
3. **Manual override** - Physical controller changed settings

**Solutions**:
- Check climate entity connectivity
- Verify internet connection
- Check CSNet Manager app
- Restart integration if needed

---

## Tips & Best Practices

### Do

- **Use Eco mode** for normal daily operation
- **Use Performance mode** for high-demand periods (baths, multiple showers)
- **Set temperature to 50-55°C** for legionella prevention and efficiency
- **Schedule boost periods** before predictable high-usage times
- **Turn off when away** for extended periods to save energy
- **Monitor temperature regularly** to ensure adequate supply

### Don't

- **Don't set temperature below 50°C long-term** (legionella risk)
- **Don't exceed 55°C** (unnecessary energy use, scaling risk)
- **Don't leave in Performance mode** continuously (wastes energy)
- **Don't turn off/on frequently** (causes wear)
- **Don't ignore low temperature** alerts (may indicate system issues)

### Pro Tips

1. **Coordinate with heating schedule** - DHW heating reduces space heating capacity
2. **Use off-peak electricity** - Schedule boost during cheap rate periods
3. **Preheat before high usage** - Performance mode 30-60 minutes before needed
4. **Monitor patterns** - Adjust schedule based on actual usage
5. **Winter boost** - May need higher temperatures when inlet water is colder
6. **Legionella prevention** - Ensure temperature reaches 60°C weekly (usually automatic)

---

## Safety Considerations

### Legionella Prevention

Legionella bacteria can grow in water between 20°C and 45°C.

**Recommendations**:
- Maintain DHW temperature at **50°C minimum**
- Heat to **60°C weekly** for legionella cycle (often automatic)
- Don't disable DHW for extended periods without draining

**Note**: Many Hitachi systems have automatic legionella prevention cycles.

### Scalding Prevention

Water above 55°C can cause scalding.

**Recommendations**:
- **Don't exceed 55°C** for domestic use
- Install **thermostatic mixing valves** at points of use
- **Educate household members** about hot water safety
- Use **lower temperatures** (45-50°C) if children or elderly present

### Energy Efficiency

**Best Practices**:
- Use **Eco mode** as default
- Reserve **Performance mode** for actual high-demand situations
- **Insulate pipes** to reduce heat loss
- **Fix leaks promptly** to avoid wasted heating
- **Schedule strategically** to align with usage patterns

---

## Integration with Other Systems

### Solar Hot Water Pre-Heat

If you have solar hot water:

```yaml
automation:
  - alias: "Use Solar Pre-Heat"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_hot_water_temperature
        above: 45
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: eco
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.remote_dhw
        data:
          temperature: 50
```

### Smart Grid Integration

Respond to grid demand:

```yaml
automation:
  - alias: "Grid Demand Response - Reduce DHW"
    trigger:
      - platform: state
        entity_id: binary_sensor.grid_demand_high
        to: "on"
    action:
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.remote_dhw
        data:
          temperature: 45
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.remote_dhw
        data:
          operation_mode: eco
```

---

## Next Steps

Explore related documentation:
- **[Climate Control](Climate-Control.md)** - Control heating zones
- **[Sensors Reference](Sensors-Reference.md)** - All available sensors
- **[Advanced Features](Advanced-Features.md)** - Additional system features
- **[Multi-Zone Configuration](Multi-Zone-Configuration.md)** - Managing multiple circuits

---

**[← Back to Climate Control](Climate-Control.md)** | **[Next: Sensors Reference →](Sensors-Reference.md)**

