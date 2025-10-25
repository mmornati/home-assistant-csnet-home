# Frequently Asked Questions (FAQ)

Quick answers to common questions about the Hitachi CSNet Home integration.

---

## General Questions

### What is this integration?

The Hitachi CSNet Home integration connects your Hitachi heat pump system to Home Assistant using the CSNet Manager cloud service. It allows you to control and monitor your heating/cooling system directly from Home Assistant.

### Which Hitachi systems are supported?

Any Hitachi heat pump equipped with the **ATW-IOT-01 module** that works with the CSNet Manager service. This includes:
- Yutaki S, SC, S80, M models
- Yutampo models  
- Systems with single or multiple zones
- Systems with or without DHW (hot water)
- Fan coil compatible systems

See [Supported Devices](Supported-Devices) for detailed compatibility.

### Do I need a CSNet Manager account?

Yes. You need an active CSNet Manager account with your system registered. This is the same account you use for the CSNet Manager mobile app or website.

### Is this cloud-based or local control?

**Cloud-based**. The integration communicates with Hitachi's CSNet Manager cloud service. It does NOT communicate directly with your heat pump locally. This means:
- ✅ Works from anywhere with internet
- ✅ Uses official Hitachi API
- ❌ Requires internet connection
- ❌ Some latency in commands (5-10 seconds)

### Is this official from Hitachi?

No, this is a **community-developed integration**. It was created by reverse-engineering the CSNet Manager web interface since Hitachi doesn't provide an official API. However, it uses the same methods as the official CSNet Manager app.

---

## Installation & Setup

### How do I install it?

Three methods:
1. **HACS** (recommended) - Easiest updates
2. **Manual from Release** - Download ZIP from GitHub
3. **Manual from Source** - Clone repository

See complete instructions: [Installation Guide](Installation-Guide)

### Do I need HACS?

No, HACS is optional but recommended. You can install manually if you prefer.

### Can I use this with Home Assistant Core?

Yes! The integration works with all Home Assistant installation types:
- Home Assistant OS
- Home Assistant Container (Docker)
- Home Assistant Core (Python venv)
- Home Assistant Supervised

### What Home Assistant version do I need?

Home Assistant 2023.1.0 or newer recommended. Older versions may work but aren't tested.

### How do I update the integration?

**Via HACS**: HACS will notify when updates available. Click Update.

**Manually**: Download new release, replace files, restart Home Assistant.

---

## Configuration

### What credentials do I use?

Use your **CSNet Manager** credentials - the same username and password you use for:
- CSNet Manager mobile app
- CSNet Manager website (www.csnetmanager.com)

### What is the scan interval?

How often Home Assistant checks for updates from CSNet Manager. Default is 60 seconds.

**Recommendations**:
- **60 seconds** - Good balance (default)
- **30-45 seconds** - More responsive (don't go lower)
- **120-180 seconds** - Less API load, slower updates

### Can I change settings after setup?

Yes. Go to Settings → Devices & Services → CSNet Home → Configure.

You can change:
- Scan interval
- Language preference

To change credentials, you need to delete and re-add the integration.

### Why does it need my CSNet password?

The integration must log in to CSNet Manager on your behalf to retrieve data and send commands. Your credentials are stored securely in Home Assistant (encrypted with your instance key).

---

## Features & Capabilities

### What can I control?

**Climate (per zone)**:
- Turn on/off
- Set target temperature
- Change HVAC mode (Heat/Cool/Auto/Off)
- Switch preset (Eco/Comfort)
- Fan modes (silent or speed control)

**Water Heater** (if you have DHW):
- Turn on/off
- Set temperature
- Change mode (Off/Eco/Performance)

### What can I monitor?

**Zone Sensors**:
- Current & target temperature
- Operation status
- Alarm codes
- WiFi signal & connectivity

**System Sensors**:
- Water temperature (in/out)
- Water flow & pressure
- Outdoor temperature
- Pump speed
- Defrost status
- OTC settings
- And many more!

See complete list: [Sensors Reference](Sensors-Reference)

### Can I control multiple zones independently?

Yes! Each zone/thermostat gets its own climate entity that can be controlled independently.

### Does it work with Alexa/Google Home?

Yes, through Home Assistant. If you've connected Home Assistant to Alexa or Google Home, you can expose these climate entities and control them via voice.

### Can I create automations?

Absolutely! All entities can be used in Home Assistant automations, scripts, and scenes. See [Automations Guide](Automations-and-Scripts) for examples.

---

## Operation

### How fast do commands execute?

Commands typically take **5-15 seconds** to execute because they go through the cloud:
1. Home Assistant → CSNet Manager (cloud)
2. CSNet Manager → Your heat pump
3. Confirmation back

This is normal for cloud-based control.

### How often does data update?

Every **scan_interval** seconds (default: 60). Not real-time, but sufficient for most use cases.

### Will this interfere with the CSNet Manager app?

No. Both can be used simultaneously. Changes made in either place will sync (after the next update cycle).

### What happens if my internet goes down?

- Home Assistant loses connection to CSNet Manager
- Entities show "Unavailable"
- You can't control via Home Assistant
- **BUT** your heat pump continues operating with its last settings
- Physical controls still work
- When internet returns, connection restores automatically

### What happens if CSNet Manager service is down?

Same as internet down - you lose control via Home Assistant but the heat pump continues operating normally. You can still use physical controls.

---

## Zones & Circuits

### What's the difference between zones and circuits?

**Circuit** (C1, C2): Physical hydraulic circuit from heat pump
- C1 = First heating circuit
- C2 = Second heating circuit (if present)

**Zone**: Area controlled by a thermostat
- Can be air zones (room thermostats)
- Or water zones (floor heating areas)

### How many zones can I have?

Depends on your system configuration:
- **Single zone**: 1 thermostat, 1 climate entity
- **Dual zone**: 2 thermostats, 2 climate entities
- **With DHW**: Plus 1 water heater entity

### What's Zone 3? Zone 5?

**Internal zone IDs**:
- Zone 1 = C1 Air circuit (room thermostat 1)
- Zone 2 = C2 Air circuit (room thermostat 2)
- Zone 3 = DHW (water heater)
- Zone 4 = (varies by system)
- Zone 5 = C1 Water circuit (floor heating/radiators)
- Zone 6 = C2 Water circuit

### I have floor heating - what zone is that?

Usually Zone 5 (C1 Water) or Zone 6 (C2 Water) depending on circuit.

---

## DHW / Water Heater

### What is DHW?

Domestic Hot Water - your hot water heater/tank.

### Do I get a water heater entity?

Only if your system has DHW configured in CSNet Manager. If you have DHW but no entity, check CSNet Manager configuration.

### What's the difference between Eco and Performance mode?

- **Eco**: Normal efficient heating to target temperature
- **Performance** (Boost): Aggressive fast heating, prioritizes DHW over space heating

Use Performance before baths or when you need hot water quickly.

### What temperature should I set?

**Recommended**: 50-55°C
- **Minimum**: 50°C (prevents legionella)
- **Maximum**: 55°C (prevents scaling, optimal efficiency)

---

## Modes & Presets

### What's the difference between mode and preset?

**HVAC Mode**: What type of conditioning
- Heat, Cool, Auto, Off

**Preset Mode**: Energy/comfort level
- Comfort = normal temperature
- Eco = reduced temperature for energy savings

### Why don't I see "Auto" mode?

Some systems show it as "Heat/Cool" instead. This is the same as Auto mode - system automatically heats or cools as needed.

### What does Eco mode actually do?

Eco mode typically:
- Reduces target temperature by 2-3°C in heating
- Increases target temperature by 2-3°C in cooling
- Saves energy while maintaining basic comfort

### Can I create custom presets?

Not directly in the integration, but you can:
- Use Home Assistant scenes
- Create automations with specific temperature settings
- Use input_select helpers for custom modes

---

## Sensors

### Why do some sensors show "Unknown"?

Common reasons:
- Sensor doesn't apply to your system type
- Feature not configured in CSNet Manager
- Initial data sync not complete yet
- That data isn't provided by your model

This is usually normal - just hide/disable sensors you don't need.

### Why is outdoor temperature different from weather apps?

`sensor.system_controller_outdoor_temperature` comes from your heat pump's sensor, which may differ slightly from weather services. Both are valid - the heat pump sensor is what the system uses for control.

### What's a good WiFi signal?

- **-30 to -50 dBm**: Excellent
- **-50 to -60 dBm**: Good
- **-60 to -70 dBm**: Fair
- **-70 dBm or worse**: Poor (may cause issues)

If signal is poor, consider WiFi extender or repositioning.

---

## Advanced Features

### What is Silent Mode?

Silent mode reduces outdoor unit noise by limiting compressor and fan speed. Use at night or when noise is a concern.

**Note**: Not available on fan coil systems (they have fan speed control instead).

### What is fan speed control?

On fan coil compatible systems, you can control indoor fan speed:
- Off, Low, Medium, Auto

Replaces silent mode functionality.

### How do I know if I have fan coil?

Check `sensor.system_controller_fan_coil_compatible`:
- **On**: You have fan speed control
- **Off**: You have silent mode instead

### What is OTC?

**Outdoor Temperature Compensation** - System automatically adjusts water temperature based on outdoor temperature for optimal efficiency.

OTC sensors show your configuration:
- Type (None, Points, Gradient, Fixed)
- Separate for heating and cooling
- Separate for C1 and C2 circuits

This is informational - configured in CSNet Manager, not controllable via HA.

---

## Alarms

### I got an alarm notification - what do I do?

1. Check `alarm_message` sensor for description
2. Check `alarm_origin` to see which component
3. Look up alarm code in system manual
4. Check CSNet Manager app for more details
5. Try basic troubleshooting (power cycle, check water pressure)
6. Call service if alarm persists

### What do alarm codes mean?

Alarm codes indicate specific system issues. Common ones:
- **0**: No alarm
- **Low numbers (1-20)**: Often sensor or communication issues
- **High numbers**: Usually component faults

See your system manual or contact support for specific codes.

### Can I silence alarm notifications?

You can modify or disable the alarm notification automation. However, we recommend keeping them - alarms indicate real issues that need attention.

---

## Troubleshooting

### Why aren't my controls working?

Check:
1. Is system actually on? (Check `on_off` sensor)
2. Is HVAC mode correct? (Not "Off")
3. Any alarms? (Check `alarm_code`)
4. Is device online? (Check `connectivity` sensor)
5. Did you wait 1-2 minutes for sync?

See [Troubleshooting](Troubleshooting) for detailed help.

### Why do I see "Unavailable"?

Usually means connection lost to CSNet Manager:
- Check internet connection
- Check if CSNet Manager website is accessible
- Check `connectivity` sensor
- Try reloading integration

### Temperature isn't updating

Temperatures update every **scan_interval** (default 60 seconds), not real-time. Wait a minute and check again.

### I changed something but it's not reflected

Changes can take:
- 5-15 seconds for command to execute
- Up to next scan_interval for confirmation
- So potentially 60-75 seconds total

This is normal for cloud-based control.

---

## Performance & Resources

### Does this use a lot of internet data?

No, very minimal:
- API calls are small JSON responses
- Default 60-second interval = ~1 call/minute
- Total data usage: < 1 MB/day typically

### Will this slow down my Home Assistant?

No, the integration is lightweight:
- Runs asynchronously
- Single update check per interval
- Minimal processing required

### Can I reduce API calls?

Yes, increase `scan_interval`:
- 120 seconds = half as many calls
- 180 seconds = one-third as many calls

Trade-off: less responsive updates.

---

## Comparison & Alternatives

### How is this different from Hi-Kumo integration?

Hi-Kumo was the old system. New ATW-IOT-01 module replaced it. This integration:
- ✅ Works with new ATW-IOT-01 hardware
- ✅ Uses CSNet Manager (current system)
- ❌ Won't work with old Hi-Kumo systems

### Are there other ways to integrate Hitachi?

For ATW-IOT-01 systems, this is currently the only known Home Assistant integration.

### Can I control this locally without cloud?

No, not with ATW-IOT-01. The module only communicates with Hitachi's cloud service. There's no documented local API.

---

## Privacy & Security

### Where are my credentials stored?

In Home Assistant's encrypted configuration storage. They never leave your Home Assistant instance except when authenticating with CSNet Manager.

### Can the integration author see my data?

No. The integration runs entirely on your Home Assistant instance. No data is sent to the developer or any third party (only to Hitachi's CSNet Manager service).

### Is my system secure?

Security depends on:
- Your Home Assistant security
- Your CSNet Manager password strength
- Your network security

Use strong passwords and keep Home Assistant updated.

---

## Contributing & Support

### How can I contribute?

Many ways:
- Report bugs on GitHub Issues
- Share your device configuration in Supported Devices
- Answer questions in Discussions
- Submit code improvements via Pull Requests
- Improve documentation
- Test preview builds

See [Contributing](Contributing) guide.

### Where do I report bugs?

GitHub Issues: https://github.com/mmornati/home-assistant-csnet-home/issues

Please include:
- Home Assistant version
- Integration version
- System type and configuration
- Debug logs
- Steps to reproduce

### Where do I ask questions?

GitHub Discussions: https://github.com/mmornati/home-assistant-csnet-home/discussions

Search first - your question may already be answered!

### Is there a Discord/Forum?

Currently we use GitHub Discussions for community support. This keeps everything searchable and organized.

---

## Future Development

### Will feature X be added?

Check GitHub Issues for requested features. If it's not there, create a feature request!

Development priorities:
1. Bug fixes and stability
2. Support for more device types
3. New features based on community feedback

### Can I sponsor development?

The project is open source and maintained by volunteers. The best way to support is:
- Report issues and help test fixes
- Contribute code or documentation
- Help other users in Discussions
- Spread the word

### Roadmap?

There's no fixed roadmap. Development is driven by:
- Community bug reports
- Feature requests
- Contributor availability
- Discovery of new API capabilities

---

## Quick Links

- **[Home](Home)** - Documentation home
- **[Installation Guide](Installation-Guide)** - How to install
- **[Configuration Guide](Configuration-Guide)** - How to configure
- **[Troubleshooting](Troubleshooting)** - Fix issues
- **[GitHub Repository](https://github.com/mmornati/home-assistant-csnet-home)** - Source code
- **[GitHub Issues](https://github.com/mmornati/home-assistant-csnet-home/issues)** - Bug reports
- **[GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions)** - Community support

---

## Still Have Questions?

If your question isn't answered here:

1. **Search the documentation** - Use your browser's find function (Ctrl+F)
2. **Check [Troubleshooting](Troubleshooting)** - Common issues covered there
3. **Search [GitHub Discussions](https://github.com/mmornati/home-assistant-csnet-home/discussions)** - May already be answered
4. **Ask in Discussions** - Create a new discussion thread

---

**[← Back to Home](Home)** | **[Back to Troubleshooting](Troubleshooting)**

