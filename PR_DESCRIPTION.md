# Add Water System Sensors Support

## Overview
This PR adds comprehensive water system monitoring capabilities to the CSNet Home integration by implementing support for the `/data/installationdevices` API endpoint. This enables users to monitor water-related metrics that were previously unavailable in Home Assistant.

## New Features

### 🌊 Water System Sensors
Added 7 new sensor types for comprehensive water system monitoring:

- **Water Speed** (100%) - Pump/flow speed with speedometer icon
- **Water Debit** (3.9m³/h) - Water flow rate with water icon
- **Water In Temperature** (20°C) - Incoming water temperature
- **Water Out Temperature** (20°C) - Outgoing water temperature  
- **Set Water Temperature** (23°C) - Target water temperature
- **Pressure Water Circuit** (4.48 bar) - Water circuit pressure
- **Temp Out Water from Exchanger** (20°C) - Heat exchanger outlet temperature

### 🏠 Installation-Level Monitoring
- Water sensors are created at the installation level, providing system-wide visibility
- Each device with water data gets its own set of sensors
- Sensors are grouped under dedicated "Water System" devices in Home Assistant

## Technical Changes

### API Layer (`api.py`)
- **New Method**: `async_get_installation_devices_data()`
  - Calls `/data/installationdevices?installationId=-1` endpoint
  - Extracts water-related data from installation devices
  - Maps JSON response fields to standardized sensor data structure
  - Handles both success and error scenarios gracefully

### Constants (`const.py`)
- **New Endpoint**: `INSTALLATION_DEVICES_PATH = "/data/installationdevices"`
- **Water Sensor Configuration**: `WATER_SENSOR_TYPES` dictionary
  - Defines units, device classes, and icons for each sensor type
  - Supports temperature, pressure, and custom sensor types

### Data Coordination (`coordinator.py`)
- **Enhanced Data Flow**: Now fetches from both existing and new endpoints
- **New Method**: `get_water_data()` for accessing water sensor data
- **Storage**: Water data stored alongside existing sensor data

### Sensor Implementation (`sensor.py`)
- **New Class**: `CSNetHomeWaterSensor` for water-specific sensors
- **Automatic Creation**: Sensors created for each device with water data
- **Proper Classification**: Temperature and pressure sensors with correct device classes
- **Icon Support**: Appropriate icons for each sensor type
- **Unique Naming**: `{Device Name} {Sensor Name}` format

### Testing (`test_api.py`)
- **Comprehensive Tests**: Added tests for both success and failure scenarios
- **Data Validation**: Verifies proper extraction and mapping of water data
- **Backward Compatibility**: All existing tests continue to pass

## Usage

### Sensor Naming Convention
Water sensors follow the pattern: `{Device Name} {Sensor Name}`
- Example: `Water Device 1 Water Speed`
- Example: `Water Device 1 Water In Temperature`

### Device Organization
- Water sensors are grouped under "Water System" devices
- Separate from existing climate/room devices
- Each installation device with water data gets its own device group

### Home Assistant Integration
- Sensors appear automatically after integration restart
- Full Home Assistant sensor features (history, automation, etc.)
- Proper units and device classes for optimal UI experience

## API Integration Details

### New Endpoint
```http
GET /data/installationdevices?installationId=-1
```

### Expected Response Structure
```json
{
  "status": "success",
  "data": [
    {
      "id": 1001,
      "name": "Water Device 1",
      "waterSpeed": 100,
      "waterDebit": 3.9,
      "waterInTemperature": 20.0,
      "waterOutTemperature": 20.0,
      "setWaterTemperature": 23.0,
      "pressureWaterCircuit": 4.48,
      "tempOutWaterExchanger": 20.0
    }
  ]
}
```

## Backward Compatibility
- ✅ All existing functionality preserved
- ✅ No breaking changes to existing sensors
- ✅ Existing API calls unchanged
- ✅ All existing tests pass

## Testing
- ✅ New API method tests added
- ✅ Water sensor creation logic tested
- ✅ Error handling scenarios covered
- ✅ All existing tests continue to pass (23/23)

## Files Modified
- `custom_components/csnet_home/api.py` - New installation devices API method
- `custom_components/csnet_home/const.py` - New constants and water sensor types
- `custom_components/csnet_home/coordinator.py` - Enhanced data coordination
- `custom_components/csnet_home/sensor.py` - New water sensor class and setup
- `tests/test_api.py` - Comprehensive test coverage

## Benefits
1. **Complete System Monitoring**: Users can now monitor all aspects of their water heating system
2. **Better Home Automation**: Water sensors enable advanced automation scenarios
3. **System Health Monitoring**: Pressure and temperature sensors help identify issues early
4. **Energy Efficiency**: Flow rate and temperature data support optimization
5. **Installation-Level Visibility**: System-wide view rather than device-specific

## Future Enhancements
- Potential for water heater controls based on sensor data
- Advanced automation templates for water system management
- Integration with energy monitoring systems
- Historical data analysis and reporting

---

**Closes**: #21 (Add new sensors getting from all remaining device data)
