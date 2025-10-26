# Multi-Zone Configuration Guide

Learn how to configure and manage multi-zone Hitachi heat pump systems with C1 and C2 circuits.

## Overview

Multi-zone systems allow independent control of different areas or circuits in your home. This guide covers:

- Understanding zones and circuits
- Configuration examples
- Independent vs coordinated control
- Optimization strategies
- Common scenarios

---

## Understanding Zones vs Circuits

### Circuits (C1, C2)

**Physical hydraulic circuits** from the heat pump:

- **C1 (Circuit 1)**: First heating/cooling circuit
- **C2 (Circuit 2)**: Second heating/cooling circuit (if present)

Each circuit has its own:
- Water supply line
- Temperature control
- Flow regulation

### Zones

**Logical control areas** with thermostats:

- **Zone 1**: Typically C1 Air (first room thermostat)
- **Zone 2**: Typically C2 Air (second room thermostat)
- **Zone 5**: Typically C1 Water (floor heating/radiators)
- **Zone 6**: Typically C2 Water (second water circuit)
- **Zone 3**: DHW (Domestic Hot Water)

### Common Configurations

| Configuration | Circuits | Description |
|--------------|----------|-------------|
| **Single Zone** | C1 only | One thermostat or water circuit |
| **Dual Air Zones** | C1 + C2 | Two room thermostats |
| **Water + Air** | C1 Water + C1 Air | Floor heating + room thermostat |
| **Dual Water** | C1 + C2 Water | Two floor heating zones |
| **Mixed** | Various | Combination of air and water zones |

---

## Configuration Examples

### Example 1: Two-Floor House (Dual Air)

**Setup**:
- First floor: Living room, kitchen, bathroom
- Second floor: Bedrooms

**Configuration**:
- **C1 (Zone 1)**: First floor thermostat
- **C2 (Zone 2)**: Second floor thermostat

**Entities Created**:
```yaml
- climate.remote_first_floor    # C1 control
- climate.remote_second_floor   # C2 control
```

**Benefits**:
- Independent temperature control per floor
- Different schedules possible (e.g., bedrooms cooler at night)
- Energy savings (heat only occupied floors)

**Dashboard Example**:
```yaml
type: vertical-stack
cards:
  - type: thermostat
    entity: climate.remote_first_floor
    name: First Floor
  
  - type: thermostat
    entity: climate.remote_second_floor
    name: Second Floor
  
  - type: entities
    entities:
      - entity: sensor.remote_first_floor_current_temperature
        name: First Floor Temp
      - entity: sensor.remote_second_floor_current_temperature
        name: Second Floor Temp
```

### Example 2: Floor Heating + Room (Mixed)

**Setup**:
- Ground floor: Underfloor heating (water circuit)
- Upper floor: Fan coil or air handler

**Configuration**:
- **C1 Water (Zone 5)**: Floor heating
- **C2 Air (Zone 2)**: Upper floor thermostat

**Entities Created**:
```yaml
- climate.remote_ground_floor    # Water circuit control
- climate.remote_upper_floor     # Air circuit control
```

**Characteristics**:
- Floor heating: Slower response, constant comfort
- Air circuit: Faster response, more reactive
- Different temperature ranges per circuit type

### Example 3: Two Water Zones

**Setup**:
- Zone 1: Living areas floor heating
- Zone 2: Bedrooms floor heating

**Configuration**:
- **C1 Water (Zone 5)**: Living areas
- **C2 Water (Zone 6)**: Bedrooms

**Entities Created**:
```yaml
- climate.remote_living_areas
- climate.remote_bedrooms
```

**Benefits**:
- Different temperatures for different areas
- Schedule bedrooms cooler when empty
- Optimize comfort vs energy per area

---

## Independent vs Coordinated Control

### Independent Control

Each zone operates completely independently:

```yaml
# Set different temperatures
service: climate.set_temperature
target:
  entity_id: climate.remote_first_floor
data:
  temperature: 22

service: climate.set_temperature
target:
  entity_id: climate.remote_second_floor
data:
  temperature: 19
```

**Benefits**:
- Maximum flexibility
- Optimize each zone separately
- Different schedules per zone

**Considerations**:
- Heat pump capacity shared between zones
- One zone's demand affects the other
- May reduce efficiency if settings very different

### Coordinated Control

Control zones together for consistency:

```yaml
# Set all zones to same temperature
service: climate.set_temperature
target:
  entity_id:
    - climate.remote_first_floor
    - climate.remote_second_floor
data:
  temperature: 21
```

**Benefits**:
- Consistent whole-house temperature
- Simpler management
- More predictable behavior

**Use Cases**:
- Vacation mode
- Party/guests (heat whole house)
- Quick temperature changes

---

## Demand Management

### Understanding Demand

Each zone can "demand" heating or cooling from the heat pump:

**Demand Attributes**:
- `c1_demand` - Circuit 1 is calling for heat/cool
- `c2_demand` - Circuit 2 is calling for heat/cool

**Check Demand Status**:
```yaml
{{ state_attr('climate.remote_first_floor', 'c1_demand') }}
{{ state_attr('climate.remote_second_floor', 'c2_demand') }}
```

### Demand-Based Automations

#### Alert When Both Zones Demanding

```yaml
automation:
  - alias: "Alert High Demand"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('climate.remote_first_floor', 'c1_demand') and
             state_attr('climate.remote_second_floor', 'c2_demand') }}
        for: "00:10:00"
    action:
      - service: notify.mobile_app
        data:
          message: "Both zones demanding heat - consider adjusting setpoints"
```

#### Priority Zone

Give priority to one zone when both demand:

```yaml
automation:
  - alias: "Priority to Living Room"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('climate.remote_living_room', 'c1_demand') and
             state_attr('climate.remote_bedroom', 'c2_demand') }}
    action:
      # Reduce bedroom temperature slightly
      - service: climate.set_temperature
        target:
          entity_id: climate.remote_bedroom
        data:
          temperature: >
            {{ state_attr('climate.remote_bedroom', 'temperature') - 1 }}
```

---

## Temperature Scheduling

### Per-Zone Schedules

Create different schedules for each zone:

```yaml
automation:
  # First floor schedule
  - alias: "First Floor Temperature Schedule"
    trigger:
      - platform: time
        at: "06:00:00"
        id: morning
      - platform: time
        at: "23:00:00"
        id: night
    action:
      - choose:
          - conditions:
              - condition: trigger
                id: morning
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.remote_first_floor
                data:
                  temperature: 22
          - conditions:
              - condition: trigger
                id: night
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.remote_first_floor
                data:
                  temperature: 19
  
  # Second floor schedule
  - alias: "Second Floor Temperature Schedule"
    trigger:
      - platform: time
        at: "21:00:00"
        id: bedtime
      - platform: time
        at: "08:00:00"
        id: wake
    action:
      - choose:
          - conditions:
              - condition: trigger
                id: bedtime
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.remote_second_floor
                data:
                  temperature: 18
          - conditions:
              - condition: trigger
                id: wake
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.remote_second_floor
                data:
                  temperature: 20
```

### Occupancy-Based Control

Adjust zones based on occupancy:

```yaml
automation:
  - alias: "Reduce Unoccupied Zone Temperature"
    trigger:
      - platform: state
        entity_id: binary_sensor.first_floor_occupied
        to: "off"
        for: "01:00:00"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.remote_first_floor
        data:
          preset_mode: eco
  
  - alias: "Restore When Occupied"
    trigger:
      - platform: state
        entity_id: binary_sensor.first_floor_occupied
        to: "on"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.remote_first_floor
        data:
          preset_mode: comfort
```

---

## System Monitoring

### Multi-Zone Dashboard

Comprehensive monitoring dashboard:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "## Multi-Zone System"
  
  - type: horizontal-stack
    cards:
      - type: thermostat
        entity: climate.remote_first_floor
        name: First Floor
      - type: thermostat
        entity: climate.remote_second_floor
        name: Second Floor
  
  - type: entities
    title: System Status
    entities:
      - type: attribute
        entity: climate.remote_first_floor
        attribute: c1_demand
        name: C1 Demand
      - type: attribute
        entity: climate.remote_second_floor
        attribute: c2_demand
        name: C2 Demand
      - entity: sensor.system_controller_in_water_temperature
        name: Water In
      - entity: sensor.system_controller_out_water_temperature
        name: Water Out
      - entity: sensor.system_controller_outdoor_temperature
        name: Outdoor
  
  - type: history-graph
    title: Temperature History
    entities:
      - entity: sensor.remote_first_floor_current_temperature
        name: First Floor
      - entity: sensor.remote_second_floor_current_temperature
        name: Second Floor
      - entity: sensor.system_controller_outdoor_temperature
        name: Outdoor
    hours_to_show: 24
```

### Demand Monitoring

Track which zones are demanding:

```yaml
type: entities
title: Zone Demand Status
entities:
  - type: custom:template-entity-row
    entity: climate.remote_first_floor
    name: First Floor
    secondary: >
      {% if state_attr('climate.remote_first_floor', 'c1_demand') %}
        🔥 Demanding
      {% else %}
        ✓ Satisfied
      {% endif %}
  
  - type: custom:template-entity-row
    entity: climate.remote_second_floor
    name: Second Floor
    secondary: >
      {% if state_attr('climate.remote_second_floor', 'c2_demand') %}
        🔥 Demanding
      {% else %}
        ✓ Satisfied
      {% endif %}
```

---

## Optimization Strategies

### Energy Efficiency

#### Strategy 1: Staggered Heating

Avoid both zones demanding simultaneously:

```yaml
automation:
  - alias: "Stagger Zone Heating"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      # Heat first floor first
      - service: climate.set_temperature
        target:
          entity_id: climate.remote_first_floor
        data:
          temperature: 22
      
      # Wait for first floor to reach temperature
      - wait_template: >
          {{ not state_attr('climate.remote_first_floor', 'c1_demand') }}
        timeout: "01:00:00"
      
      # Then heat second floor
      - service: climate.set_temperature
        target:
          entity_id: climate.remote_second_floor
        data:
          temperature: 21
```

#### Strategy 2: Temperature Offsets

Keep zones within a few degrees of each other:

```yaml
automation:
  - alias: "Limit Temperature Spread"
    trigger:
      - platform: state
        entity_id:
          - climate.remote_first_floor
          - climate.remote_second_floor
        attribute: temperature
    condition:
      - condition: template
        value_template: >
          {% set diff = state_attr('climate.remote_first_floor', 'temperature') - 
                       state_attr('climate.remote_second_floor', 'temperature') %}
          {{ diff | abs > 4 }}
    action:
      - service: notify.mobile_app
        data:
          message: "Large temperature difference between zones may reduce efficiency"
```

### Comfort Optimization

#### Maintain Minimum Temperature

Ensure no zone gets too cold:

```yaml
automation:
  - alias: "Minimum Temperature Guard"
    trigger:
      - platform: numeric_state
        entity_id:
          - sensor.remote_first_floor_current_temperature
          - sensor.remote_second_floor_current_temperature
        below: 16
    action:
      - service: climate.set_temperature
        target:
          entity_id: "{{ trigger.entity_id.replace('sensor.', 'climate.').replace('_current_temperature', '') }}"
        data:
          temperature: 19
      - service: climate.turn_on
        target:
          entity_id: "{{ trigger.entity_id.replace('sensor.', 'climate.').replace('_current_temperature', '') }}"
```

#### Pre-heat Before Use

Pre-heat zones before occupancy:

```yaml
automation:
  - alias: "Pre-heat Bedroom Before Bedtime"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.remote_second_floor
        data:
          temperature: 20
      - service: climate.set_preset_mode
        target:
          entity_id: climate.remote_second_floor
        data:
          preset_mode: comfort
```

---

## Troubleshooting Multi-Zone Issues

### One Zone Not Heating

**Symptoms**: One zone stays cold while other heats

**Possible Causes**:
- Zone turned off
- Valve closed or stuck
- Thermostat malfunction
- Priority given to other zone

**Solutions**:
1. Check zone is ON in Home Assistant
2. Check `c1_demand` or `c2_demand` - is zone calling for heat?
3. Verify thermostat battery/power
4. Check valve operation (may need manual check)
5. Temporarily turn off other zone to test

### Zones Fighting Each Other

**Symptoms**: Temperature fluctuates, never settles

**Possible Causes**:
- Setpoints too far apart
- Both zones demanding constantly
- Poor zone isolation

**Solutions**:
1. Reduce temperature difference between zones
2. Check for open doors/airflow between zones
3. Use staggered heating strategy
4. Consider adjusting OTC curves

### Uneven Heating

**Symptoms**: One zone always warmer/cooler than target

**Possible Causes**:
- Different thermal mass (air vs water)
- Poor thermostat placement
- Circuit flow imbalance
- Insulation differences

**Solutions**:
1. Adjust target temperatures to compensate
2. Check thermostat location (not in draft, sun, etc.)
3. Balance flow valves (may need professional)
4. Consider zone-specific temperature offsets

---

## Advanced Multi-Zone Automations

### Smart Load Balancing

```yaml
automation:
  - alias: "Smart Load Balance"
    trigger:
      - platform: time_pattern
        minutes: "/15"  # Check every 15 minutes
    condition:
      # Both zones demanding
      - condition: template
        value_template: >
          {{ state_attr('climate.remote_first_floor', 'c1_demand') and
             state_attr('climate.remote_second_floor', 'c2_demand') }}
    action:
      # Determine which zone is further from target
      - variables:
          zone1_diff: >
            {{ state_attr('climate.remote_first_floor', 'temperature') - 
               state_attr('climate.remote_first_floor', 'current_temperature') }}
          zone2_diff: >
            {{ state_attr('climate.remote_second_floor', 'temperature') - 
               state_attr('climate.remote_second_floor', 'current_temperature') }}
      
      # Prioritize zone with larger deficit
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ zone1_diff > zone2_diff }}"
            sequence:
              - service: climate.set_preset_mode
                target:
                  entity_id: climate.remote_second_floor
                data:
                  preset_mode: eco
        default:
          - service: climate.set_preset_mode
            target:
              entity_id: climate.remote_first_floor
            data:
              preset_mode: eco
```

### Coordinated Away Mode

```yaml
automation:
  - alias: "Multi-Zone Away Mode"
    trigger:
      - platform: state
        entity_id: input_boolean.away_mode
        to: "on"
    action:
      # Set all zones to eco with reduced temperature
      - service: climate.set_preset_mode
        target:
          entity_id:
            - climate.remote_first_floor
            - climate.remote_second_floor
        data:
          preset_mode: eco
      
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.remote_first_floor
            - climate.remote_second_floor
        data:
          temperature: 16
```

---

## Best Practices

### ✅ DO

- **Keep zones within 3-4°C** of each other for efficiency
- **Use staggered heating** when possible
- **Monitor demand status** to understand system behavior
- **Create zone-specific schedules** based on usage
- **Balance comfort vs efficiency** per zone
- **Regular maintenance** of thermostats and valves
- **Use preset modes** (Eco/Comfort) for easy control

### ❌ DON'T

- **Don't set extreme temperature differences** (>5°C)
- **Don't leave unused zones** at high temperatures
- **Don't ignore demand conflicts** - optimize settings
- **Don't forget** zones affect each other
- **Don't override** OTC settings without understanding
- **Don't neglect** physical valve and thermostat maintenance

---

## Next Steps

Explore related documentation:
- **[Climate Control](Climate-Control.md)** - Detailed climate entity control
- **[Advanced Features](Advanced-Features.md)** - Silent mode, fan control, OTC
- **[Sensors Reference](Sensors-Reference.md)** - All available sensors
- **[Water Heater Control](Water-Heater-Control.md)** - DHW management

---

**[← Back to Advanced Features](Advanced-Features.md)** | **[Back to Home](Home.md)**

