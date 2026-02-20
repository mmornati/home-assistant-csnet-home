import sys
import os
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock

# Add current directory to path
sys.path.append(os.getcwd())

# Handle missing homeassistant dependency in restricted environments
try:
    import homeassistant.core
except ImportError:
    import types

    # Mock homeassistant package
    ha = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha

    # Mock core
    ha.core = types.ModuleType("homeassistant.core")
    sys.modules["homeassistant.core"] = ha.core
    ha.core.HomeAssistant = MagicMock()

    # Mock config_entries
    ha.config_entries = types.ModuleType("homeassistant.config_entries")
    sys.modules["homeassistant.config_entries"] = ha.config_entries
    ha.config_entries.ConfigEntry = MagicMock()

    # Mock const
    ha.const = types.ModuleType("homeassistant.const")
    sys.modules["homeassistant.const"] = ha.const
    ha.const.CONF_SCAN_INTERVAL = "scan_interval"
    ha.const.Platform = MagicMock()
    ha.const.Platform.SENSOR = "sensor"
    ha.const.Platform.CLIMATE = "climate"
    ha.const.Platform.WATER_HEATER = "water_heater"
    ha.const.Platform.NUMBER = "number"

    # Mock helpers
    ha.helpers = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = ha.helpers

    # Mock device_registry
    ha.helpers.device_registry = types.ModuleType(
        "homeassistant.helpers.device_registry"
    )
    sys.modules["homeassistant.helpers.device_registry"] = ha.helpers.device_registry
    ha.helpers.device_registry.DeviceEntry = MagicMock()

    # Mock update_coordinator
    ha.helpers.update_coordinator = types.ModuleType(
        "homeassistant.helpers.update_coordinator"
    )
    sys.modules["homeassistant.helpers.update_coordinator"] = (
        ha.helpers.update_coordinator
    )

    class MockDataUpdateCoordinator:
        def __init__(self, hass, logger, name, update_method, update_interval):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_method = update_method
            self.update_interval = update_interval
            self._listeners = []

        async def _async_update_data(self):
            raise NotImplementedError

    ha.helpers.update_coordinator.DataUpdateCoordinator = MockDataUpdateCoordinator

    # Also mock aiohttp if missing
    try:
        import aiohttp
    except ImportError:
        sys.modules["aiohttp"] = MagicMock()

    try:
        import async_timeout
    except ImportError:
        sys.modules["async_timeout"] = MagicMock()

# Now import coordinator
from custom_components.csnet_home.coordinator import CSNetHomeCoordinator

# Define simulated latencies
LATENCY_LOAD_TRANSLATIONS = 0.1
LATENCY_ELEMENTS = 0.5
LATENCY_DEVICES = 0.5
LATENCY_ALARMS = 0.2


async def run_benchmark(hass=None):
    """Benchmark the coordinator update performance."""
    if hass is None:
        hass = MagicMock()

    # Mock the API
    mock_api = MagicMock()
    mock_api.logged_in = True  # Assume logged in initially for simpler benchmark

    async def slow_load_translations():
        await asyncio.sleep(LATENCY_LOAD_TRANSLATIONS)

    async def slow_get_elements():
        await asyncio.sleep(LATENCY_ELEMENTS)
        return {"common_data": {"installation": "123"}, "sensors": []}

    async def slow_get_devices():
        await asyncio.sleep(LATENCY_DEVICES)
        return {"some": "device_data"}

    async def slow_get_alarms():
        await asyncio.sleep(LATENCY_ALARMS)
        return {"some": "alarm_data"}

    mock_api.load_translations = AsyncMock(side_effect=slow_load_translations)
    mock_api.async_get_elements_data = AsyncMock(side_effect=slow_get_elements)
    mock_api.async_get_installation_devices_data = AsyncMock(
        side_effect=slow_get_devices
    )
    mock_api.async_get_installation_alarms = AsyncMock(side_effect=slow_get_alarms)
    # Ensure translate_alarm doesn't fail
    mock_api.translate_alarm = MagicMock(return_value="Translated Alarm")
    mock_api.get_heating_status_from_installation_devices = MagicMock(return_value={})

    # Setup HASS data
    hass.data = {"csnet_home": {"test_entry": {"api": mock_api}}}

    # Initialize Coordinator
    coordinator = CSNetHomeCoordinator(hass, 30, "test_entry")

    # Measure execution time
    start_time = time.perf_counter()
    await coordinator._async_update_data()
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"\n[BENCHMARK] Execution time: {duration:.4f} seconds")

    # Verify calls were made
    mock_api.load_translations.assert_called_once()
    mock_api.async_get_elements_data.assert_called_once()
    mock_api.async_get_installation_devices_data.assert_called_once()
    mock_api.async_get_installation_alarms.assert_called_once()

    # Assert performance is optimized (should be < sum of latencies)
    assert (
        duration < 1.0
    ), f"Performance regression! Time: {duration:.4f}s (expected < 1.0s)"

    return duration


# For pytest execution
try:
    import pytest

    @pytest.mark.asyncio
    async def test_coordinator_performance(hass):
        await run_benchmark(hass)

except ImportError:
    pass

# For standalone execution
if __name__ == "__main__":
    asyncio.run(run_benchmark())
