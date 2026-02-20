"""Fixtures loader for CSNet Home tests."""

import copy
import json
from pathlib import Path
from typing import Any, Dict

FIXTURES_DIR = Path(__file__).parent


def load_fixture(fixture_path: str) -> Dict[str, Any]:
    """
    Load a JSON fixture file.

    Args:
        fixture_path: Relative path to fixture file from fixtures directory
                     (e.g., "api_responses/elements_two_zones.json")

    Returns:
        Dictionary containing the fixture data

    Raises:
        FileNotFoundError: If fixture file doesn't exist
        json.JSONDecodeError: If fixture file is not valid JSON

    Example:
        >>> data = load_fixture("api_responses/elements_two_zones.json")
        >>> assert data["status"] == "success"
    """
    fixture_file = FIXTURES_DIR / fixture_path

    if not fixture_file.exists():
        raise FileNotFoundError(
            f"Fixture file not found: {fixture_file}\n"
            f"Available fixtures in {FIXTURES_DIR}:\n"
            + "\n".join(
                str(f.relative_to(FIXTURES_DIR)) for f in FIXTURES_DIR.rglob("*.json")
            )
        )

    with open(fixture_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_fixture(fixture_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """
    Save data to a JSON fixture file.

    Args:
        fixture_path: Relative path to fixture file from fixtures directory
        data: Dictionary to save as JSON
        indent: JSON indentation level (default: 2)

    Example:
        >>> data = {"status": "success", "data": {...}}
        >>> save_fixture("api_responses/new_test.json", data)
    """
    fixture_file = FIXTURES_DIR / fixture_path
    fixture_file.parent.mkdir(parents=True, exist_ok=True)

    with open(fixture_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def list_fixtures(directory: str = "") -> list[str]:
    """
    List all available fixture files.

    Args:
        directory: Optional subdirectory to list (e.g., "api_responses")

    Returns:
        List of fixture file paths relative to fixtures directory

    Example:
        >>> fixtures = list_fixtures("api_responses")
        >>> assert "api_responses/elements_two_zones.json" in fixtures
    """
    search_dir = FIXTURES_DIR / directory if directory else FIXTURES_DIR
    return [str(f.relative_to(FIXTURES_DIR)) for f in search_dir.rglob("*.json")]


def sanitize_api_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize an API response for use as a test fixture.

    This function removes or replaces sensitive information while
    maintaining the structure and data types. It specifically handles
    CSNet Home API response structures to ensure referential integrity.

    Args:
        response: Raw API response dictionary

    Returns:
        Sanitized response dictionary safe for committing to repository

    Example:
        >>> # Example usage
        >>> real_response = {"data": {"rooms": [{"id": 123, "name": "Bedroom"}]}}
        >>> safe_response = sanitize_api_response(real_response)
        >>> save_fixture("new_fixture.json", safe_response)
    """
    # Deep copy to avoid modifying original
    sanitized = copy.deepcopy(response)

    # Add metadata
    sanitized["_sanitized"] = True
    sanitized["_comment"] = "Sanitized test fixture"

    # Mappings for ID consistency
    room_map = {}
    device_map = {}

    # Check for main CSNet API structure
    if isinstance(sanitized, dict) and "data" in sanitized and isinstance(sanitized["data"], dict):
        data = sanitized["data"]

        # Top level PII fields
        if "latitude" in data:
            data["latitude"] = "52.379189"
        if "longitude" in data:
            data["longitude"] = "4.899431"
        if "name" in data:
            data["name"] = "Home"
        if "administrator" in data:
            data["administrator"] = "admin"
        if "user_dispayableName" in data:
            data["user_dispayableName"] = "User"
        if "installation" in data:
            data["installation"] = 12345

        # 1. Sanitize Rooms
        if "rooms" in data and isinstance(data["rooms"], list):
            for i, room in enumerate(data["rooms"]):
                if not isinstance(room, dict):
                    continue
                old_id = room.get("id")
                new_id = 2000 + i
                if old_id is not None:
                    room_map[old_id] = new_id

                room["id"] = new_id
                room["name"] = f"Room {i + 1}"
                if "installation_id" in room:
                    room["installation_id"] = 12345

        # 2. Sanitize Device Status
        if "device_status" in data and isinstance(data["device_status"], list):
            for i, device in enumerate(data["device_status"]):
                if not isinstance(device, dict):
                    continue
                old_id = device.get("id")
                new_id = 1000 + i
                if old_id is not None:
                    device_map[old_id] = new_id

                device["id"] = new_id
                device["ownerId"] = 12345
                device["name"] = f"Device {i + 1}"
                device["firmware"] = "1.0.0"
                device["key"] = "sanitized_key"
                device["hash"] = "sanitized_hash"

        # 3. Sanitize Elements
        if "elements" in data and isinstance(data["elements"], list):
            for i, elem in enumerate(data["elements"]):
                if not isinstance(elem, dict):
                    continue

                # Update relationships using maps
                if "roomId" in elem and elem["roomId"] in room_map:
                    elem["roomId"] = room_map[elem["roomId"]]

                if "deviceId" in elem and elem["deviceId"] in device_map:
                    elem["deviceId"] = device_map[elem["deviceId"]]
                elif "deviceId" in elem:
                    # Fallback if device ID matches installation or unknown
                    elem["deviceId"] = 12345

                if "parentId" in elem:
                    elem["parentId"] = 12345

                # Update names
                elem["parentName"] = f"Element {i + 1}"
                if "deviceName" in elem:
                    elem["deviceName"] = f"Device {i + 1}"

        # 4. Sanitize Holidays
        if "holidays" in data and isinstance(data["holidays"], list):
            for holiday in data["holidays"]:
                if not isinstance(holiday, dict):
                    continue
                if "indoorId" in holiday:
                    if holiday["indoorId"] in room_map:
                        holiday["indoorId"] = room_map[holiday["indoorId"]]
                    elif holiday["indoorId"] in device_map:
                        holiday["indoorId"] = device_map[holiday["indoorId"]]

    # Recursive pass to catch any other common PII fields
    def recursive_clean(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "username":
                    obj[key] = "test_user"
                elif key == "password":
                    obj[key] = "***"
                elif key == "email":
                    obj[key] = "test@example.com"
                elif key == "latitude" and isinstance(value, str) and value != "52.379189":
                    obj[key] = "52.379189"
                elif key == "longitude" and isinstance(value, str) and value != "4.899431":
                    obj[key] = "4.899431"

                if isinstance(value, (dict, list)):
                    recursive_clean(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    recursive_clean(item)

    recursive_clean(sanitized)

    return sanitized
