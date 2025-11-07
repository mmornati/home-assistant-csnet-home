# v2.2.1 Release Notes

## 🎯 Overview
v2.2.1 includes important bug fixes for water temperature control synchronization and outdoor unit operation status mapping, plus enhanced documentation for fixed water temperature features.

## ✨ New Features

### Fixed Water Temperature Control (Issue #120)
- **New Number Entities**: Added dedicated number entities for controlling fixed water supply temperatures
  - `number.{zone}_fixed_water_temperature_heating_c1/c2`
  - `number.{zone}_fixed_water_temperature_cooling_c1/c2`
- **Circuit-Level Settings**: Fixed water temperature controls apply to both air zones (1,2) and water zones (5,6) of the same circuit
- **OTC Dependency**: Entities automatically appear only when OTC (Outdoor Temperature Compensation) type is set to "FIX"
- **Climate Entity Behavior**: 
  - Air circuits always show editable room temperature
  - Water circuits show fixed temperature when OTC is FIX, otherwise unavailable
- **Comprehensive Documentation**: Added detailed user guide in Climate Control documentation

## 🐛 Bug Fixes

### Outdoor Unit Operation Status Alignment (Issue #122)
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

### Immediate Data Sync
- **API Consistency**: Added 1.5-second delay before coordinator refresh to ensure server processes changes
- **async_refresh()**: Changed from `async_request_refresh()` to `async_refresh()` to wait for completion
- **Applied to Both**: Water temperature and climate entity now refresh data immediately after setting values

## 📝 Documentation Enhancements

- **Fixed Water Temperature Guide**: Comprehensive user documentation in Climate Control section
  - Explains OTC modes and Fixed mode requirements
  - Shows how to enable fixed temperature control
  - Includes UI, service call, and automation examples
  - Troubleshooting guide for common issues

## 🔧 Technical Changes

### File Changes
- `custom_components/csnet_home/number.py` - New file with fixed water temperature number entities
- `custom_components/csnet_home/climate.py` - Updated OTC handling and async refresh logic
- `custom_components/csnet_home/api.py` - Added helper methods for fixed temperature operations
- `custom_components/csnet_home/__init__.py` - Registered NUMBER platform
- `custom_components/csnet_home/sensor.py` - Fixed outdoor operation status mapping
- `docs/wiki/Climate-Control.md` - Added comprehensive fixed water temperature documentation

### Commits
- feat: Add fixed water temperature control for C1/C2 circuits (Issue #120)
- docs: Add fixed water temperature control documentation
- fix: Add immediate data sync after setting fixed water temperature
- fix: align outdoor operation status mapping with CSNet constants

## ✅ Testing
All changes pass:
- ✅ black (code formatting)
- ✅ codespell (spelling)
- ✅ flake8 (style guide)
- ✅ bandit (security)
- ✅ pylint (code analysis)
- ✅ mypy (type checking)

## 📦 Compatibility
- Home Assistant 2023.1.0+
- All device types supported
- Backward compatible with v2.2.0

## 🙏 Contributors
- [@mmornati](https://github.com/mmornati)

---

**Compare**: [v2.2.0...v2.2.1](https://github.com/mmornati/home-assistant-csnet-home/compare/v2.2.0...v2.2.1)
