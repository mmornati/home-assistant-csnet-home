---
title: Release notes
description: What changed in each version of the Hitachi CSNet Home integration, from the first release to today.
---

# Release notes

Every version of the integration, newest first. Install or update from HACS; each version is also on the [GitHub releases page](https://github.com/mmornati/home-assistant-csnet-home/releases).

## Next release (not released yet)

These changes are merged or waiting for review and will ship in the next version.

### Heating curves you can describe

CSNet reports which kind of heating curve (water law, "loi d'eau") each circuit uses, but not its values. The new **Configure** form of the integration lets you copy them from the unit controller: two points for a **Points** curve, the gradient for a **Gradient** curve, and the vertex offset. Each described circuit gets a sensor with the water temperature its curve asks for at the unit's average outdoor temperature, with the whole curve in its attributes. Nothing is sent to the unit. See [Heating Curve Values](wiki/Advanced-Features.md#heating-curve-values-water-law). ([#246](https://github.com/mmornati/home-assistant-csnet-home/pull/246))

### Dashboard cards shipped with the integration

Eleven cards appear in the dashboard **Add card** picker, with nothing else to install: heat pump overview, live water circuit, heating curve, performance (COP), system health, refrigerant circuit, temperatures, what ran, energy per day, power today against the usual day, and the energy signature with tomorrow's forecast. They find their entities by themselves, use your electricity meter and its power sensor when you chose one in the settings, show the cost with the price of the Energy dashboard, follow light and dark themes, and speak English, French and Spanish. See [Dashboard Cards](wiki/Dashboard-Cards.md). ([#247](https://github.com/mmornati/home-assistant-csnet-home/pull/247))

### More equipment

Sensors for hot water tanks (mode, anti-legionella), fan coils (actual fan speed), R290 units (primary flow) and cascades (units enabled, working, required), created only when the unit reports them; accounts with several installations are reported in the diagnostics. ([#245](https://github.com/mmornati/home-assistant-csnet-home/pull/245))

## 2.13.0

*14 November 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/2.13.0)

New entities for what the unit is doing and how much heat it produces, a real COP from your own electricity meter, and controls limited to what your unit can actually do. No existing entity is renamed or removed.

#### Please read before updating

- **Climate entities offer fewer options on units that lack them.** `cool` is offered only where the unit has cooling, `heat_cool` only where it has auto, and the "silent" fan mode only on units with silent mode. Eco/comfort and hot water boost follow the same rule. If an automation or dashboard uses an option your unit never had, adjust it. Only an explicit "no" from the unit removes an option; nothing changes for values the unit does not report.
- **New entities appear** on the unit's device, with ids such as `binary_sensor.system_controller_compressor` and `sensor.system_controller_heat_produced_today`.

#### Added

- **Binary sensors: what the unit is running.** Compressor, defrost, water pumps 1 to 3, circuit 1 and 2 demand, and for units with a hot water tank the DHW electric heater and DHW recirculation. Backup heater, boiler, smart function input and forced off depend on what an installer fitted, so they are created disabled: enable the ones you have.
- **Heat produced, as recorded by CSNet.** Today, yesterday and this month, from the records behind the consumption page of the CSNet web app, read every 15 minutes. Split by use (space heating, cooling, hot water, pool) when the unit has several. Units with Hitachi's pulse meter also get the electricity the server recorded.
- **COP from your own electricity meter (optional).** A new setting, "Electricity meter of the heat pump": pick any Home Assistant energy sensor (kWh, Wh or MWh) that measures the heat pump, from any device or integration. You then get COP today, yesterday, this month and last month, as CSNet's heat divided by what your meter counted.
  - A day or month gets a COP only if the meter was read within 20 minutes of its start, so the first day shows nothing until midnight has passed, and the month figure starts with the next month. Readings are kept across restarts.
  - COP today uses heat and electricity both up to the last hour CSNet has delivered, so it updates once an hour.
  - Without a meter, the existing estimate from the compressor current is unchanged.
- **Eco offset per circuit and indoor board software** sensors.
- **Diagnostics** now include the most recent energy records, which helps when reporting a question about the heat or COP figures.

#### Changed

- **Fixed water temperature limits** come from the unit when it reports them.
- A new climate attribute, `deactivated_in_current_mode`, tells when a circuit is switched off in the mode the unit is running in.
- Sensors that depend on data the unit reports are added as soon as that data arrives, without a reload, if it was missing at startup.

#### Tested on

A Yutaki S with two circuits, no hot water tank, no cooling, no silent mode and no pulse meter. The COP was validated by replaying two days of a real three-phase meter's readings and CSNet's hourly records through the integration: 99 kWh of heat over 40.70 kWh metered gave 2.43, equal to the hand calculation.

Not tested on a real unit: hot water tank, pool, cooling and fan coil units, and units with a pulse meter. Their entities are only created when the unit reports the values; reports are welcome, with the diagnostics download attached.

## 2.12.0

*13 November 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/2.12.0)

This release comes from a full review of the integration against the CSNet Manager web app. It fixes wrong readings and repeated alarm notifications, makes orders to the unit safer, and adds a diagnostics download.

#### Please read before updating

- **Three-phase units (8 and 10 HP): power, energy and COP estimates change.** These units are now detected as three-phase, so the estimated consumption is about 2.9 times higher and the COP correspondingly lower, which is closer to reality. The Energy dashboard shows a step up from the day you update; earlier days keep their old values. Smaller units are unchanged; you can force single or three-phase in the integration's settings (#231).
- **Alarm notifications.** Each alarm is notified once. An alarm whose notification you dismissed is not notified again while it stays active, also after a restart. After updating you will get the notifications for currently active alarms one more time (#238).
- **About 20 technical sensors move to the "Diagnostic" section** of their device page and no longer appear in automatically generated dashboards: software versions, model and capacity codes, configuration flags, OTC types, connectivity. Entity ids, history and automations are not affected (#243).
- **Silent mode** is only sent to units that report having one. On other units the "silent" fan mode now answers with an error instead of sending an order (#240).

#### Fixed

- **Repeated alarm notifications** (issue #185): one failed request for the alarm list made the integration forget what it had notified and notify everything again. The alarm history sensor no longer drops to 0 either (#238).
- **Readings**
  - Heat output was not counted while the compressor ran with the thermostat satisfied (#234).
  - "No probe" markers (-127, -67) are no longer shown as temperatures (#234).
  - The status flags attributes decoded the wrong field (#234).
  - Daily energy is no longer restored from a previous day after a restart, and a failed poll no longer adds energy (#234).
  - The mode sensor showed "off" for a unit in auto (#234).
  - Swimming pool temperature is read from the unit status (#234).
- **Installations with several indoor units** read the limits, flags and temperatures of each unit instead of the first one's everywhere (#233).
- **Zone data could stay one poll behind** when part of a poll failed (#233).
- **An expired session no longer makes everything unavailable for a minute**: the integration signs in again inside the same poll (#233).
- **Alarm texts** use the language you chose (#233).
- **Climate**
  - Setpoints move in 0.5 °C steps for rooms and 1 °C for water circuits, as on the unit (#235).
  - In auto, temperature limits and the water circuit setpoint follow the mode the unit is running in (#235, #240).
  - A stopped zone reports "off"; a missing temperature no longer causes an error (#235).
  - 19.9 °C was sent as 19.8 °C (#240).
  - Silent mode used a key the server does not know (#240).
- **Configuration**
  - The reconfigure screen no longer sends the stored password to the browser; password fields are masked. Leave the password empty to keep the current one (#241).
  - Changing a setting no longer signs in to CSNet again (#241).
  - The temperature override and the alarm code filter can be emptied; an unreadable alarm code list is refused (#241).
  - The alarm options have labels in English, French and Spanish (#241).

#### Changed

- **Orders to the unit** are sent one at a time and at least 1.5 s apart. An accepted order shows in Home Assistant at once instead of at the next poll, and setting a water circuit temperature no longer blocks for 1.5 s (#242).
- **The alarm list is read every 5 minutes** instead of every minute; zone alarm codes still follow the normal interval (#238).
- **The unit's device shows its model** (for example "Yutaki S") instead of "HVAC System" (#243).

#### Added

- **Diagnostics download** from the integration's menu, with account, location and hardware identifiers removed. Attach it to bug reports (#232).

#### Internal

- The API client and coordinator live on the config entry (`runtime_data`); dead code removed; less work per poll when debug logging is off (#236, #237, #239).
- A scripted local test instance for contributors: `python3 scripts/test_ha.py` (#232).

#### Not verified on a real unit

The maintainer's unit has no silent mode, no fixed-temperature water circuit, no hot water tank, no pool and no active alarm. The fixes for those rest on the web app's code and on unit tests. Reports from units that have them are welcome.

## 2.11.3

*12 November 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/2.11.3)

#### What's Changed
##### Other Changes
* fix(sensor): divide water pressure by 50 again by @mmornati in [#230](https://github.com/mmornati/home-assistant-csnet-home/pull/230)


**Full changelog**: [2.11.2...2.11.3](https://github.com/mmornati/home-assistant-csnet-home/compare/2.11.2...2.11.3)

## 2.11.2

*11 November 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/2.11.2)

#### What's Changed
##### Other Changes
* fix(sensor): don't create compressor sensors the outdoor unit lacks (suction pressure, second cycle) by @mmornati in [#226](https://github.com/mmornati/home-assistant-csnet-home/pull/226)


**Full changelog**: [2.11.1...2.11.2](https://github.com/mmornati/home-assistant-csnet-home/compare/2.11.1...2.11.2)

## 2.11.1

*11 November 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/2.11.1)

#### What's Changed
##### Other Changes
* fix(migration): use per-entry device lookup on HA 2026.11+ by @mmornati in [#225](https://github.com/mmornati/home-assistant-csnet-home/pull/225)


**Full changelog**: [2.11.0...2.11.1](https://github.com/mmornati/home-assistant-csnet-home/compare/2.11.0...2.11.1)

## 2.11.0

*11 November 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/2.11.0)

#### What's Changed
##### Other Changes
* fix: stable zone ids across CSNet renames, correct water pressure, add circuit 2 water temperature by @mmornati in [#224](https://github.com/mmornati/home-assistant-csnet-home/pull/224)


**Full changelog**: [2.10.0...2.11.0](https://github.com/mmornati/home-assistant-csnet-home/compare/2.10.0...2.11.0)

## 2.10.0

*30 October 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/2.10.0)

#### What's Changed
##### Other Changes
* fix: drop async_timeout dependency, repair stale tests (#206) by @mmornati in [#208](https://github.com/mmornati/home-assistant-csnet-home/pull/208)
* ci: make HA compatibility checks fail for real, add Claude release review by @mmornati in [#209](https://github.com/mmornati/home-assistant-csnet-home/pull/209)
* fix(climate): migrate to native_* temperature properties (HA 2026.11 deprecation) by @mmornati in [#207](https://github.com/mmornati/home-assistant-csnet-home/pull/207)
* ci(ha-release-review): show Claude's error text when the review step fails by @mmornati in [#210](https://github.com/mmornati/home-assistant-csnet-home/pull/210)
* ci(ha-release-review): use Claude Max token, fall back to API key by @mmornati in [#211](https://github.com/mmornati/home-assistant-csnet-home/pull/211)
* ci(ha-release-review): call the Messages API directly instead of Claude Code by @mmornati in [#213](https://github.com/mmornati/home-assistant-csnet-home/pull/213)
* fix(api): back off on login failures, retry expired writes, raise UpdateFailed/ConfigEntryAuthFailed by @mmornati in [#214](https://github.com/mmornati/home-assistant-csnet-home/pull/214)
* fix(water_heater): follow the coordinator so the entity goes unavailable when a poll fails by @mmornati in [#217](https://github.com/mmornati/home-assistant-csnet-home/pull/217)
* docs: project landing page, API audit and unofficial-API disclaimer by @mmornati in [#212](https://github.com/mmornati/home-assistant-csnet-home/pull/212)
* fix: prepare for HA 2026.11 deprecations (water heater native_*, update listener) by @mmornati in [#219](https://github.com/mmornati/home-assistant-csnet-home/pull/219)
* docs: update known limitations for login backoff, reauth and 60 s floor by @mmornati in [#215](https://github.com/mmornati/home-assistant-csnet-home/pull/215)
* fix(api): retry alarm delete after an expired session by @mmornati in [#218](https://github.com/mmornati/home-assistant-csnet-home/pull/218)
* ci(ha-release-review): make the review model configurable by @mmornati in [#220](https://github.com/mmornati/home-assistant-csnet-home/pull/220)
* ci: label-triggered Claude fix workflow for HA release reviews by @mmornati in [#221](https://github.com/mmornati/home-assistant-csnet-home/pull/221)
* fix(ha-fix): stream tool-runner turns, use the reviewed HA version's source by @mmornati in [#222](https://github.com/mmornati/home-assistant-csnet-home/pull/222)


**Full changelog**: [v2.9.0...2.10.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.9.0...2.10.0)

## 2.9.0

*19 October 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.9.0)

#### What's Changed
##### Other Changes
* fix(ci): fix Hassfest requirements error and fork PR preview comment by @mmornati in [#205](https://github.com/mmornati/home-assistant-csnet-home/pull/205)
* Enhancement: Add cooling thermal power support, dedicated DHW tank sensor, and fix missing EVO mapping by @davigar1391 in [#196](https://github.com/mmornati/home-assistant-csnet-home/pull/196)


**Full changelog**: [v2.8.0...v2.9.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.8.0...v2.9.0)

## 2.8.0

*14 June 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.8.0)

#### What's Changed
##### Other Changes
* refactor(sensor): migrate to SensorEntity + SensorEntityDescription (fixes #199) by @mmornati in [#200](https://github.com/mmornati/home-assistant-csnet-home/pull/200)


**Full changelog**: [v2.7.1...v2.8.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.7.1...v2.8.0)

## 2.7.1

*31 May 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.7.1)

#### What's Changed
##### Other Changes
* fix(ci): add Python 3.14 detection for nightly compatibility tests by @mmornati in [#192](https://github.com/mmornati/home-assistant-csnet-home/pull/192)
* Feature: Add configurable alarm notification filtering (#193) by @mmornati in [#194](https://github.com/mmornati/home-assistant-csnet-home/pull/194)
* Fix cooling min temperature locked at 20°C for water circuits by @mmornati in [#198](https://github.com/mmornati/home-assistant-csnet-home/pull/198)


**Full changelog**: [v2.7.0...v2.7.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.7.0...v2.7.1)

## 2.7.0

*22 February 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.7.0)

#### What's Changed
##### Other Changes
* feat: expose actual Output Power sensors (#166) by @mmornati in [#167](https://github.com/mmornati/home-assistant-csnet-home/pull/167)
* Remove unused is_yutaki method by @mmornati in [#169](https://github.com/mmornati/home-assistant-csnet-home/pull/169)
* test: add missing test for coordinator alarm notification by @mmornati in [#170](https://github.com/mmornati/home-assistant-csnet-home/pull/170)
* Fix temperature oscillation for Yutampo/water heaters (Issue #141) by @mmornati in [#158](https://github.com/mmornati/home-assistant-csnet-home/pull/158)
* 🧪 Add tests for CSNet Home number entity by @mmornati in [#180](https://github.com/mmornati/home-assistant-csnet-home/pull/180)
* Refactor CSNetHomeInstallationSensor state logic by @mmornati in [#168](https://github.com/mmornati/home-assistant-csnet-home/pull/168)
* ⚡ Optimize sensor data lookup to O(1) by @mmornati in [#171](https://github.com/mmornati/home-assistant-csnet-home/pull/171)
* Refactor API data extraction logic by @mmornati in [#172](https://github.com/mmornati/home-assistant-csnet-home/pull/172)
* Implement robust API response sanitization for fixtures by @mmornati in [#173](https://github.com/mmornati/home-assistant-csnet-home/pull/173)
* Refactor get_temperature_limits to use configuration map by @mmornati in [#177](https://github.com/mmornati/home-assistant-csnet-home/pull/177)
* Refactor CSNetHomeCompressorSensor state logic by @mmornati in [#174](https://github.com/mmornati/home-assistant-csnet-home/pull/174)
* Refactor coordinator update method for better maintainability by @mmornati in [#175](https://github.com/mmornati/home-assistant-csnet-home/pull/175)
* ⚡ Parallelize independent API calls in coordinator update by @mmornati in [#176](https://github.com/mmornati/home-assistant-csnet-home/pull/176)
* Refactor sensor setup to use configuration lists by @mmornati in [#178](https://github.com/mmornati/home-assistant-csnet-home/pull/178)
* ⚡ Optimize CSNetHomeClimate by inheriting from CoordinatorEntity by @mmornati in [#179](https://github.com/mmornati/home-assistant-csnet-home/pull/179)
* Alarm Management Improvements by @mmornati in [#181](https://github.com/mmornati/home-assistant-csnet-home/pull/181)


**Full changelog**: [v2.6.0...v2.7.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.6.0...v2.7.0)

## 2.6.0

*19 February 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.6.0)

#### What's Changed
##### Other Changes
* 🔒 Redact PII in debug logs by @mmornati in [#159](https://github.com/mmornati/home-assistant-csnet-home/pull/159)
* ⚡ Reuse ClientSession for Connection Pooling by @mmornati in [#160](https://github.com/mmornati/home-assistant-csnet-home/pull/160)
* Refactor HVAC mode setting logic in api.py by @mmornati in [#161](https://github.com/mmornati/home-assistant-csnet-home/pull/161)
* 🧪 Add unit tests for helpers.py by @mmornati in [#162](https://github.com/mmornati/home-assistant-csnet-home/pull/162)
* Add reconfiguration flow with validation and i18n by @mmornati in [#152](https://github.com/mmornati/home-assistant-csnet-home/pull/152)
* ⚡ Optimize get_alarm_origin with O(1) lookups by @mmornati in [#165](https://github.com/mmornati/home-assistant-csnet-home/pull/165)
* fix: Restore missing implementation from PR #155 (new sensors + Spanish language) by @mmornati in [#164](https://github.com/mmornati/home-assistant-csnet-home/pull/164)


**Full changelog**: [v2.5.0...v2.6.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.5.0...v2.6.0)

## 2.5.0

*8 February 2026* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.5.0)

#### What's Changed
##### Other Changes
* Added new functions by @davigar1391 in [#155](https://github.com/mmornati/home-assistant-csnet-home/pull/155)
* feat: Add waterOutlet3Temp (TWO3) external tank temperature sensor by @mmornati in [#156](https://github.com/mmornati/home-assistant-csnet-home/pull/156)


**Full changelog**: [v2.4.0...v2.5.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.4.0...v2.5.0)

## 2.4.0

*13 December 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.4.0)

#### What's Changed
##### 🚀 Enhancements
* ✨ Add Swimming Pool (SWP) Support by @mmornati in [#105](https://github.com/mmornati/home-assistant-csnet-home/pull/105)


**Full changelog**: [v2.3.8...v2.4.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.8...v2.4.0)

## 2.3.8

*13 December 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.8)

#### What's Changed
##### 🐛 Bug Fixes
* Fix device_info KeyError causing HA crashes with Versatile Thermostat (Closes #140) by @mmornati in [#142](https://github.com/mmornati/home-assistant-csnet-home/pull/142)
##### Other Changes
* Fix: Replace % with # in password field to match CSNet API behavior by @mmornati in [#145](https://github.com/mmornati/home-assistant-csnet-home/pull/145)


**Full changelog**: [v2.3.7...v2.3.8](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.7...v2.3.8)

## 2.3.7

*24 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.7)

#### What's Changed
##### Other Changes
* Add manual override for Legacy Fan Coil support by @davigar1391 in [#135](https://github.com/mmornati/home-assistant-csnet-home/pull/135)


**Full changelog**: [v2.3.6...v2.3.7](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.6...v2.3.7)

## 2.3.6

*22 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.6)

#### What's Changed
##### Other Changes
* Fix issue #137: Correct water heater current_temperature reading by @mmornati in [#138](https://github.com/mmornati/home-assistant-csnet-home/pull/138)


**Full changelog**: [v2.3.5...v2.3.6](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.5...v2.3.6)

## 2.3.5

*19 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.5)

#### What's Changed
##### 🐛 Bug Fixes
* Fix: Add missing helpers.py module to resolve critical startup error by @mmornati in [#134](https://github.com/mmornati/home-assistant-csnet-home/pull/134)


**Full changelog**: [v2.3.4...v2.3.5](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.4...v2.3.5)

## 2.3.4

*19 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.4)

#### What's Changed
##### Other Changes
* Dynamic Fan Coil Model Support & State Fix by @davigar1391 in [#133](https://github.com/mmornati/home-assistant-csnet-home/pull/133)

#### New Contributors
* @davigar1391 made their first contribution in [#133](https://github.com/mmornati/home-assistant-csnet-home/pull/133)

**Full changelog**: [v2.3.3...v2.3.4](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.3...v2.3.4)

## 2.3.3

*15 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.3)

#### What's Changed
##### Other Changes
* Fix issue #131: Add temperature limits validation matching JavaScript logic by @mmornati in [#132](https://github.com/mmornati/home-assistant-csnet-home/pull/132)


**Full changelog**: [v2.3.2...v2.3.3](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.2...v2.3.3)

## 2.3.2

*11 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.2)

#### What's Changed
##### Other Changes
* fix: Correct pump speed unit from m/s to percentage (Issue #128) by @mmornati in [#129](https://github.com/mmornati/home-assistant-csnet-home/pull/129)


**Full changelog**: [v2.3.1...v2.3.2](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.1...v2.3.2)

## 2.3.1

*9 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.1)

#### What's Changed
##### Other Changes
* Fix thermostat limit handling and add packaging helper by @mmornati in [#125](https://github.com/mmornati/home-assistant-csnet-home/pull/125)
* Fix #124: Negative Temperature Overflow in Compressor Sensors by @mmornati in [#126](https://github.com/mmornati/home-assistant-csnet-home/pull/126)


**Full changelog**: [v2.3.0...v2.3.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.3.0...v2.3.1)

## 2.3.0

*8 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.3.0)

#### What's Changed
##### Other Changes
* feat: Add fixed water temperature control for C1/C2 circuits (Issue #120) by @mmornati in [#121](https://github.com/mmornati/home-assistant-csnet-home/pull/121)


**Full changelog**: [v2.2.1...v2.3.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.2.1...v2.3.0)

## 2.2.1 — Water Temperature Control & Operation Status Fixes

*7 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.2.1)

#### 🎯 Overview
v2.2.1 includes important bug fixes for water temperature control synchronization and outdoor unit operation status mapping, plus enhanced documentation for fixed water temperature features.

#### ✨ New Features

##### Fixed Water Temperature Control (Issue #120)
- **New Number Entities**: Added dedicated number entities for controlling fixed water supply temperatures
  - `number.{zone}_fixed_water_temperature_heating_c1/c2`
  - `number.{zone}_fixed_water_temperature_cooling_c1/c2`
- **Circuit-Level Settings**: Fixed water temperature controls apply to both air zones (1,2) and water zones (5,6) of the same circuit
- **OTC Dependency**: Entities automatically appear only when OTC (Outdoor Temperature Compensation) type is set to "FIX"
- **Climate Entity Behavior**: 
  - Air circuits always show editable room temperature
  - Water circuits show fixed temperature when OTC is FIX, otherwise unavailable
- **Comprehensive Documentation**: Added detailed user guide in Climate Control documentation

#### 🐛 Bug Fixes

##### Outdoor Unit Operation Status Alignment (Issue #122)
- **Fixed Status Mapping**: Corrected operation status codes to properly align with CSNet constants (0-11)
- **Status Codes**:
  - 0: Off
  - 1: Cooling Demand Off
  - 2: Cooling Thermostat Off
  - 3: Cooling Thermostat On
  - 4: Heating Demand Off
  - 5: Heating Thermostat Off
  - 6: Heating Thermostat On
  - 7: DHW Off
  - 8: DHW On
  - 9: Swimming Pool Off
  - 10: Swimming Pool On
  - 11: Alarm
- **Defrost Clarification**: Removed incorrect "defrost" label when unit is heating; now properly exposed `defrosting` flag as separate attribute
- **Enhanced Attributes**: Compressor sensor now includes `status_text`, `raw_value`, and `defrosting` flag for better diagnostics

##### Immediate Data Sync
- **API Consistency**: Added 1.5-second delay before coordinator refresh to ensure server processes changes
- **async_refresh()**: Changed from `async_request_refresh()` to `async_refresh()` to wait for completion
- **Applied to Both**: Water temperature and climate entity now refresh data immediately after setting values

#### 📝 Documentation Enhancements

- **Fixed Water Temperature Guide**: Comprehensive user documentation in Climate Control section
  - Explains OTC modes and Fixed mode requirements
  - Shows how to enable fixed temperature control
  - Includes UI, service call, and automation examples
  - Troubleshooting guide for common issues

#### 🔧 Technical Changes

##### File Changes
- `custom_components/csnet_home/number.py` - New file with fixed water temperature number entities
- `custom_components/csnet_home/climate.py` - Updated OTC handling and async refresh logic
- `custom_components/csnet_home/api.py` - Added helper methods for fixed temperature operations
- `custom_components/csnet_home/__init__.py` - Registered NUMBER platform
- `custom_components/csnet_home/sensor.py` - Fixed outdoor operation status mapping
- `docs/wiki/Climate-Control.md` - Added comprehensive fixed water temperature documentation

##### Commits Included
- **#121**: feat: Add fixed water temperature control for C1/C2 circuits (Issue #120)
- **#123**: fix: align outdoor operation status mapping with CSNet constants

#### ✅ Testing
All changes pass:
- ✅ black (code formatting)
- ✅ codespell (spelling)
- ✅ flake8 (style guide)
- ✅ bandit (security)
- ✅ pylint (code analysis)
- ✅ mypy (type checking)

#### 📦 Compatibility
- Home Assistant 2023.1.0+
- All device types supported
- Backward compatible with v2.2.0

#### 🙏 Contributors
- [@mmornati](https://github.com/mmornati)

**Compare**: [v2.2.0...v2.2.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.2.0...v2.2.1)

## 2.2.0

*3 November 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.2.0)

#### What's Changed
##### Other Changes
* feat: Add comprehensive compressor and outdoor unit monitoring sensors by @mmornati in [#119](https://github.com/mmornati/home-assistant-csnet-home/pull/119)


**Full changelog**: [v2.1.1...v2.2.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.1.1...v2.2.0)

## 2.1.1

*27 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.1.1)

#### What's Changed
##### 🚀 Enhancements
* Add Comprehensive User Documentation with Automated GitHub Pages Deployment by @mmornati in [#103](https://github.com/mmornati/home-assistant-csnet-home/pull/103)
* feat: added a suite to make a local integration testing of the automation by @mmornati in [#102](https://github.com/mmornati/home-assistant-csnet-home/pull/102)
##### Other Changes
* feat: Comprehensive Home Assistant Compatibility Testing Infrastructure by @mmornati in [#104](https://github.com/mmornati/home-assistant-csnet-home/pull/104)
* Fix broken internal documentation links by @mmornati in [#106](https://github.com/mmornati/home-assistant-csnet-home/pull/106)
* Fix internal documentation links for MkDocs compatibility by @mmornati in [#107](https://github.com/mmornati/home-assistant-csnet-home/pull/107)
* Fix temperature limits and add configurable override by @mmornati in [#117](https://github.com/mmornati/home-assistant-csnet-home/pull/117)


**Full changelog**: [v2.1.0...v2.1.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.1.0...v2.1.1)

## 2.1.0

*24 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.1.0)

#### What's Changed
##### 🚀 Enhancements
* feat: Expose OTC (Outdoor Temperature Compensation) Settings (Issue #71) by @mmornati in [#101](https://github.com/mmornati/home-assistant-csnet-home/pull/101)
##### Other Changes
* Improve outdoor temperature sensor naming for better user experience by @Copilot in [#99](https://github.com/mmornati/home-assistant-csnet-home/pull/99)


**Full changelog**: [v2.0.0...v2.1.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.0.0...v2.1.0)

## 2.0.0

*23 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v2.0.0)

### 🎉 Release v2.0.0

This is a major release with significant new features, enhancements, and bug fixes. This release adds comprehensive diagnostics, enhanced HVAC control, improved alarm handling, and better system monitoring capabilities.

#### ✨ New Features & Enhancements

##### HVAC Control Improvements
- **Auto HVAC Mode Support** (#90) - Added support for automatic HVAC mode, allowing the system to automatically switch between heating and cooling
- **Silent/Quiet Mode Support** (#91) - Introduced silent/quiet mode control for quieter operation
- **Dynamic Temperature Limits from API** (#92) - Temperature limits are now dynamically fetched from the API for more accurate control
- **Fan Speed Control for Fan Coil Systems** (#93) - Added fan speed control capabilities for fan coil systems (Issue #66)

##### Diagnostic & Monitoring Sensors
- **WiFi Signal and Connectivity Sensors** (#94) - Added sensors to monitor WiFi signal strength and connectivity status (Issue #72)
- **System Configuration Diagnostic Sensors** (#96) - Added comprehensive system configuration diagnostic sensors (Issue #78)
- **Central Control Configuration Diagnostic Sensors** (#82) - Added diagnostic sensors for central control configuration
- **Weather Temperature Sensor** (#97) - Added outdoor weather temperature sensor integration (Issue #79)
- **Operation Status Decoder** (#98) - Decode operation status values to human-readable text for better understanding (Issue #67)

##### Device Management
- **System Controller Rename** (#83) - Renamed installation device to 'System Controller' for better clarity

##### Enhanced Alarm Handling
- **Enhanced Alarm Handling** (#95) - Improved alarm detection and handling capabilities (Issue #75)

#### 🐛 Bug Fixes

- **Fix Heating Control for elementType 5 Devices** (#59) - Fixed heating control by using correct circuit parameters for elementType 5 devices
- **Increased Maximum Heating Temperature** (#60) - Adjusted maximum heating temperature limits
- **Fix TypeError on Temperature Change** (#62) - Fixed TypeError when sensor_data becomes None during temperature changes

#### 🔧 Dependency Updates

- Bump codecov/codecov-action from 4 to 5 (#84)
- Bump peter-evans/create-or-update-comment from 4 to 5 (#85)
- Bump actions/setup-python from 5.3.0 to 6.0.0 (#86)
- Bump peter-evans/find-comment from 3 to 4 (#87)
- Bump actions/github-script from 7 to 8 (#88)

#### 📊 Statistics

- **15 Pull Requests** merged
- **9 New Features/Enhancements**
- **3 Bug Fixes**
- **5 Dependency Updates**

#### 🙏 Contributors

Thank you to all contributors who made this release possible!

---

**Full changelog**: [v1.4.2...v2.0.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.4.2...v2.0.0)

## 1.4.2 — Diagnostic Sensors & Temperature Limit Update

*23 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.4.2)

#### 🎯 What's New in v1.4.2

This release adds diagnostic capabilities to help troubleshoot heat pump control issues, increases the maximum heating temperature limit, and improves device naming for better clarity.

---

#### ✨ Features

##### 🔍 Central Control Configuration Diagnostic Sensors (#82)

Added four new diagnostic sensors to help users identify and troubleshoot why CSNET Home commands might not be working:

**New Sensors:**

1. **Central Config** (`central_config`)
   - Displays the current control mode setting on the heat pump LCD
   - Possible values: Unit Only, RT Only, Unit & RT, Total Control, Total Control+
   - ⚠️ Shows warning indicator when value is insufficient for remote control (< 3)

2. **LCD Software Version** (`lcd_software_version`)
   - Displays the LCD firmware version in hex format (e.g., `0x0222`)
   - Helps determine if firmware supports remote control features

3. **Unit Model** (`unit_model`)
   - Shows the heat pump model name (Yutaki S, SC, S80, M, SC Lite, or Yutampo)
   - Different models have different control requirements

4. **Central Control Enabled** (`central_control_enabled`)
   - **Binary sensor** indicating if remote control is properly configured
   - **ON**: Commands from CSNET Home will be accepted by the heat pump
   - **OFF**: Unit will ignore remote commands (needs LCD menu configuration)
   - Implements the same logic used in the CSNET web interface

**Problem This Solves:**

Users were encountering the error: *"Le réglage de la commande centrale n'est pas défini sur « Total »"* when trying to control their heat pump. This occurred when the heat pump's LCD was not configured for centralized control. These sensors make the configuration status visible in Home Assistant.

**How to Fix Control Issues:**

If `central_control_enabled` shows **OFF**:
1. Access the heat pump LCD menu
2. Navigate to: **Settings → Control Settings → Central Control**
3. Change to **"Total"** control mode
4. Save the configuration

All sensors read from the existing `/data/installationdevices` API endpoint and appear under the "System Controller" device.

##### 🏷️ Improved Device Naming (#83)

**Device Naming Improvements:**

1. **Installation Device Renamed:**
   - **Old:** "Installation Global"  
   - **New:** "System Controller"
   - Better reflects its role as the main heat pump controller/unit

2. **Enhanced Device Models:**
   - **Zone devices:** `PAC ATW-IOT-01` → `PAC Remote Controller`
   - **System Controller:** `PAC Installation` → `HVAC System` 
   - **API fallback:** `ATW-IOT-01` → `Remote`

**Benefits:**
- More accurate naming (ATW-IOT-01 is the IoT gateway, not the controller)
- Language-neutral device names
- Clearer device identification in Home Assistant UI
- Better represents the actual hardware functions

**⚠️ Breaking Change Notice:**
This naming change may affect automations and dashboards that reference device names. Please update any:
- Automations using device triggers/conditions
- Dashboards with hardcoded device references
- Templates referencing the old device names

##### 🌡️ Increased Maximum Heating Temperature (#60)

**Changed:** Maximum heating temperature limit increased from **35°C to 55°C**

- Provides more flexibility for users who need higher temperatures
- Aligns better with heat pump capabilities (web app shows up to 80°C for some installations)
- 55°C provides a reasonable balance between efficiency and flexibility

**Credit:** Thanks to @validide for this contribution!

---

#### 🔧 Technical Details

##### Files Changed
- `custom_components/csnet_home/sensor.py` - Added diagnostic sensors + updated device naming
- `custom_components/csnet_home/api.py` - Updated device model naming
- `custom_components/csnet_home/climate.py` - Updated device model naming  
- `custom_components/csnet_home/water_heater.py` - Updated device model naming
- `custom_components/csnet_home/const.py` - Increased max temperature limit
- `tests/test_sensor.py` - Added comprehensive tests for new sensors + updated naming tests
- `tests/test_api.py` - Updated tests for new device naming

##### Testing
- ✅ All 46 tests passing
- ✅ 100% code coverage maintained
- ⚠️ **Breaking change:** Device naming updates may require automation/dashboard updates

---

#### 📊 Statistics

- **3 PRs merged** (#60, #82, #83)
- **550+ lines added**
- **40+ lines changed**
- **2+ contributors**

---

#### 🙏 Contributors

Thank you to everyone who contributed to this release:
- @validide - Maximum temperature enhancement
- @mmornati - Diagnostic sensors implementation + device naming improvements

---

#### 📝 Upgrade Notes

##### For Most Users (Non-Breaking)
- The diagnostic sensors will appear automatically under your "System Controller" device
- Temperature limits are automatically increased

##### For Users with Automations/Dashboards (Breaking Changes)
1. **Check your automations** that use device triggers/conditions
2. **Update dashboard references** from "Installation Global" to "System Controller"  
3. **Review templates** that reference device names
4. **Test all affected automations** after upgrade

The device entity IDs remain the same - only display names have changed.

---

#### 🔜 Coming Next

- Additional diagnostic capabilities based on user feedback
- Further UI/UX improvements

---

**Full changelog**: [v1.4.1...v1.4.2](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.4.1...v1.4.2)

## 1.4.1 — Bug Fix Release

*22 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.4.1)

#### What's Changed

##### Bug Fixes
* **Fix TypeError when sensor_data becomes None during temperature change** (#62)
  - Resolved an issue where  could become  during temperature updates, causing a TypeError
  - Added proper None checks in the climate entity's  method
  - Prevents Home Assistant from logging errors when sensor data temporarily becomes unavailable
  - Added comprehensive test coverage for this scenario

##### Technical Details
This patch release addresses a race condition that could occur when updating climate entity data, improving the stability and reliability of the integration.

**Full changelog**: [v1.4.0...v1.4.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.4.0...v1.4.1)

## 1.3.1

*20 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.3.1)

#### What's Changed
##### 🚀 Bug Fixing
* fix: problem in changing HVAC modes in some contexts


**Full changelog**: [v1.2.3...v1.3.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.2.3...v1.3.1)

## 1.3.0

*19 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.3.0)

##### Summary
- Fix and enhance climate entity using elements API:
  - Correct HVAC mode mapping (off/heat/cool) and actions (heating/cooling/idle)
  - Add presets (comfort/eco) from `ecocomfort`
  - Expose extra attributes: `real_mode`, `operation_status`, `timer_running`, `alarm_code`, `c1_demand`, `c2_demand`, `doingBoost`
  - Implement `turn_on`/`turn_off` behavior
- Add unit tests for climate entity
- Improve README with features, quick start, local testing, and known limitations
- Add PR preview workflow to attach a ZIP artifact to every PR
- Lint/quality fixes (flake8, pylint) and pre-commit stability (Bandit/pbr)

##### Motivation
- Align entity behavior with data available from the elements endpoint
- Facilitate pre-merge testing via downloadable ZIP from PR runs
- Improve developer and user documentation and testing ergonomics
- Resolve pre-commit issues to keep CI green

##### Changes
- `custom_components/csnet_home/climate.py`:
  - Fix mode logic, presets, actions; add extra attributes and on/off
- `custom_components/csnet_home/sensor.py`:
  - Clean no-else-return; minor state logic cleanup
- `custom_components/csnet_home/api.py`:
  - Remove unused import; document `get_current_temperature`; clean no-else-return
- `tests/test_climate.py`:
  - New tests for modes, presets, actions, attributes, on/off, temperature, unique_id
- `README.md`:
  - Features, Quick Start, local testing, known limitations, link to discussion
- `.github/workflows/pr-preview.yaml`:
  - New workflow: builds and uploads `hass-custom-csnet-home.zip` to PR as artifact and comments with run link
- `.pre-commit-config.yaml`:
  - Ensure Bandit hook installs `pbr`
- `custom_components/csnet_home/requirements-dev.txt`:
  - Add `bandit` and `pbr` to support local runs

##### How to test
- Unit tests
  - Run: `python -m venv .venv && . .venv/bin/activate && pip install -r custom_components/csnet_home/requirements-dev.txt -r custom_components/csnet_home/requirements.txt && pytest -q`
- Pre-commit
  - Run: `pre-commit clean && pre-commit install --install-hooks && pre-commit run --all-files`
- PR Preview ZIP
  - On this PR, check the bot comment for the Actions run link
  - Download artifact `csnet_home-pr-preview`
  - Unzip into `YOUR_HASS_CONFIG_DIRECTORY/custom_components/csnet_home`
  - Restart HA and validate entity behavior (modes, presets, actions)

##### Backwards compatibility
- No breaking config changes expected
- AUTO hvac mode not exposed as settable (documented in README)

##### Related
- Parameter discussion and mapping ideas: https://github.com/mmornati/home-assistant-csnet-home/discussions/21

## 1.2.3

*9 October 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.2.3)

#### What's Changed
##### Other Changes
* Fixing Cooling temperature set by @CrazYoshi in [#44](https://github.com/mmornati/home-assistant-csnet-home/pull/44)
* Hvac mode fix by @CrazYoshi in [#51](https://github.com/mmornati/home-assistant-csnet-home/pull/51)
* Fix: allow HVAC to start also in COOL and AUTO mode by @MiquelT in [#50](https://github.com/mmornati/home-assistant-csnet-home/pull/50)

#### New Contributors
* @MiquelT made their first contribution in [#50](https://github.com/mmornati/home-assistant-csnet-home/pull/50)

**Full changelog**: [v1.2.2...v1.2.3](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.2.2...v1.2.3)

## 1.2.2

*2 April 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.2.2)

#### What's Changed
##### Other Changes
* multiple sensors by @CrazYoshi in [#37](https://github.com/mmornati/home-assistant-csnet-home/pull/37)


**Full changelog**: [v1.2.1...v1.2.2](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.2.1...v1.2.2)

## 1.2.1

*8 March 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.2.1)

#### What's Changed
##### 🚀 Enhancements
* feat: using detected XSRF token instead of statics by @mmornati in [#30](https://github.com/mmornati/home-assistant-csnet-home/pull/30)
##### 🐛 Bug Fixes
* Fix for current heating temperature by @CrazYoshi in [#25](https://github.com/mmornati/home-assistant-csnet-home/pull/25)
* Fix for setting temperature by @CrazYoshi in [#29](https://github.com/mmornati/home-assistant-csnet-home/pull/29)

#### New Contributors
* @CrazYoshi made their first contribution in [#25](https://github.com/mmornati/home-assistant-csnet-home/pull/25)

**Full changelog**: [v1.2.0...v1.2.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.2.0...v1.2.1)

## 1.2.0

*26 February 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.2.0)

#### What's Changed
##### 🚀 Enhancements
* feat: add heating information in the UI by @mmornati in [#23](https://github.com/mmornati/home-assistant-csnet-home/pull/23)


**Full changelog**: [v1.1.0...v1.2.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.1.0...v1.2.0)

## 1.1.0

*17 February 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.1.0)

### Release 1.1.0

This release is adding the **full management for the Water Heater** connected to the Hitachi heat pump. A great first contribution from @MakeTotalSense 🎉 



#### What's Changed
##### 🚀 Enhancements
* feat: upload coverage result to codecov by @mmornati in [#18](https://github.com/mmornati/home-assistant-csnet-home/pull/18)
* Issue 11 by @MakeTotalSense in [#19](https://github.com/mmornati/home-assistant-csnet-home/pull/19)

#### New Contributors
* @MakeTotalSense made their first contribution in [#19](https://github.com/mmornati/home-assistant-csnet-home/pull/19)

**Full changelog**: [v1.0.1...v1.1.0](https://github.com/mmornati/home-assistant-csnet-home/compare/v1.0.1...v1.1.0)

## 1.0.1

*2 February 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.0.1)

### Release 1.0.1

This release is full made by @MakeTotalSense 🥳 🎉  A **big** **big** thanks to him for this big contribution.

There are some major fixes related to missing or not correctly working functions and a big improvement (a first step, another one will be added to the next release) to correctly support the Water Heater.
In this version is added to HomeAssistant as a `ClimateEntity`. This allows to change the temperature but the most important feature (force an heating mode) is still missing.


#### 🚀 Enhancements
- fix: settings for water heater temperature (#15)
- fix: added max/min temperatures based on device type (#12)

#### 🐛 Bug Fixes
- fix: added missing preset modes changes (#17)
- fix: Prevent breaking data when names are missing (#5)
- fix: current temperature not updated (#3)

#### 📚 Documentation
- feat: documentation improvements (#7)

#### 🧰 Maintenance
- Merge pull request #1 from mmornati/dependabot/github_actions/actions/setup-python-5.4.0
- build(deps): bump actions/setup-python from 5.3.0 to 5.4.0

## 1.0.0

*26 January 2025* · [GitHub release](https://github.com/mmornati/home-assistant-csnet-home/releases/tag/v1.0.0)

### First Release

First Integration release version supporting Hitachi Yutaki and creating Climate Components and sensors in Home Assistant.



**Full Changelog**: https://github.com/mmornati/home-assistant-csnet-home/commits/v1.0.0
