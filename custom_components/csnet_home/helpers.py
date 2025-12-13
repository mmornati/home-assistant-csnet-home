"""Helper functions for CSNet Home integration."""


def extract_heating_status(installation_devices_data):
    """Extract heatingStatus from installation devices data structure.

    Navigates through: data[0].indoors[0].heatingStatus

    Args:
        installation_devices_data: The installation devices API response

    Returns:
        dict or None: heatingStatus dictionary, or None if not found
    """
    if not installation_devices_data:
        return None

    # Try direct access first (if already extracted)
    heating_status = installation_devices_data.get("heatingStatus")
    if heating_status:
        return heating_status

    # Navigate through: data[0].indoors[0].heatingStatus
    data_array = installation_devices_data.get("data", [])
    if isinstance(data_array, list) and len(data_array) > 0:
        first_device = data_array[0]
        if isinstance(first_device, dict):
            indoors_array = first_device.get("indoors", [])
            if isinstance(indoors_array, list) and len(indoors_array) > 0:
                first_indoors = indoors_array[0]
                if isinstance(first_indoors, dict):
                    return first_indoors.get("heatingStatus", {})

    return None
