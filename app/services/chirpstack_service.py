"""
ChirpStack API service for LoRaWAN device and gateway management.

This service provides:
- Downlink command sending (relay control)
- Device management (create, list, get, delete)
- Gateway management (create, list, get, delete)
- Application and device profile listing
"""
from __future__ import annotations

import base64
import logging
from typing import Tuple, Optional, Dict, Any, List

import requests
from flask import current_app

logger = logging.getLogger(__name__)


# Pre-calculated Modbus commands for SDM320C relay control
# Format: Slave(01) + Function(05) + Address(0000) + Value + CRC16
RELAY_OFF_COMMAND = bytes([0x01, 0x05, 0x00, 0x00, 0x00, 0x00, 0xCD, 0xCA])
RELAY_ON_COMMAND = bytes([0x01, 0x05, 0x00, 0x00, 0xFF, 0x00, 0x8C, 0x3A])


def get_config() -> Dict[str, Any]:
    """Get ChirpStack configuration from Flask app config."""
    return {
        "api_url": current_app.config.get("CHIRPSTACK_API_URL", "http://localhost:8090"),
        "api_key": current_app.config.get("CHIRPSTACK_API_KEY", ""),
        "tenant_id": current_app.config.get("CHIRPSTACK_TENANT_ID", ""),
        "passthrough_port": current_app.config.get("CHIRPSTACK_PASSTHROUGH_PORT", 5),
    }


def _get_headers() -> Dict[str, str]:
    """Get authorization headers for ChirpStack API."""
    config = get_config()
    return {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }


def _make_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
) -> Tuple[bool, Any]:
    """
    Make a request to the ChirpStack API.

    Returns:
        Tuple of (success: bool, data or error_message)
    """
    config = get_config()

    if not config["api_key"]:
        return False, "ChirpStack API key not configured"

    url = f"{config['api_url']}{endpoint}"
    headers = _get_headers()

    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
            headers=headers,
            timeout=30,
        )

        if response.status_code in (200, 201):
            try:
                return True, response.json()
            except ValueError:
                return True, {}

        # Handle error responses
        error_message = f"ChirpStack API error: {response.status_code}"
        try:
            error_data = response.json()
            if "message" in error_data:
                error_message = error_data["message"]
            elif "error" in error_data:
                error_message = error_data["error"]
        except (ValueError, KeyError):
            error_message = f"ChirpStack API error: {response.status_code} - {response.text}"

        logger.error(f"ChirpStack request failed: {error_message}")
        return False, error_message

    except requests.exceptions.Timeout:
        return False, "ChirpStack request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Failed to connect to ChirpStack"
    except requests.exceptions.RequestException as e:
        return False, f"ChirpStack request failed: {str(e)}"


# =============================================================================
# DOWNLINK COMMANDS
# =============================================================================

def send_downlink(
    device_eui: str,
    payload: bytes,
    port: Optional[int] = None,
    confirmed: bool = False,
) -> Tuple[bool, str]:
    """
    Send a downlink command to a LoRaWAN device via ChirpStack.

    Args:
        device_eui: The device EUI (16 hex characters)
        payload: Raw bytes to send
        port: LoRaWAN port (defaults to passthrough port from config)
        confirmed: Whether to request confirmation (ACK)

    Returns:
        Tuple of (success: bool, message: str)
    """
    config = get_config()

    if port is None:
        port = config["passthrough_port"]

    payload_b64 = base64.b64encode(payload).decode("utf-8")

    body = {
        "queueItem": {
            "confirmed": confirmed,
            "data": payload_b64,
            "fPort": port,
        }
    }

    logger.info(f"Sending downlink to {device_eui} on port {port}: {payload.hex()}")

    success, result = _make_request(
        "POST",
        f"/api/devices/{device_eui}/queue",
        json_data=body,
    )

    if success:
        logger.info(f"Downlink queued successfully for {device_eui}")
        return True, "Downlink queued successfully"

    return False, result


def send_relay_command(device_eui: str, action: str) -> Tuple[bool, str]:
    """
    Send a relay control command to an Eastron SDM320C meter.

    Args:
        device_eui: The device EUI of the UC100 bridge
        action: "on" to restore power, "off" to disconnect power

    Returns:
        Tuple of (success: bool, message: str)
    """
    if action not in ("on", "off"):
        return False, f"Invalid action: {action}. Must be 'on' or 'off'"

    payload = RELAY_OFF_COMMAND if action == "off" else RELAY_ON_COMMAND
    logger.info(f"Sending relay {action.upper()} command to {device_eui}")

    return send_downlink(device_eui, payload)


def get_device_queue(device_eui: str) -> Tuple[bool, Any]:
    """Get the current downlink queue for a device."""
    success, result = _make_request("GET", f"/api/devices/{device_eui}/queue")

    if success:
        return True, result.get("result", [])
    return False, result


# =============================================================================
# APPLICATION MANAGEMENT
# =============================================================================

def list_applications(limit: int = 100) -> Tuple[bool, Any]:
    """
    List all applications in ChirpStack.

    Returns:
        Tuple of (success, list of applications or error message)
    """
    config = get_config()
    params = {"limit": limit}

    # ChirpStack v4 requires tenantId for listing applications
    if config.get("tenant_id"):
        params["tenantId"] = config["tenant_id"]

    success, result = _make_request(
        "GET",
        "/api/applications",
        params=params,
    )

    if success:
        return True, result.get("result", [])
    return False, result


def get_application(application_id: str) -> Tuple[bool, Any]:
    """Get details of a specific application."""
    return _make_request("GET", f"/api/applications/{application_id}")


# =============================================================================
# DEVICE PROFILE MANAGEMENT
# =============================================================================

def list_device_profiles(limit: int = 100) -> Tuple[bool, Any]:
    """
    List all device profiles in ChirpStack.

    Returns:
        Tuple of (success, list of device profiles or error message)
    """
    config = get_config()
    params = {"limit": limit}

    # ChirpStack v4 requires tenantId for listing device profiles
    if config.get("tenant_id"):
        params["tenantId"] = config["tenant_id"]

    success, result = _make_request(
        "GET",
        "/api/device-profiles",
        params=params,
    )

    if success:
        return True, result.get("result", [])
    return False, result


def get_device_profile(device_profile_id: str) -> Tuple[bool, Any]:
    """Get details of a specific device profile."""
    return _make_request("GET", f"/api/device-profiles/{device_profile_id}")


# =============================================================================
# DEVICE MANAGEMENT
# =============================================================================

def list_devices(
    application_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[bool, Any]:
    """
    List devices in ChirpStack.

    Args:
        application_id: Filter by application (optional, but required by ChirpStack v4)
        limit: Maximum number of devices to return
        offset: Offset for pagination

    Returns:
        Tuple of (success, list of devices or error message)
    """
    # If no application_id provided, fetch devices from all applications
    if not application_id:
        # First get all applications
        success, applications = list_applications(limit=100)
        if not success:
            return False, applications

        # Collect devices from all applications
        all_devices = []
        for app in applications:
            app_id = app.get("id")
            if app_id:
                params = {"limit": limit, "offset": offset, "applicationId": app_id}
                success, result = _make_request("GET", "/api/devices", params=params)
                if success:
                    all_devices.extend(result.get("result", []))

        return True, all_devices

    # If application_id provided, fetch devices from that application
    params = {"limit": limit, "offset": offset, "applicationId": application_id}
    success, result = _make_request("GET", "/api/devices", params=params)

    if success:
        return True, result.get("result", [])
    return False, result


def get_device(device_eui: str) -> Tuple[bool, Any]:
    """
    Get details of a specific device.

    Args:
        device_eui: The device EUI (16 hex characters)

    Returns:
        Tuple of (success, device data or error message)
    """
    return _make_request("GET", f"/api/devices/{device_eui}")


def create_device(
    device_eui: str,
    name: str,
    application_id: str,
    device_profile_id: str,
    description: str = "",
    skip_fcnt_check: bool = False,
    is_disabled: bool = False,
    join_eui: Optional[str] = None,
) -> Tuple[bool, Any]:
    """
    Create a new device in ChirpStack.

    Args:
        device_eui: The device EUI (16 hex characters, lowercase)
        name: Device name
        application_id: Application ID (UUID)
        device_profile_id: Device profile ID (UUID)
        description: Optional description
        skip_fcnt_check: Skip frame counter validation
        is_disabled: Create device in disabled state
        join_eui: Join EUI for OTAA devices (optional)

    Returns:
        Tuple of (success, result or error message)
    """
    device_data = {
        "device": {
            "devEui": device_eui.lower(),
            "name": name,
            "applicationId": application_id,
            "deviceProfileId": device_profile_id,
            "description": description or name,
            "skipFcntCheck": skip_fcnt_check,
            "isDisabled": is_disabled,
        }
    }

    if join_eui:
        device_data["device"]["joinEui"] = join_eui.lower()

    logger.info(f"Creating device {device_eui} in ChirpStack")

    success, result = _make_request("POST", "/api/devices", json_data=device_data)

    if success:
        logger.info(f"Device {device_eui} created successfully in ChirpStack")
        return True, result

    logger.error(f"Failed to create device {device_eui}: {result}")
    return False, result


def update_device(
    device_eui: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_disabled: Optional[bool] = None,
    skip_fcnt_check: Optional[bool] = None,
) -> Tuple[bool, Any]:
    """
    Update an existing device in ChirpStack.

    Args:
        device_eui: The device EUI (16 hex characters)
        name: New device name (optional)
        description: New description (optional)
        is_disabled: Disable/enable device (optional)
        skip_fcnt_check: Skip frame counter check (optional)

    Returns:
        Tuple of (success, result or error message)
    """
    # First get the current device data
    success, current = get_device(device_eui)
    if not success:
        return False, f"Device not found: {current}"

    device_data = current.get("device", {})

    # Update only provided fields
    if name is not None:
        device_data["name"] = name
    if description is not None:
        device_data["description"] = description
    if is_disabled is not None:
        device_data["isDisabled"] = is_disabled
    if skip_fcnt_check is not None:
        device_data["skipFcntCheck"] = skip_fcnt_check

    return _make_request(
        "PUT",
        f"/api/devices/{device_eui}",
        json_data={"device": device_data},
    )


def delete_device(device_eui: str) -> Tuple[bool, str]:
    """
    Delete a device from ChirpStack.

    Args:
        device_eui: The device EUI (16 hex characters)

    Returns:
        Tuple of (success, message)
    """
    logger.info(f"Deleting device {device_eui} from ChirpStack")

    success, result = _make_request("DELETE", f"/api/devices/{device_eui}")

    if success:
        logger.info(f"Device {device_eui} deleted from ChirpStack")
        return True, "Device deleted successfully"

    return False, result


def set_device_keys(
    device_eui: str,
    app_key: str,
    nwk_key: Optional[str] = None,
) -> Tuple[bool, Any]:
    """
    Set OTAA keys for a device.

    Args:
        device_eui: The device EUI
        app_key: Application key (32 hex characters)
        nwk_key: Network key for LoRaWAN 1.1 (optional, defaults to app_key)

    Returns:
        Tuple of (success, result or error message)
    """
    keys_data = {
        "deviceKeys": {
            "devEui": device_eui.lower(),
            "nwkKey": (nwk_key or app_key).lower(),
            "appKey": app_key.lower(),
        }
    }

    logger.info(f"Setting OTAA keys for device {device_eui}")

    return _make_request(
        "POST",
        f"/api/devices/{device_eui}/keys",
        json_data=keys_data,
    )


def get_device_keys(device_eui: str) -> Tuple[bool, Any]:
    """Get OTAA keys for a device."""
    return _make_request("GET", f"/api/devices/{device_eui}/keys")


# =============================================================================
# GATEWAY MANAGEMENT
# =============================================================================

def list_gateways(
    limit: int = 100,
    offset: int = 0,
    tenant_id: Optional[str] = None,
) -> Tuple[bool, Any]:
    """
    List gateways in ChirpStack.

    Args:
        limit: Maximum number of gateways to return
        offset: Offset for pagination
        tenant_id: Filter by tenant (optional)

    Returns:
        Tuple of (success, list of gateways or error message)
    """
    params = {"limit": limit, "offset": offset}
    if tenant_id:
        params["tenantId"] = tenant_id

    success, result = _make_request("GET", "/api/gateways", params=params)

    if success:
        return True, result.get("result", [])
    return False, result


def get_gateway(gateway_id: str) -> Tuple[bool, Any]:
    """
    Get details of a specific gateway.

    Args:
        gateway_id: The gateway ID (16 hex characters)

    Returns:
        Tuple of (success, gateway data or error message)
    """
    return _make_request("GET", f"/api/gateways/{gateway_id}")


def create_gateway(
    gateway_id: str,
    name: str,
    tenant_id: str,
    description: str = "",
    location_latitude: Optional[float] = None,
    location_longitude: Optional[float] = None,
    location_altitude: Optional[float] = None,
    stats_interval_secs: int = 30,
) -> Tuple[bool, Any]:
    """
    Create a new gateway in ChirpStack.

    Args:
        gateway_id: The gateway ID/EUI (16 hex characters, lowercase)
        name: Gateway name
        tenant_id: Tenant ID (UUID)
        description: Optional description
        location_latitude: GPS latitude (optional)
        location_longitude: GPS longitude (optional)
        location_altitude: Altitude in meters (optional)
        stats_interval_secs: Stats reporting interval

    Returns:
        Tuple of (success, result or error message)
    """
    gateway_data = {
        "gateway": {
            "gatewayId": gateway_id.lower(),
            "name": name,
            "tenantId": tenant_id,
            "description": description or name,
            "statsInterval": stats_interval_secs,
        }
    }

    # Add location if provided
    if location_latitude is not None and location_longitude is not None:
        gateway_data["gateway"]["location"] = {
            "latitude": location_latitude,
            "longitude": location_longitude,
            "altitude": location_altitude or 0,
        }

    logger.info(f"Creating gateway {gateway_id} in ChirpStack")

    success, result = _make_request("POST", "/api/gateways", json_data=gateway_data)

    if success:
        logger.info(f"Gateway {gateway_id} created successfully in ChirpStack")
        return True, result

    logger.error(f"Failed to create gateway {gateway_id}: {result}")
    return False, result


def update_gateway(
    gateway_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    location_latitude: Optional[float] = None,
    location_longitude: Optional[float] = None,
    location_altitude: Optional[float] = None,
) -> Tuple[bool, Any]:
    """
    Update an existing gateway in ChirpStack.

    Args:
        gateway_id: The gateway ID (16 hex characters)
        name: New gateway name (optional)
        description: New description (optional)
        location_*: New location coordinates (optional)

    Returns:
        Tuple of (success, result or error message)
    """
    # First get the current gateway data
    success, current = get_gateway(gateway_id)
    if not success:
        return False, f"Gateway not found: {current}"

    gateway_data = current.get("gateway", {})

    # Update only provided fields
    if name is not None:
        gateway_data["name"] = name
    if description is not None:
        gateway_data["description"] = description

    # Update location if any coordinate provided
    if any(x is not None for x in [location_latitude, location_longitude, location_altitude]):
        location = gateway_data.get("location", {})
        if location_latitude is not None:
            location["latitude"] = location_latitude
        if location_longitude is not None:
            location["longitude"] = location_longitude
        if location_altitude is not None:
            location["altitude"] = location_altitude
        gateway_data["location"] = location

    return _make_request(
        "PUT",
        f"/api/gateways/{gateway_id}",
        json_data={"gateway": gateway_data},
    )


def delete_gateway(gateway_id: str) -> Tuple[bool, str]:
    """
    Delete a gateway from ChirpStack.

    Args:
        gateway_id: The gateway ID (16 hex characters)

    Returns:
        Tuple of (success, message)
    """
    logger.info(f"Deleting gateway {gateway_id} from ChirpStack")

    success, result = _make_request("DELETE", f"/api/gateways/{gateway_id}")

    if success:
        logger.info(f"Gateway {gateway_id} deleted from ChirpStack")
        return True, "Gateway deleted successfully"

    return False, result


# =============================================================================
# TENANT MANAGEMENT
# =============================================================================

def list_tenants(limit: int = 100) -> Tuple[bool, Any]:
    """
    List all tenants in ChirpStack.

    Returns:
        Tuple of (success, list of tenants or error message)
    """
    success, result = _make_request(
        "GET",
        "/api/tenants",
        params={"limit": limit},
    )

    if success:
        return True, result.get("result", [])
    return False, result


def get_tenant(tenant_id: str) -> Tuple[bool, Any]:
    """Get details of a specific tenant."""
    return _make_request("GET", f"/api/tenants/{tenant_id}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def test_connection() -> Tuple[bool, str]:
    """
    Test the connection to ChirpStack API.

    Returns:
        Tuple of (success, message)
    """
    config = get_config()

    if not config["api_key"]:
        return False, "ChirpStack API key not configured"

    # Try to list applications as a simple test
    success, result = list_applications(limit=1)

    if success:
        return True, "ChirpStack connection successful"

    return False, f"ChirpStack connection failed: {result}"


def get_device_with_status(device_eui: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Get device details with connection status information.

    Returns device info plus last seen time and online status.
    """
    success, result = get_device(device_eui)

    if not success:
        return False, result

    device_info = result.get("device", {})
    last_seen = result.get("lastSeenAt")

    return True, {
        "device": device_info,
        "lastSeenAt": last_seen,
        "deviceStatus": result.get("deviceStatus", {}),
        "classEnabled": result.get("classEnabled", "CLASS_A"),
    }
