"""SMS service for sending messages via SMSPortal.com REST API."""
from __future__ import annotations

import os
import base64
import logging
from typing import Tuple, Optional

import requests

logger = logging.getLogger(__name__)

# SMSPortal API configuration
SMSPORTAL_API_URL = "https://rest.smsportal.com/v3/BulkMessages"


def get_smsportal_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Get the SMSPortal API credentials from environment variables.

    Returns:
        Tuple of (client_id, api_secret) or (None, None) if not configured
    """
    client_id = os.getenv("SMSPORTAL_CLIENT_ID")
    api_secret = os.getenv("SMSPORTAL_API_SECRET")
    return client_id, api_secret


def get_auth_header() -> Optional[str]:
    """
    Generate the Basic Authentication header for SMSPortal API.

    Returns:
        Base64 encoded authorization string or None if credentials not configured
    """
    client_id, api_secret = get_smsportal_credentials()

    if not client_id or not api_secret:
        return None

    # Encode credentials as Base64: "ClientID:APISecret"
    credentials = f"{client_id}:{api_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def send_sms(phone_number: str, message: str, test_mode: bool = False) -> Tuple[bool, str]:
    """
    Send an SMS message via SMSPortal REST API.

    Args:
        phone_number: Recipient phone number in E.164 format (+27xxxxxxxxx)
        message: Message content to send
        test_mode: If True, validates request without actually sending SMS

    Returns:
        Tuple of (success: bool, message: str)
        On success: (True, "SMS sent successfully")
        On failure: (False, "Error description")

    Example:
        >>> success, result = send_sms("+27821234567", "Hello!")
        >>> if success:
        ...     print("SMS sent!")
    """
    print(f"[SMS_SERVICE] send_sms called - phone: {phone_number}, test_mode: {test_mode}")

    auth_header = get_auth_header()

    if not auth_header:
        print("[SMS_SERVICE] ERROR: SMSPortal API credentials not configured")
        logger.warning("SMSPortal API credentials not configured")
        return False, "SMS service not configured (missing SMSPORTAL_CLIENT_ID or SMSPORTAL_API_SECRET)"

    print("[SMS_SERVICE] Auth header obtained successfully")

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # SMSPortal requires E.164 format, ensure phone has + prefix
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    payload = {
        "sendOptions": {
            "testMode": test_mode,
        },
        "messages": [
            {
                "destination": phone_number,
                "content": message,
            }
        ],
    }

    try:
        print(f"[SMS_SERVICE] Sending request to SMSPortal API...")
        response = requests.post(
            SMSPORTAL_API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )
        print(f"[SMS_SERVICE] Response status: {response.status_code}")
        print(f"[SMS_SERVICE] Response body: {response.text[:500] if response.text else 'empty'}")

        if response.status_code in (200, 201, 202):
            print(f"[SMS_SERVICE] SUCCESS - SMS sent to {phone_number}")
            logger.info(f"SMS sent successfully to {phone_number}")
            return True, "SMS sent successfully"

        # Handle error responses
        error_message = f"SMSPortal API error: {response.status_code}"
        try:
            error_data = response.json()
            if "message" in error_data:
                error_message = f"SMSPortal error: {error_data['message']}"
            elif "error" in error_data:
                error_message = f"SMSPortal error: {error_data['error']}"
            elif "errors" in error_data and isinstance(error_data["errors"], list):
                errors = [e.get("message", str(e)) for e in error_data["errors"]]
                error_message = f"SMSPortal error: {'; '.join(errors)}"
        except (ValueError, KeyError):
            error_message = f"SMSPortal API error: {response.status_code} - {response.text}"

        logger.error(f"Failed to send SMS to {phone_number}: {error_message}")
        return False, error_message

    except requests.exceptions.Timeout:
        logger.error(f"SMS request timed out for {phone_number}")
        return False, "SMS request timed out"

    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to SMSPortal API for {phone_number}")
        return False, "Failed to connect to SMS service"

    except requests.exceptions.RequestException as e:
        logger.error(f"SMS request failed for {phone_number}: {str(e)}")
        return False, f"SMS request failed: {str(e)}"


def send_welcome_sms(
    phone_number: str,
    temp_password: str,
    estate_name: Optional[str] = None,
    test_mode: bool = False,
) -> Tuple[bool, str]:
    """
    Send a welcome SMS with temporary password to a new mobile user.

    Args:
        phone_number: Recipient phone number in E.164 format (+27xxxxxxxxx)
        temp_password: The temporary password generated for the user
        estate_name: Name of the estate (optional, for personalized message)
        test_mode: If True, validates request without actually sending SMS

    Returns:
        Tuple of (success: bool, message: str)

    Example:
        >>> success, result = send_welcome_sms("+27821234567", "Abc12345", "Sunset Estate")
        >>> if success:
        ...     print("Welcome SMS sent!")
    """
    print(f"[SMS_SERVICE] send_welcome_sms called - phone: {phone_number}, estate: {estate_name}")

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

    return send_sms(phone_number, message, test_mode=test_mode)


# Legacy function name for backwards compatibility
def get_clickatell_api_key() -> Optional[str]:
    """
    Legacy function - SMSPortal uses Client ID and API Secret instead.
    Kept for backwards compatibility - returns None to indicate migration needed.
    """
    logger.warning("get_clickatell_api_key() is deprecated. Use get_smsportal_credentials() instead.")
    return None
