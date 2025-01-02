from unittest.mock import patch
import pytest
from custom_components.csnet_home.api import CSNetHomeAPI

@pytest.fixture
def cloud_service_api():
    """Fixture for CloudServiceAPI."""
    return CSNetHomeAPI(None)

@patch("requests.Session.post")
def test_login(mock_post, cloud_service_api):
    """Test login to cloud service."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.cookies = {"session_id": "fake_session_id"}

    cloud_service_api.username = "test_user"
    cloud_service_api.password = "test_password"

    # Simulate login
    cloud_service_api.login()

    # Assert that cookies are saved
    assert cloud_service_api.cookies is not None
    assert "session_id" in cloud_service_api.cookies

@patch("requests.Session.get")
def test_get_sensor_values(mock_get, cloud_service_api):
    """Test fetching sensor values."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"value": 42}

    # Simulate API call to get sensor data
    sensor_data = cloud_service_api.get_sensor_values()

    # Assert that sensor data is fetched correctly
    assert sensor_data is not None
    assert sensor_data["value"] == 42
