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
    maintaining the structure and data types.

    Args:
        response: Raw API response dictionary

    Returns:
        Sanitized response dictionary safe for committing to repository

    Example:
        >>> real_response = {"data": "example"}
        >>> safe_response = sanitize_api_response(real_response)
        >>> save_fixture("new_fixture.json", safe_response)
    """
    # Sanitize common sensitive fields (deep copy to avoid modifying original)
    sanitized = copy.deepcopy(response)

    # Add metadata
    sanitized["_sanitized"] = True
    sanitized["_comment"] = "Sanitized test fixture"

    # Example sanitization (customize based on your needs)
    if isinstance(sanitized, dict):
        if "username" in sanitized:
            sanitized["username"] = "test_user"
        if "password" in sanitized:
            sanitized["password"] = "***"
        if "email" in sanitized:
            sanitized["email"] = "test@example.com"
        if "latitude" in sanitized and isinstance(sanitized["latitude"], str):
            sanitized["latitude"] = "50.123456"
        if "longitude" in sanitized and isinstance(sanitized["longitude"], str):
            sanitized["longitude"] = "3.123456"

        # Recursively sanitize nested dictionaries and lists
        for key, value in sanitized.items():
            if isinstance(value, dict):
                sanitized[key] = sanitize_api_response(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_api_response(item) if isinstance(item, dict) else item
                    for item in value
                ]

    return sanitized
