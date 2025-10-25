# Test Fixtures

This directory contains sanitized API response fixtures for testing the CSNet Home integration without requiring real credentials or API access.

## Directory Structure

```
fixtures/
├── README.md                          # This file
├── api_responses/                     # CSNet API response fixtures
│   ├── elements_two_zones.json       # Standard 2-zone system
│   ├── elements_empty_names.json     # System with missing device/room names
│   ├── elements_with_fan_speeds.json # System with fan coil control
│   ├── elements_with_bcd_alarm.json  # System with BCD-encoded alarm
│   ├── installation_devices.json     # Installation devices data
│   └── installation_alarms.json      # Installation alarms data
└── conftest_fixtures.py               # Pytest fixtures for loading test data

```

## Usage in Tests

### Loading Fixtures

```python
import pytest
from tests.fixtures.conftest_fixtures import load_fixture

def test_my_feature():
    # Load a fixture
    elements_data = load_fixture("api_responses/elements_two_zones.json")
    
    # Use in your test
    assert elements_data["status"] == "success"
```

### Using Fixtures in Mocks

```python
@pytest.mark.asyncio
async def test_with_mock_api(mock_aiohttp_client, hass):
    mock_client = mock_aiohttp_client.return_value
    mock_response = mock_client.get.return_value.__aenter__.return_value
    mock_response.status = 200
    
    # Load fixture data
    mock_response.json = AsyncMock(
        return_value=load_fixture("api_responses/elements_two_zones.json")
    )
    
    # Run your test
    api = CSNetHomeAPI(hass, "user", "pass")
    api._session = mock_client
    data = await api.async_get_elements_data()
    
    # Assertions...
```

## Recording New Fixtures

### Method 1: From Browser DevTools (Recommended)

1. **Open CSNet Manager** in your browser with DevTools (F12)
2. **Navigate to Network tab**
3. **Perform actions** in the web interface
4. **Find the API call** (e.g., `elements`, `installationdevices`)
5. **Right-click** → **Copy** → **Copy Response**
6. **Sanitize the data:**
   - Replace personal information (names, locations, IDs)
   - Keep the structure intact
   - Use placeholder values like "Device1", "Room1", etc.
7. **Save** to `tests/fixtures/api_responses/`

### Method 2: From Integration Debug Logs

If you have debug logging enabled:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

1. Check your Home Assistant logs
2. Look for API response logs
3. Copy the JSON response
4. Sanitize as above
5. Save to fixtures directory

### Method 3: Using pytest to Record

Create a test that dumps real API responses (run once with real credentials):

```python
import json
import pytest

@pytest.mark.skip("Only run manually to record fixtures")
@pytest.mark.asyncio
async def test_record_api_response(hass):
    """Record real API responses for fixtures."""
    api = CSNetHomeAPI(hass, "real_user", "real_pass")
    
    # Get real data
    data = await api.async_get_elements_data()
    
    # Sanitize before saving
    # TODO: Implement sanitization
    
    # Save to fixture
    with open("tests/fixtures/api_responses/new_fixture.json", "w") as f:
        json.dump(data, f, indent=2)
```

## Sanitization Guidelines

When creating fixtures from real data:

### ✅ DO Sanitize:
- Personal names → "Device1", "Room1", "User1"
- Location data → Generic coordinates
- Device IDs → Sequential numbers (1234, 1235, etc.)
- Installation IDs → Generic IDs
- Firmware versions → Generic like "1234"
- Keys/tokens → "xxx" or "test-token"

### ❌ DON'T Modify:
- Data structure (keep all fields)
- Data types (numbers, strings, booleans)
- Array lengths
- Nested object structures
- Field names
- Value ranges (if temperature is 19.5, keep it around that range)

## Fixture Naming Convention

Use descriptive names that indicate the test scenario:

- `elements_SCENARIO.json` - Main elements endpoint responses
- `installation_devices_SCENARIO.json` - Installation devices data
- `installation_alarms_SCENARIO.json` - Alarm data

Examples:
- `elements_two_zones.json` - Standard 2-zone system
- `elements_multi_zone.json` - System with 3+ zones
- `elements_cooling_only.json` - Cooling-only configuration
- `elements_with_dhw.json` - System with water heater
- `elements_alarm_active.json` - System with active alarm

## Contributing Fixtures

If you have a unique device configuration, please contribute fixtures!

1. Follow the recording and sanitization process above
2. Create a descriptive fixture file
3. Add a comment in the fixture explaining what makes it special
4. Update this README with the new fixture description
5. Submit a PR

## Example Fixture Structure

```json
{
  "_comment": "Two-zone heating system with fan coil support",
  "_sanitized": true,
  "_source": "Real API response from 2025-01-06",
  "status": "success",
  "data": {
    "elements": [...],
    "device_status": [...],
    ...
  }
}
```

## Fixture Validation

To validate fixtures are working correctly:

```bash
# Run tests with fixtures
pytest tests/test_api.py -v

# Run specific fixture test
pytest tests/test_api.py::test_api_get_elements_data_success -v
```

## Troubleshooting

### Fixture Not Loading

- Check file path is correct
- Verify JSON is valid (use `python -m json.tool fixture.json`)
- Ensure file is in the correct directory

### Test Failing with Fixture

- Compare fixture structure with what code expects
- Check for missing fields
- Verify data types match
- Look at the API parsing code to understand expected structure

## Resources

- [CSNet Manager Web Interface](https://www.csnetmanager.com)
- [Integration Documentation](../../README.md)
- [API Implementation](../../custom_components/csnet_home/api.py)
- [Test Suite](../README.md)

