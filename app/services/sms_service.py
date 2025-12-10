"""SMS service for sending messages via Clickatell."""
from __future__ import annotations

import os
import logging
from typing import Tuple, Optional

import requests

logger = logging.getLogger(__name__)

# Clickatell API configuration
CLICKATELL_API_URL = "https://platform.clickatell.com/messages"


def get_clickatell_api_key() -> Optional[str]:
    """
    Get the Clickatell API key from environment variable.

    Returns:
        API key string or None if not configured
    """
    return os.getenv("CLICKATELL_API_KEY")


def send_sms(phone_number: str, message: str) -> Tuple[bool, str]:
    """
    Send an SMS message via Clickatell.

    Args:
        phone_number: Recipient phone number in E.164 format (+27xxxxxxxxx)
        message: Message content to send

    Returns:
        Tuple of (success: bool, message: str)
        On success: (True, "SMS sent successfully")
        On failure: (False, "Error description")

    Example:
        >>> success, result = send_sms("+27821234567", "Hello!")
        >>> if success:
        ...     print("SMS sent!")
    """
    api_key = get_clickatell_api_key()

    if not api_key:
        logger.warning("Clickatell API key not configured")
        return False, "SMS service not configured (missing API key)"

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "content": message,
        "to": [phone_number],
    }

    try:
        response = requests.post(
            CLICKATELL_API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code in (200, 201, 202):
            logger.info(f"SMS sent successfully to {phone_number}")
            return True, "SMS sent successfully"

        # Handle error responses
        error_message = f"Clickatell API error: {response.status_code}"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_message = f"Clickatell error: {error_data['error']}"
            elif "errorMessage" in error_data:
                error_message = f"Clickatell error: {error_data['errorMessage']}"
        except (ValueError, KeyError):
            error_message = f"Clickatell API error: {response.status_code} - {response.text}"

        logger.error(f"Failed to send SMS to {phone_number}: {error_message}")
        return False, error_message

    except requests.exceptions.Timeout:
        logger.error(f"SMS request timed out for {phone_number}")
        return False, "SMS request timed out"

    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to Clickatell API for {phone_number}")
        return False, "Failed to connect to SMS service"

    except requests.exceptions.RequestException as e:
        logger.error(f"SMS request failed for {phone_number}: {str(e)}")
        return False, f"SMS request failed: {str(e)}"


def send_welcome_sms(
    phone_number: str,
    temp_password: str,
    estate_name: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Send a welcome SMS with temporary password to a new mobile user.

    Args:
        phone_number: Recipient phone number in E.164 format (+27xxxxxxxxx)
        temp_password: The temporary password generated for the user
        estate_name: Name of the estate (optional, for personalized message)

    Returns:
        Tuple of (success: bool, message: str)

    Example:
        >>> success, result = send_welcome_sms("+27821234567", "Abc12345", "Sunset Estate")
        >>> if success:
        ...     print("Welcome SMS sent!")
    """
    if estate_name:
        message = (
            f"Welcome to {estate_name}! "
            f"Download the Quantify app and login with "
            f"phone: {phone_number} password: {temp_password}"
        )
    else:
        message = (
            f"Welcome! Download the Quantify app and login with "
            f"phone: {phone_number} password: {temp_password}"
        )

    return send_sms(phone_number, message)
