# Troubleshooting Guide

Solutions to common issues with the Hitachi CSNet Home integration.

## Quick Diagnosis

Start here to identify your issue:

| Symptom | Likely Category | Jump To |
|---------|----------------|---------|
| Can't find integration when adding | [Installation Issues](#installation-issues) |
| Authentication fails | [Configuration Issues](#configuration-issues) |
| No entities created | [Configuration Issues](#configuration-issues) |
| Entities show "Unavailable" | [Connection Issues](#connection-issues) |
| Controls don't respond | [Control Issues](#control-issues) |
| Wrong temperature readings | [Sensor Issues](#sensor-issues) |
| Alarms appearing | [Alarm Issues](#alarm-issues) |

---

## Installation Issues

### Integration Not Found in Search

**Symptoms**: Can't find "Hitachi CSNet Home" when adding integration

**Causes**:
- Integration not properly installed
- Home Assistant not restarted after installation
- Browser cache showing old data
- File permissions incorrect

**Solutions**:

1. **Verify Installation**:
   ```bash
   ls -la custom_components/csnet_home/
   ```
   Should show: `__init__.py`, `manifest.json`, and other files

2. **Check manifest.json**:
   ```bash
   cat custom_components/csnet_home/manifest.json
   ```
   Should contain valid JSON with `"domain": "csnet_home"`

3. **Fix Permissions** (if needed):
   ```bash
   chmod -R 755 custom_components/csnet_home/
   chown -R homeassistant:homeassistant custom_components/csnet_home/
   ```

4. **Clear Browser Cache**:
   - Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
   - Or clear browser cache completely

5. **Restart Home Assistant**:
   - Settings → System → Restart
   - Wait 2-3 minutes for full restart

6. **Check Logs**:
   - Settings → System → Logs
   - Filter for `csnet_home`
   - Look for loading errors

### Integration Loads But Shows Errors

**Symptoms**: Errors in logs about missing dependencies or import failures

**Causes**:
- Missing Python dependencies
- Incompatible Home Assistant version
- Corrupted files

**Solutions**:

1. **Check Home Assistant Version**:
   - Requires HA 2023.1.0 or newer
   - Update if needed

2. **Reinstall Dependencies**:
   ```bash
   pip install -r custom_components/csnet_home/requirements.txt
   ```

3. **Reinstall Integration**:
   - Delete `custom_components/csnet_home/`
   - Reinstall fresh copy
   - Restart Home Assistant

---

## Configuration Issues

### Authentication Failed

**Symptoms**: "Invalid credentials" or "Authentication failed" error

**Causes**:
- Incorrect username or password
- Typo in credentials
- Account locked or inactive
- CSNet Manager service down

**Solutions**:

1. **Test Credentials**:
   - Open https://www.csnetmanager.com
   - Try logging in with same credentials
   - If login fails, reset password there

2. **Check for Typos**:
   - Re-enter credentials carefully
   - Check for extra spaces
   - Verify caps lock is off

3. **Try Password Reset**:
   - Go to CSNet Manager website
   - Use "Forgot Password" feature
   - Set new password
   - Try again with new password

4. **Check Account Status**:
   - Ensure account is active
   - Verify email is confirmed
   - Check for any account restrictions

5. **Test API Availability**:
   ```bash
   curl -I https://www.csnetmanager.com
   ```
   Should return HTTP 200

### No Entities Created

**Symptoms**: Configuration succeeds but no climate or sensor entities appear

**Causes**:
- No devices in CSNet Manager account
- Devices not properly configured in CSNet Manager
- Initial sync not complete
- Integration crashed during setup

**Solutions**:

1. **Verify Devices in CSNet Manager**:
   - Open CSNet Manager app/website
   - Check that devices appear
   - Verify zones are configured
   - Ensure system is online

2. **Wait for Initial Sync**:
   - Can take 1-2 minutes after configuration
   - Wait for scan_interval (default 60 seconds)
   - Refresh Home Assistant browser

3. **Check Logs for Errors**:
   - Settings → System → Logs
   - Look for `csnet_home` errors
   - Note any exceptions or failed API calls

4. **Enable Debug Logging**:
   ```yaml
   # configuration.yaml
   logger:
     logs:
       custom_components.csnet_home: debug
   ```
   - Restart Home Assistant
   - Try configuration again
   - Check logs for detailed errors

5. **Remove and Re-add**:
   - Delete the integration
   - Restart Home Assistant
   - Add integration again
   - Wait 2-3 minutes

### Wrong Number of Entities

**Symptoms**: Expected more/fewer zones or sensors

**Causes**:
- System configuration differs from expectations
- Some zones disabled in CSNet Manager
- DHW not configured
- Sensors only appear for certain configurations

**Solutions**:

1. **Count Zones in CSNet Manager**:
   - Open CSNet Manager app
   - Count how many thermostats/zones shown
   - Compare with Home Assistant

2. **Check DHW Configuration**:
   - Water heater entity only appears if DHW configured
   - Verify in CSNet Manager settings

3. **Review System Type**:
   - Some sensors only for specific configurations
   - Check `sensor.system_controller_unit_model`
   - Fan coil sensors only on compatible systems

4. **Check Entity Registry**:
   - Settings → Devices & Services → Entities
   - Filter by `csnet`
   - Look for disabled entities

---

## Connection Issues

### Entities Show "Unavailable"

**Symptoms**: All or some entities show as "Unavailable"

**Causes**:
- Internet connection lost
- CSNet Manager service down
- Integration crashed
- Authentication expired

**Solutions**:

1. **Check Internet Connection**:
   ```bash
   ping 8.8.8.8
   ping www.csnetmanager.com
   ```

2. **Check Connectivity Sensor**:
   - Look at `sensor.{device}_connectivity`
   - If "off", device can't reach cloud

3. **Check Last Communication**:
   - Look at `sensor.{device}_last_communication`
   - If timestamp is old, connection lost

4. **Restart Integration**:
   - Settings → Devices & Services
   - Find CSNet Home
   - Click ⋮ → Reload

5. **Check CSNet Manager Status**:
   - Try accessing www.csnetmanager.com
   - If site is down, wait for service restoration

6. **Re-authenticate**:
   - Delete integration
   - Re-add with credentials
   - May need to refresh authentication

### Intermittent Unavailability

**Symptoms**: Entities become unavailable then recover

**Causes**:
- Unstable internet connection
- WiFi signal issues
- CSNet Manager service intermittent
- Scan interval too aggressive

**Solutions**:

1. **Check WiFi Signal**:
   - Monitor `sensor.{device}_wifi_signal`
   - Should be better than -70 dBm
   - Move device or improve WiFi if weak

2. **Increase Scan Interval**:
   - Current default: 60 seconds
   - Try increasing to 120 or 180 seconds
   - Reduces API call frequency

3. **Monitor Connection**:
   ```yaml
   automation:
     - alias: "Log Connection Issues"
       trigger:
         - platform: state
           entity_id: sensor.remote_living_room_connectivity
           to: "off"
       action:
         - service: logbook.log
           data:
             name: "CSNet Connection"
             message: "Device went offline at {{ now() }}"
   ```

4. **Check Network Quality**:
   - Run continuous ping test
   - Check for packet loss
   - Verify DNS resolution

---

## Control Issues

### Temperature Changes Don't Work

**Symptoms**: Set temperature but system doesn't respond

**Causes**:
- System is off
- Temperature already at target
- Eco mode using different setpoint
- Manual override at physical thermostat
- Control sync delay

**Solutions**:

1. **Check HVAC Mode**:
   - Ensure mode is Heat or Cool (not Off)
   - Check climate entity state

2. **Check Current vs Target**:
   - Compare `current_temperature` with `temperature`
   - System won't heat if current > target

3. **Check Operation Status**:
   - Look at `operation_status_text` attribute
   - Verify system is actually running

4. **Wait for Sync**:
   - Changes can take 1-2 minutes to sync
   - Wait for next scan_interval update

5. **Verify in CSNet Manager**:
   - Check if change appears in CSNet app
   - If not, may be API issue

6. **Check for Alarms**:
   - Look at `alarm_code` attribute
   - Alarms may prevent operation

### Mode Changes Don't Work

**Symptoms**: Try to change HVAC mode but it doesn't change

**Causes**:
- Unsupported mode for configuration
- System protection active
- Physical lock-out enabled
- API command failed

**Solutions**:

1. **Check Available Modes**:
   - Look at climate entity attributes
   - `hvac_modes:` shows supported modes

2. **Try via CSNet Manager**:
   - Test if mode change works there
   - If not, physical/system restriction

3. **Check for Errors**:
   - Enable debug logging
   - Look for API response errors

4. **Restart Integration**:
   - Reload CSNet Home integration
   - Try mode change again

### Preset Mode Doesn't Change

**Symptoms**: Eco/Comfort mode doesn't switch

**Causes**:
- Feature not supported on zone
- Temperature limits prevent change
- API command malformed

**Solutions**:

1. **Check Preset Modes Available**:
   - Look at `preset_modes:` attribute
   - Should show `[comfort, eco]`

2. **Verify ecocomfort Value**:
   - Check integration logs for `ecocomfort` field
   - Should be 0 (eco) or 1 (comfort), not -1

3. **Try Temperature Change Instead**:
   - Manually adjust temperature
   - May be more reliable

---

## Sensor Issues

### Sensor Shows "Unknown"

**Symptoms**: Sensor state is "Unknown" or blank

**Causes**:
- Value not provided by your system
- Feature not supported on your model
- Initial data sync incomplete
- Sensor doesn't apply to configuration

**Solutions**:

1. **Wait for Full Sync**:
   - First sync can take 1-2 scan intervals
   - Wait 2-3 minutes after configuration

2. **Check System Type**:
   - Some sensors only on specific models
   - Water sensors require hydraulic system
   - Fan sensors require fan coil configuration

3. **Verify Data in API**:
   - Enable debug logging
   - Check if value exists in `/data/elements` response

4. **Accept as Expected**:
   - Some sensors genuinely not applicable
   - Hide/disable unused sensors

### Temperature Reading Seems Wrong

**Symptoms**: Temperature value doesn't match reality

**Causes**:
- Thermostat location not ideal
- Sync delay (not real-time)
- Unit conversion issue
- Sensor calibration needed

**Solutions**:

1. **Wait for Update**:
   - Sensors update every scan_interval (60s default)
   - Not real-time, small delays normal

2. **Compare with CSNet Manager**:
   - Check temperature in CSNet app
   - Should match (if not, report as bug)

3. **Check Thermostat Location**:
   - Ensure thermostat properly located
   - Not in direct sunlight, draft, or near heat source

4. **Calibrate in CSNet Manager**:
   - Some thermostats can be calibrated
   - Check CSNet Manager settings

### WiFi Signal Showing Weak

**Symptoms**: `sensor.{device}_wifi_signal` shows poor value (< -70 dBm)

**Causes**:
- Device far from WiFi router
- Interference
- WiFi network issues

**Solutions**:

1. **Improve WiFi Coverage**:
   - Move router closer
   - Add WiFi extender/mesh node
   - Use 2.4GHz band (better range)

2. **Reduce Interference**:
   - Change WiFi channel
   - Move away from interfering devices

3. **Check Device Connectivity**:
   - Monitor `sensor.{device}_connectivity`
   - If stable despite weak signal, may be acceptable

---

## Alarm Issues

### Alarm Code Appearing

**Symptoms**: `alarm_code` sensor shows non-zero value

**Causes**:
- Actual system fault
- Temporary condition
- Maintenance required
- System protection activated

**Solutions**:

1. **Check Alarm Message**:
   - Look at `alarm_message` sensor
   - Read `alarm_origin` for location

2. **Check CSNet Manager**:
   - Open CSNet Manager app
   - Look for alarm details there
   - May have more information

3. **Consult Manual**:
   - Look up alarm code in system manual
   - Check [Alarm Code Reference]

4. **Basic Checks**:
   - Is system powered on?
   - Is water pressure adequate (1-2.5 bar)?
   - Is outdoor unit clear of obstructions?
   - Are all valves open?

5. **Reset if Temporary**:
   - Some alarms auto-clear
   - Try turning system off then on
   - Check if alarm clears

6. **Call for Service**:
   - Persistent alarms need professional service
   - Contact Hitachi technician
   - Provide alarm code and description

### False Alarm Notifications

**Symptoms**: Getting alarm notifications but no real issue

**Causes**:
- Transient conditions trigger alarms
- Notification automation too sensitive
- Alarm history sensor updates

**Solutions**:

1. **Add Delay to Automation**:
   ```yaml
   trigger:
     - platform: state
       entity_id: sensor.remote_living_room_alarm_active
       to: "on"
       for: "00:05:00"  # Wait 5 minutes
   ```

2. **Filter by Alarm Code**:
   ```yaml
   condition:
     - condition: template
       value_template: "{{ states('sensor.remote_living_room_alarm_code') | int > 10 }}"
   ```

3. **Check Alarm History**:
   - Review `sensor.alarm_history` attributes
   - See if alarms are clearing quickly

---

## Performance Issues

### High CPU Usage

**Symptoms**: Home Assistant CPU usage high, integration blamed

**Causes**:
- Scan interval too low
- Too many concurrent API calls
- Logging too verbose

**Solutions**:

1. **Increase Scan Interval**:
   - Default 60s is good for most
   - Increase to 120-180s if needed

2. **Disable Debug Logging**:
   - Remove debug logging if enabled
   - Only enable when actively troubleshooting

3. **Check for Loops**:
   - Review automations using CSNet entities
   - Ensure no infinite loops

### Slow Response

**Symptoms**: Commands take long time to execute

**Causes**:
- CSNet Manager API is slow
- Internet connection latency
- Cloud service load

**Solutions**:

1. **This is Normal**:
   - Cloud-based control has inherent latency
   - 5-10 second delays are expected
   - Not same as local control

2. **Check Internet Speed**:
   - Run speed test
   - Ensure adequate bandwidth

3. **Monitor API Response Times**:
   - Enable debug logging temporarily
   - Check how long API calls take

---

## Advanced Troubleshooting

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

Restart Home Assistant, then:
1. Go to Settings → System → Logs
2. Filter for `csnet_home`
3. Reproduce issue
4. Capture logs

### Capture API Response

1. Open browser Developer Tools (F12)
2. Go to www.csnetmanager.com
3. Navigate to Network tab
4. Log in
5. Find `/data/elements` request
6. Copy response JSON

This shows what data your system provides.

### Check Integration State

```yaml
# In Developer Tools → Template
{{ states.climate | selectattr('entity_id', 'search', 'remote') | list }}
{{ state_attr('climate.remote_living_room', 'operation_status') }}
{{ states.sensor | selectattr('entity_id', 'search', 'system_controller') | list }}
```

### Restart Integration

Without removing configuration:
1. Go to Settings → Devices & Services
2. Find Hitachi CSNet Home
3. Click ⋮ (three dots)
4. Click Reload

### Reinstall Clean

Complete reinstall:
1. Settings → Devices & Services
2. Delete CSNet Home integration
3. Restart Home Assistant
4. Delete `custom_components/csnet_home/` folder
5. Reinstall integration files
6. Restart Home Assistant
7. Add integration again

---

## Getting Help

### Before Asking for Help

Gather this information:

1. **Home Assistant version**: Settings → About
2. **Integration version**: Check manifest.json
3. **System type**: Yutaki model, zone configuration
4. **Error messages**: From logs
5. **Steps to reproduce**: What you did before issue

### Where to Get Help

**GitHub Discussions** (Questions):
👉 https://github.com/mmornati/home-assistant-csnet-home/discussions

**GitHub Issues** (Bugs):
👉 https://github.com/mmornati/home-assistant-csnet-home/issues

**When Reporting**:
- Include all information above
- Attach debug logs
- Share elements API response (redact personal info)
- Describe expected vs actual behavior

### Contributing Fixes

Found a bug? Know how to fix it?
1. Fork the repository
2. Create a fix
3. Submit a Pull Request
4. Help others with the same issue!

---

## Common Error Messages

### "Config flow could not be loaded"

**Meaning**: Integration failed to initialize config flow

**Fix**:
- Check installation
- Verify all files present
- Restart Home Assistant

### "Platform error: csnet_home"

**Meaning**: Error loading climate/sensor platform

**Fix**:
- Check logs for specific error
- Verify configuration
- May need reinstall

### "Update failed"

**Meaning**: Coordinator couldn't update data

**Fix**:
- Check internet connection
- Verify authentication
- Check CSNet Manager availability

### "Unknown error occurred"

**Meaning**: Unexpected error in integration

**Fix**:
- Enable debug logging
- Check full error in logs
- Report as bug if persistent

---

## Prevention Tips

### ✅ DO

- Keep Home Assistant updated
- Keep integration updated
- Monitor connectivity sensors
- Have stable internet connection
- Use recommended scan_interval (60s)
- Enable logging when troubleshooting
- Report bugs to help community

### ❌ DON'T

- Set scan_interval < 30 seconds
- Make rapid repeated changes
- Ignore alarm notifications
- Disable without investigating
- Mix multiple integration versions
- Forget to restart after changes

---

## Next Steps

- Return to [Home](Home.md) page
- Check [FAQ](FAQ.md) for quick answers
- Review [Configuration Guide](Configuration-Guide.md)
- Visit [GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues)

---

**[← Back to Home](Home.md)** | **[Next: FAQ →](FAQ.md)**

