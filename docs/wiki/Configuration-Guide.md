# Configuration Guide

This guide will help you configure the Hitachi CSNet Home integration after installation.

## Prerequisites

Before configuring, ensure:

✅ Integration is installed (see [Installation Guide](Installation-Guide))  
✅ Home Assistant has been restarted  
✅ You have your CSNet Manager credentials ready  
✅ Your Hitachi system is connected to CSNet Manager and working

---

## Initial Configuration

### Step 1: Add the Integration

1. Open **Home Assistant**
2. Navigate to **Settings** → **Devices & Services**
3. Click the **+ Add Integration** button (bottom right)
4. Search for **"Hitachi"** or **"CSNet"**
5. Click on **Hitachi CSNet Home**

**[PLACEHOLDER: Screenshot of integration search showing Hitachi CSNet Home]**

### Step 2: Enter Your Credentials

You'll see a configuration dialog with the following fields:

| Field | Description | Example |
|-------|-------------|---------|
| **Username** | Your CSNet Manager username | `user@example.com` |
| **Password** | Your CSNet Manager password | `••••••••` |
| **Scan Interval** | Update frequency in seconds (default: 60) | `60` |
| **Language** | Alarm message language | `en` or `fr` |

**[PLACEHOLDER: Screenshot of configuration dialog]**

#### Field Details

**Username & Password**
- Use the **same credentials** you use for:
  - CSNet Manager mobile app
  - CSNet Manager website (www.csnetmanager.com)
- Credentials are stored securely in Home Assistant

**Scan Interval** (Optional)
- How often Home Assistant checks for updates (in seconds)
- **Default**: 60 seconds (recommended)
- **Minimum**: 30 seconds (don't set lower to avoid rate limits)
- **Maximum**: 300 seconds (5 minutes)
- Lower values = more responsive, but more API calls
- Higher values = less responsive, but lower load

**Language** (Optional)
- Choose the language for alarm messages
- **Options**: `en` (English) or `fr` (French)
- **Default**: `en`
- Can be changed later by reconfiguring

### Step 3: Submit Configuration

1. Enter your credentials
2. Adjust scan interval if needed (60 seconds is recommended)
3. Select your preferred language
4. Click **Submit**

### Step 4: Wait for Authentication

The integration will:
1. Connect to CSNet Manager
2. Authenticate your credentials
3. Retrieve your system configuration
4. Create entities for your devices

This usually takes 5-10 seconds.

### Step 5: Verify Success

If successful, you'll see:
- **Configuration created** message
- New devices in **Settings** → **Devices & Services**
- Entities created for your zones and sensors

**[PLACEHOLDER: Screenshot of successful configuration]**

---

## What Gets Created

After configuration, the integration automatically creates entities based on your system.

### Devices

One device is created for **each zone/thermostat** in your system:

**Device Name Format**: `{Device Name}-{Zone Name}`

Example: `Remote-Living Room`

Each device includes:
- Climate entity
- Multiple sensors
- Device information (model, firmware, etc.)

### Entities Per Zone

For **each zone** (C1, C2, etc.), you get:

#### Climate Entity
- **Entity ID**: `climate.{device_name}_{zone_name}`
- **Example**: `climate.remote_living_room`
- Controls temperature, mode, and presets

#### Temperature Sensors
- **Current Temperature**: `sensor.{device}_current_temperature`
- **Target Temperature**: `sensor.{device}_setting_temperature`

#### Status Sensors
- **Mode**: `sensor.{device}_mode` (Heat, Cool, Auto)
- **On/Off**: `sensor.{device}_on_off`
- **Alarm Code**: `sensor.{device}_alarm_code`
- **Alarm Active**: `sensor.{device}_alarm_active`
- **Alarm Message**: `sensor.{device}_alarm_message`
- **Doing Boost**: `sensor.{device}_doingBoost`

#### Device Sensors
- **WiFi Signal**: `sensor.{device}_wifi_signal`
- **Connectivity**: `sensor.{device}_connectivity`
- **Last Communication**: `sensor.{device}_last_communication`

### Water Heater Entity (If applicable)

If your system has DHW (Domestic Hot Water):

- **Entity ID**: `water_heater.{device_name}_dhw`
- **Example**: `water_heater.remote_dhw`
- Controls water heater temperature and operation mode

### System-Wide Sensors

Additional sensors for overall system monitoring:

#### Water System Sensors
- `sensor.system_controller_pump_speed`
- `sensor.system_controller_water_flow`
- `sensor.system_controller_in_water_temperature`
- `sensor.system_controller_out_water_temperature`
- `sensor.system_controller_set_water_temperature`
- `sensor.system_controller_water_pressure`
- `sensor.system_controller_gas_temperature`
- `sensor.system_controller_liquid_temperature`

#### Environmental Sensors
- `sensor.system_controller_outdoor_temperature`
- `sensor.system_controller_outdoor_average_temperature`
- `sensor.system_controller_weather_temperature`

#### System Status Sensors
- `sensor.system_controller_defrost`
- `sensor.system_controller_mix_valve_position`
- `sensor.system_controller_central_control_enabled`
- `sensor.system_controller_unit_model`
- `sensor.system_controller_lcd_software_version`

#### Configuration Sensors
- `sensor.system_controller_fan_coil_compatible`
- `sensor.system_controller_c1_thermostat_present`
- `sensor.system_controller_c2_thermostat_present`
- `sensor.system_controller_cascade_slave_mode`

#### OTC (Outdoor Temperature Compensation) Sensors
- `sensor.system_controller_otc_heating_type_c1`
- `sensor.system_controller_otc_cooling_type_c1`
- `sensor.system_controller_otc_heating_type_c2`
- `sensor.system_controller_otc_cooling_type_c2`

#### Alarm Sensors
- `sensor.alarm_history` - Recent alarm history
- `sensor.total_alarms` - Total alarm count
- `sensor.active_alarms` - Currently active alarms
- `sensor.alarms_by_origin` - Alarms grouped by origin

---

## Configuration Examples

### Example 1: Single Zone with DHW

**System**: Yutaki S with 1 zone and water heater

**Created Entities**:
- `climate.remote_zone_1` - Main zone climate control
- `water_heater.remote_dhw` - Water heater
- `sensor.remote_zone_1_current_temperature`
- `sensor.remote_zone_1_target_temperature`
- Plus all system-wide sensors

### Example 2: Two Zones (C1 and C2)

**System**: Yutaki S with floor heating on 2 floors

**Created Entities**:
- `climate.remote_first_floor` - C1 circuit
- `climate.remote_second_floor` - C2 circuit
- Sensors for each zone
- System-wide sensors

### Example 3: Multi-Zone with DHW

**System**: Yutaki SC with 2 thermostats + DHW

**Created Entities**:
- `climate.remote_living_room` - C1 thermostat
- `climate.remote_bedrooms` - C2 thermostat
- `water_heater.remote_dhw` - Water heater
- All zone sensors
- All system sensors

### Example 4: Fan Coil System

**System**: Fan coil compatible with 2 zones

**Created Entities**:
- `climate.remote_zone_1` - With fan speed control
- `climate.remote_zone_2` - With fan speed control
- Additional fan speed attributes and sensors

---

## Customizing Entity Names

After creation, you can customize entity names:

### Renaming Entities

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Search for your CSNet entities
3. Click on an entity
4. Click the **Settings** icon (gear)
5. Change **Name** and/or **Entity ID**
6. Click **Update**

**[PLACEHOLDER: Screenshot of entity rename dialog]**

### Organizing with Areas

Assign entities to Home Assistant areas:

1. Go to **Settings** → **Devices & Services**
2. Click on your CSNet device
3. Click **Area** dropdown
4. Select or create an area (e.g., "Living Room", "First Floor")
5. Entities will be grouped by area in the UI

### Creating Groups

Group related entities:

```yaml
# configuration.yaml
group:
  heating_first_floor:
    name: First Floor Heating
    entities:
      - climate.remote_first_floor
      - sensor.remote_first_floor_current_temperature
      - sensor.remote_first_floor_target_temperature
```

---

## Advanced Configuration Options

### Adjusting Scan Interval

To change the scan interval after initial setup:

1. Go to **Settings** → **Devices & Services**
2. Find **Hitachi CSNet Home**
3. Click **Configure**
4. Adjust **Scan Interval**
5. Click **Submit**

**Recommendations**:
- **Normal use**: 60-120 seconds
- **Active monitoring**: 30-60 seconds
- **Low priority**: 180-300 seconds

### Changing Language

To change the alarm message language:

1. Go to **Settings** → **Devices & Services**
2. Find **Hitachi CSNet Home**
3. Click **Configure**
4. Change **Language**
5. Click **Submit**
6. Restart Home Assistant to apply changes

### Enabling Debug Logging

For troubleshooting, enable detailed logging:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

After adding, restart Home Assistant and check logs:
- **Settings** → **System** → **Logs**
- Filter for `csnet_home`

---

## Troubleshooting Configuration

### Authentication Failed

**Problem**: "Invalid credentials" or "Authentication failed"

**Solutions**:
1. **Verify credentials**: Test login at [CSNet Manager website](https://www.csnetmanager.com)
2. **Check for typos**: Carefully re-enter username and password
3. **Reset password**: Use CSNet Manager to reset if needed
4. **Check account status**: Ensure account is active

### No Entities Created

**Problem**: Configuration succeeds but no entities appear

**Solutions**:
1. **Wait a few minutes**: Initial sync can take time
2. **Check device**: Go to Settings → Devices & Services → Devices
3. **Restart HA**: Sometimes requires a restart to appear
4. **Check logs**: Look for errors in Settings → System → Logs
5. **Verify CSNet setup**: Ensure devices show in CSNet Manager app

### Wrong Number of Entities

**Problem**: Expected more/fewer zones or sensors

**Solutions**:
1. **Check CSNet Manager**: Verify how many zones are configured there
2. **Review system type**: Some sensors only appear for specific configurations
3. **Check DHW**: Water heater entity only created if DHW is configured
4. **Reload integration**: Try removing and re-adding

### Connection Timeout

**Problem**: Configuration times out

**Solutions**:
1. **Check internet**: Verify Home Assistant can reach internet
2. **Check firewall**: Ensure CSNet Manager domain is accessible
3. **Increase timeout**: May need to wait longer for slow connections
4. **Retry**: Sometimes CSNet Manager servers are slow

### Duplicate Entities

**Problem**: Entities created multiple times

**Solutions**:
1. **Remove old configuration**: Delete the integration completely
2. **Clean up entities**: Manually remove duplicate entities
3. **Restart HA**: Restart before re-adding
4. **Re-add integration**: Configure from scratch

---

## Reconfiguring

To change configuration:

### Option 1: Reconfigure (Keeps Data)

1. Go to **Settings** → **Devices & Services**
2. Find **Hitachi CSNet Home**
3. Click **Configure**
4. Update settings
5. Click **Submit**

### Option 2: Remove and Re-add (Fresh Start)

1. Go to **Settings** → **Devices & Services**
2. Find **Hitachi CSNet Home**
3. Click **⋮** (three dots)
4. Select **Delete**
5. Confirm deletion
6. Wait 10 seconds
7. Add integration again (see Step 1)

**Note**: Removing the integration will:
- ❌ Delete all entities
- ❌ Remove from automations and dashboards
- ❌ Clear historical data
- ✅ Allow fresh configuration

---

## Verifying Configuration

After configuration, verify everything is working:

### Check Climate Entities

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Filter by `climate.`
3. Verify you see your expected zones
4. Click on each to verify current temperature is reading

### Check Water Heater (If applicable)

1. Filter entities by `water_heater.`
2. Verify DHW entity exists
3. Check current temperature reading

### Check Sensors

1. Filter entities by `sensor.`
2. Look for your zone sensors
3. Verify system sensors are reporting
4. Check for any "Unknown" or "Unavailable" states

### Test Controls

1. Open a climate entity
2. Try changing target temperature
3. Verify change reflects in CSNet Manager app
4. Try changing mode (Heat/Cool)
5. Test preset modes (Eco/Comfort)

**[PLACEHOLDER: Screenshot of climate entity card with controls]**

---

## Next Steps

✅ Configuration complete!

Now explore:
- **[Climate Control Guide](Climate-Control)** - Learn to control your zones
- **[Water Heater Control](Water-Heater-Control)** - Manage your DHW
- **[Sensors Reference](Sensors-Reference)** - Understand all sensors
- **[Advanced Features](Advanced-Features)** - Silent mode, fan control, OTC
- **[Automations Guide](Automations-and-Scripts)** - Create smart automations

---

## Getting Help

If you need assistance:
- Check [Troubleshooting](Troubleshooting) for common issues
- Review [FAQ](FAQ) for frequent questions
- Ask in [GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions)
- Report bugs in [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues)

---

**[← Back to Installation](Installation-Guide)** | **[Next: Climate Control →](Climate-Control)**

