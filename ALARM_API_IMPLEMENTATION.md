# Alarm API Implementation Summary

## Overview
This document describes the implementation of the dedicated alarm API endpoint (`/data/installationalarms`) for retrieving alarm information from the CSNet Manager service.

## Changes Made

### 1. Constants (`const.py`)
- Added `INSTALLATION_ALARMS_PATH = "/data/installationalarms"` constant

### 2. API Class (`api.py`)
- Added `self.installation_id` attribute to store the installation ID from elements data
- Added `async_get_installation_alarms()` method to fetch alarms from the dedicated endpoint
- Modified `async_get_elements_data()` to capture and store the installation ID from the response

### 3. Coordinator (`coordinator.py`)
- Updated `_async_update_data()` to fetch installation alarms data
- Added alarm data to `common_data` dictionary
- Added `get_installation_alarms_data()` method to retrieve alarm information

### 4. Tests
- Added 3 new tests in `test_api.py` for the alarm API endpoint:
  - `test_api_get_installation_alarms_success`
  - `test_api_get_installation_alarms_no_installation_id`
  - `test_api_get_installation_alarms_failure`
- Added 2 new tests in `test_coordinator.py`:
  - `test_coordinator_get_installation_alarms_data`
  - `test_coordinator_get_installation_alarms_data_empty`
- Updated existing coordinator tests to mock the new `async_get_installation_alarms` method

## API Endpoint Details

### URL Format
```
https://www.csnetmanager.com/data/installationalarms?installationId={installation_id}&_csrf={csrf_token}
```

### Request Headers
- `accept: */*`
- `x-requested-with: XMLHttpRequest`
- Standard headers from `COMMON_API_HEADERS`

### Request Method
GET

### Authentication
- Requires active session (cookies)
- Requires XSRF token
- Requires installation ID (obtained from `/data/elements` response)

## How It Works

1. During initialization, `installation_id` is `None`
2. When `async_get_elements_data()` is called, it extracts the `installation` field from the response and stores it in `self.installation_id`
3. The coordinator calls `async_get_installation_alarms()` during each update cycle
4. If `installation_id` is available, the alarm endpoint is queried with the installation ID and CSRF token
5. The alarm data is stored in `common_data["installation_alarms"]` for access by sensors or other components
6. The existing alarm notification system (based on `alarmCode` from elements) continues to work alongside the new endpoint

## Backward Compatibility

✅ **Fully backward compatible**
- The existing alarm code tracking from `/data/elements` continues to function
- Alarm sensors (`alarm_code`, `alarm_active`, `alarm_message`) continue to work as before
- Persistent notifications for alarms continue to be sent
- The new endpoint provides additional alarm information that can be used by future enhancements

## Test Results

All 51 tests pass, including:
- 20 API tests (including 3 new alarm API tests)
- 12 Coordinator tests (including 2 new alarm data tests)
- 10 Climate tests
- 9 Sensor tests

## Future Enhancements

The alarm data from the dedicated endpoint can be used to:
1. Create more detailed alarm sensors
2. Provide historical alarm information
3. Display alarm trends
4. Enhanced alarm notifications with more context
5. Alarm acknowledgment/clearing functionality (if the API supports it)

## Notes

- The alarm endpoint requires an installation ID, which is only available after the first successful call to `/data/elements`
- If no installation ID is available, the method returns `None` without making a request
- The endpoint uses the CSRF token for security, matching the pattern used in the provided curl command

