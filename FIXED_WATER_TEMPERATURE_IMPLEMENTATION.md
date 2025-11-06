# Fixed Water Temperature Implementation

## Problem Statement

According to issue #120 and the CSNet website JavaScript code, **water temperature for C1 and C2 water circuits is only editable when OTC (Outdoor Temperature Compensation) type is set to "FIX" (Fixed mode)**.

When OTC type is set to "law" (curve/gradient), the water temperature is automatically calculated and cannot be set manually. This is why users don't see the temperature control in their installations using law temperature mode.

## Solution

### Implementation Summary

1. **Created Number Entities** for fixed water temperature (instead of climate entity target temperature)
   - These entities only appear when OTC type is "FIX"
   - Separate entities for C1 and C2, heating and cooling modes
   
2. **Updated Climate Entity** to disable target temperature for water circuits when OTC type is not FIX
   - Returns `None` for `target_temperature` when OTC is not FIX
   - Warns when trying to set temperature when not editable

3. **Added API Helper Methods** to properly navigate installation devices data structure
   - `get_heating_status_from_installation_devices()` - Extracts heatingStatus from nested structure
   - `get_heating_setting_from_installation_devices()` - Extracts heatingSetting from nested structure
   - `is_fixed_water_temperature_editable()` - Checks if OTC type is FIX
   - `get_fixed_water_temperature()` - Gets current fixed temperature value
   - `async_set_fixed_water_temperature()` - Sets fixed water temperature

## Implementation Details

### JavaScript Code Analysis

From `/Users/mmornati/Downloads/csnet_js.txt`:

**Lines 11130-11133**: Fixed temperature input is only displayed when OTC type is FIX:
```javascript
if((selectedUnit.subzone==SUB_C1_AIR) && selectedUnit.heatingStatus.otcTypeHeatC1==OTC_HEATING_TYPE_FIX && !isOnHolidayC1) 
    fixTempHeatC1ExternalDiv.style.display="";
```

**Lines 5798-5800**: Function to check if fixed temperature should be used:
```javascript
if (isUnitOperatingInHeating(unit))
    return unit.heatingStatus.otcTypeHeatC1 == OTC_HEATING_TYPE_FIX;
else
    return unit.heatingStatus.otcTypeCoolC1 == OTC_COOLING_TYPE_FIX;
```

**Lines 7240-7245**: Temperature setting only uses fixed temperature when OTC type is FIX:
```javascript
if (li.fixTempHeatC1 != null && (mode==HEATING_MODES_HEAT || mode==HEATING_MODES_AUTO || mode==-1)){
    if(iu.heatingStatus.otcTypeHeatC1==OTC_HEAT_FIX){
        setting = li.fixTempHeatC1 * 10;
    }
}
```

### OTC Type Constants

From JavaScript and constants:
- **Heating OTC Types**: 
  - `0` = None
  - `1` = Points
  - `2` = Gradient
  - `3` = **FIX** (Fixed mode - only this allows manual temperature control)

- **Cooling OTC Types**:
  - `0` = None
  - `1` = Points
  - `2` = **FIX** (Fixed mode - only this allows manual temperature control)

### API Data Structure

The installation devices API response structure:
```json
{
  "data": [{
    "indoors": [{
      "heatingStatus": {
        "otcTypeHeatC1": 3,  // OTC_HEATING_TYPE_FIX
        "otcTypeCoolC1": 2,  // OTC_COOLING_TYPE_FIX
        "otcTypeHeatC2": 3,
        "otcTypeCoolC2": 2,
        ...
      },
      "heatingSetting": {
        "fixTempHeatC1": 40,
        "fixTempCoolC1": 19,
        "fixTempHeatC2": 40,
        "fixTempCoolC2": 19,
        ...
      }
    }]
  }]
}
```

## Files Modified

### 1. `custom_components/csnet_home/api.py`
- Added `get_heating_status_from_installation_devices()` helper method
- Added `get_heating_setting_from_installation_devices()` helper method
- Added `is_fixed_water_temperature_editable()` method
- Added `get_fixed_water_temperature()` method
- Added `async_set_fixed_water_temperature()` method
- Updated `async_set_temperature()` to handle zone 6 (C2_WATER)
- Updated all methods to use helper methods for navigation

### 2. `custom_components/csnet_home/number.py` (NEW FILE)
- Created new number platform
- `CSNetHomeFixedWaterTemperatureNumber` entity class
- Automatically creates entities only when OTC type is FIX
- Supports C1 and C2, heating and cooling modes
- Entity is only available when OTC type is FIX

### 3. `custom_components/csnet_home/climate.py`
- Updated `target_temperature` property to return `None` for water circuits when OTC is not FIX
- Updated `async_set_temperature()` to check OTC type before allowing temperature changes
- Updated OTC attributes section to use helper method

### 4. `custom_components/csnet_home/__init__.py`
- Added `Platform.NUMBER` to PLATFORMS list

## Entity Naming

### Number Entities Created

When OTC type is FIX for a circuit/mode, number entities are created:

- `number.{zone_name}_fixed_water_temperature_heating_c1` - For C1 heating mode
- `number.{zone_name}_fixed_water_temperature_cooling_c1` - For C1 cooling mode
- `number.{zone_name}_fixed_water_temperature_heating_c2` - For C2 heating mode
- `number.{zone_name}_fixed_water_temperature_cooling_c2` - For C2 cooling mode

**Example**: 
- `number.salon_fixed_water_temperature_heating_c1`
- `number.bibliotheque_fixed_water_temperature_cooling_c2`

**Important**: Fixed temperature is a **CIRCUIT-level** setting that affects both air and water zones:
- Number entities are created for **air zones (1, 2) when available** (preferred for UI)
- If air zone is not available, entities are created for **water zones (5, 6)**
- The fixed temperature controls the **water supply temperature** for the entire circuit (C1 or C2)

### Climate Entity Behavior

**For air circuits (zone 1, 2):**
- `target_temperature` always returns the room temperature (`settingTempRoomZ1/Z2`) - **always editable**
- Fixed water temperature is controlled via a **separate number entity** (when OTC is FIX)
- The room temperature and fixed water temperature are **independent settings**

**For water circuits (zone 5, 6):**
- **When OTC type is FIX**: `target_temperature` returns the current fixed temperature value
- **When OTC type is NOT FIX**: `target_temperature` returns `None` (unavailable)

This prevents users from trying to set temperature when it's not editable.

## Usage Examples

### Example 1: User with Fixed Temperature Mode (OTC = FIX)

**User has OTC type = FIX for C1 heating:**
- ✅ Climate entity shows `target_temperature` (editable)
- ✅ Number entity `fixed_water_temperature_heating_c1` appears (editable)
- ✅ Both can set the fixed water temperature

### Example 2: User with Law Temperature Mode (OTC = Gradient/Points)

**User has OTC type = Gradient for C1 heating:**
- ❌ Climate entity shows `target_temperature = None` (not editable)
- ❌ Number entity does NOT appear (unavailable)
- ✅ Temperature is automatically calculated by the system

## Testing Checklist

- [ ] Test with OTC type = FIX (heating mode)
  - [ ] Number entity appears
  - [ ] Climate entity shows target temperature
  - [ ] Can set temperature via number entity
  - [ ] Can set temperature via climate entity (if enabled)

- [ ] Test with OTC type = FIX (cooling mode)
  - [ ] Number entity appears
  - [ ] Can set temperature via number entity

- [ ] Test with OTC type = Gradient/Points (law mode)
  - [ ] Number entity does NOT appear
  - [ ] Climate entity shows target_temperature = None
  - [ ] Attempting to set temperature via climate shows warning

- [ ] Test with C1 and C2 circuits
  - [ ] Both C1 and C2 entities created independently
  - [ ] Each circuit checks its own OTC type

- [ ] Test mode changes
  - [ ] Number entities update when HVAC mode changes
  - [ ] Availability checks correct mode

## Technical Notes

### Data Structure Navigation

The API response structure is nested:
```
installation_devices_data
  └─ data[0]
      └─ indoors[0]
          ├─ heatingStatus (contains OTC types)
          └─ heatingSetting (contains fixed temperatures)
```

Helper methods navigate this structure automatically.

### OTC Type Checking Logic

```python
# For heating mode (mode == 1)
if otcTypeHeatC{circuit} == 3:  # OTC_HEATING_TYPE_FIX
    # Editable
else:
    # Not editable (law/curve/gradient)

# For cooling mode (mode == 0)
if otcTypeCoolC{circuit} == 2:  # OTC_COOLING_TYPE_FIX
    # Editable
else:
    # Not editable
```

### Availability Logic

Number entities are only created when:
1. OTC type is FIX for the circuit and mode
2. Sensor data exists for the water zone (zone 5 or 6)
3. Installation devices data is available

The `available` property returns `False` when OTC type changes away from FIX.

## Backward Compatibility

- ✅ No breaking changes
- ✅ Existing climate entities continue to work for air circuits
- ✅ Existing climate entities work for water circuits when OTC is FIX
- ✅ Water circuits gracefully handle non-FIX OTC types
- ✅ All existing sensors remain unchanged

## Future Enhancements

Potential improvements:
1. Add UI hint in climate entity when temperature is not editable
2. Show OTC type in climate entity attributes
3. Add service to switch OTC type (requires CSNet Manager configuration)
4. Add template sensors for fixed temperature values

---

**Status**: ✅ Implementation Complete
**Date**: October 29, 2025
**Issue**: Addresses issue #120

