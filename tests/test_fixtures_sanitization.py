"""Tests for fixture sanitization."""

from tests.fixtures.conftest_fixtures import sanitize_api_response

# Sample data mimicking elements_two_zones.json
SAMPLE_DATA = {
    "status": "success",
    "data": {
        "device_status": [
            {
                "id": 1709,
                "disabled": False,
                "ownerId": 123,
                "name": "Hitachi PAC",
                "lastComm": 1736193442000,
                "type": 0,
                "status": 1,
                "hash": "real_hash",
                "firmware": "1234",
                "key": "111111",
                "currentTime": 20250106205719,
                "currentTimeMillis": 1736193448768,
                "rssi": -70,
            }
        ],
        "rooms": [
            {
                "id": 394,
                "installation_id": 1234,
                "name": "1st Floor",
                "disabled": False,
            },
            {
                "id": 395,
                "installation_id": 1234,
                "name": "2nd Floor",
                "disabled": False,
            },
        ],
        "weatherTemperature": 9,
        "latitude": "50.123456",
        "iu_qty": 1,
        "weatherForecastIcon": "10d",
        "administrator": "admin",
        "holidays": [
            {
                "indoorId": 394,  # Matches room 394
                "year": 0,
                "month": 0,
                "day": 0,
                "hour": -1,
                "minute": -1,
                "c1AirSetting": 17,
                "c2AirSetting": 17,
                "c1Affected": True,
                "c2Affected": True,
                "dhwAffected": True,
                "swpAffected": True,
                "pacAffected": False,
                "iot_time": 20250106205719,
                "dhwSetting": 30,
                "swpSetting": 28,
                "compatibleWithDHWSWPSettings": True,
                "zones": [],
            }
        ],
        "installation": 1234,
        "avOuTemp": 4.0,
        "elements": [
            {
                "parentId": 1234,
                "elementType": 1,
                "parentName": "1st Floor",
                "mode": 1,
                "realMode": 1,
                "onOff": 1,
                "settingTemperature": 19.0,
                "currentTemperature": 19.5,
                "yutaki": True,
                "modelCode": 0,
                "alarmCode": 0,
                "deviceId": 1234,
                "deviceName": "Hitachi PAC",
                "ouAddress": 0,
                "iuAddress": 0,
                "roomId": 394,  # Matches room 394
                "ecocomfort": 1,
                "fanSpeed": -1,
                "operationStatus": 5,
                "hasCooling": False,
                "hasAuto": False,
                "hasBoost": False,
                "c1Demand": True,
                "c2Demand": True,
                "doingBoost": False,
                "timerRunning": False,
                "fixAvailable": False,
                "silentMode": 0,
            },
            {
                "parentId": 1234,
                "elementType": 2,
                "parentName": "2nd Floor",
                "mode": 1,
                "realMode": 1,
                "onOff": 1,
                "settingTemperature": 19.0,
                "currentTemperature": 17.5,
                "yutaki": True,
                "modelCode": 0,
                "alarmCode": 0,
                "deviceId": 1234,
                "deviceName": "Hitachi PAC",
                "ouAddress": 0,
                "iuAddress": 0,
                "roomId": 395,  # Matches room 395
                "ecocomfort": 1,
                "fanSpeed": -1,
                "operationStatus": 5,
                "hasCooling": False,
                "hasAuto": False,
                "hasBoost": False,
                "c1Demand": True,
                "c2Demand": True,
                "doingBoost": False,
                "timerRunning": False,
                "fixAvailable": False,
                "silentMode": 1,
            },
        ],
        "name": "My Home",
        "weatherForecastUpdate": 1736066133704,
        "user_dispayableName": "Myself",
        "longitude": "3.12",
    },
}


def test_sanitize_api_response():
    """Test that API responses are correctly sanitized."""
    sanitized = sanitize_api_response(SAMPLE_DATA)
    data = sanitized["data"]

    # Verify top-level fields
    assert data["latitude"] == "52.379189"
    assert data["longitude"] == "4.899431"
    assert data["name"] == "Home"
    assert data["administrator"] == "admin"
    assert data["user_dispayableName"] == "User"
    assert data["installation"] == 12345

    # Verify device_status
    device = data["device_status"][0]
    assert device["id"] == 1000
    assert device["ownerId"] == 12345
    assert device["name"] == "Device 1"
    assert device["firmware"] == "1.0.0"
    assert device["key"] == "sanitized_key"
    assert device["hash"] == "sanitized_hash"

    # Verify rooms
    room1 = data["rooms"][0]
    room2 = data["rooms"][1]
    assert room1["id"] == 2000
    assert room1["name"] == "Room 1"
    assert room1["installation_id"] == 12345
    assert room2["id"] == 2001
    assert room2["name"] == "Room 2"
    assert room2["installation_id"] == 12345

    # Verify elements
    elem1 = data["elements"][0]
    elem2 = data["elements"][1]
    assert elem1["parentId"] == 12345
    assert elem1["deviceId"] == 12345
    assert elem1["roomId"] == 2000  # Should match Room 1 ID
    assert elem1["parentName"] == "Element 1"
    assert elem2["parentId"] == 12345
    assert elem2["deviceId"] == 12345
    assert elem2["roomId"] == 2001  # Should match Room 2 ID
    assert elem2["parentName"] == "Element 2"

    # Verify holidays
    holiday = data["holidays"][0]
    assert holiday["indoorId"] == 2000  # Should match Room 1 ID

    # Verify metadata
    assert sanitized["_sanitized"] is True
    assert sanitized["_comment"] == "Sanitized test fixture"
