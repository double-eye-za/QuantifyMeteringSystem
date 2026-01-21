"""ChirpStack API service for sending LoRaWAN downlink commands."""
from __future__ import annotations

import base64
import logging
from typing import Tuple, Optional, Dict, Any

import requests
from flask import current_app

logger = logging.getLogger(__name__)


# Pre-calculated Modbus commands for SDM320C relay control
# Format: Slave(01) + Function(05) + Address(0000) + Value + CRC16
RELAY_COMMANDS = {
    "off": bytes.fromhex("010500000000CDCA"),  # Relay OFF - disconnect power
    "on": bytes.fromhex("0105000000FF008C3A".replace("00FF00", "FF00")),  # Relay ON - restore power
}

# Fix the ON command (was malformed above)
RELAY_COMMANDS["on"] = bytes.fromhex("0105000000FF8C3A".replace("0000FF", "FF00"))
# Actually let's just hardcode both correctly:
RELAY_COMMANDS = {
    "off": bytes.fromhex("010500000000CDCA"),  # 01 05 00 00 00 00 CD CA
    "on": bytes.fromhex("0105000000FF008C3A".replace("00FF00", "FF00")),
}
# Simpler - just define the raw bytes:
RELAY_OFF_COMMAND = bytes([0x01, 0x05, 0x00, 0x00, 0x00, 0x00, 0xCD, 0xCA])
RELAY_ON_COMMAND = bytes([0x01, 0x05, 0x00, 0x00, 0xFF, 0x00, 0x8C, 0x3A])


def get_config() -> Dict[str, Any]:
    """Get ChirpStack configuration from Flask app config."""
    return {
        "api_url": current_app.config.get("CHIRPSTACK_API_URL", "http://localhost:8080"),
        "api_key": current_app.config.get("CHIRPSTACK_API_KEY", ""),
        "passthrough_port": current_app.config.get("CHIRPSTACK_PASSTHROUGH_PORT", 5),
    }


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

    if not config["api_key"]:
        logger.warning("ChirpStack API key not configured")
        return False, "ChirpStack API key not configured"

    if port is None:
        port = config["passthrough_port"]

    # Encode payload as base64
    payload_b64 = base64.b64encode(payload).decode("utf-8")

    # ChirpStack v4 API endpoint
    url = f"{config['api_url']}/api/devices/{device_eui}/queue"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    body = {
        "queueItem": {
            "confirmed": confirmed,
            "data": payload_b64,
            "fPort": port,
        }
    }

    try:
        logger.info(f"Sending downlink to {device_eui} on port {port}: {payload.hex()}")

        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=30,
        )

        if response.status_code in (200, 201):
            logger.info(f"Downlink queued successfully for {device_eui}")
            return True, "Downlink queued successfully"

        # Handle error responses
        error_message = f"ChirpStack API error: {response.status_code}"
        try:
            error_data = response.json()
            if "message" in error_data:
                error_message = f"ChirpStack error: {error_data['message']}"
            elif "error" in error_data:
                error_message = f"ChirpStack error: {error_data['error']}"
        except (ValueError, KeyError):
            error_message = f"ChirpStack API error: {response.status_code} - {response.text}"

        logger.error(f"Failed to queue downlink for {device_eui}: {error_message}")
        return False, error_message

    except requests.exceptions.Timeout:
        logger.error(f"ChirpStack request timed out for {device_eui}")
        return False, "ChirpStack request timed out"

    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to ChirpStack API for {device_eui}")
        return False, "Failed to connect to ChirpStack"

    except requests.exceptions.RequestException as e:
        logger.error(f"ChirpStack request failed for {device_eui}: {str(e)}")
        return False, f"ChirpStack request failed: {str(e)}"


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

    if action == "off":
        payload = RELAY_OFF_COMMAND
    else:
        payload = RELAY_ON_COMMAND

    logger.info(f"Sending relay {action.upper()} command to {device_eui}")

    return send_downlink(device_eui, payload)


def get_device_queue(device_eui: str) -> Tuple[bool, Any]:
    """
    Get the current downlink queue for a device.

    Args:
        device_eui: The device EUI (16 hex characters)

    Returns:
        Tuple of (success: bool, queue_items or error_message)
    """
    config = get_config()

    if not config["api_key"]:
        return False, "ChirpStack API key not configured"

    url = f"{config['api_url']}/api/devices/{device_eui}/queue"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            return True, data.get("result", [])

        return False, f"ChirpStack API error: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, f"ChirpStack request failed: {str(e)}"
