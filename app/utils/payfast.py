"""PayFast payment gateway utilities.

Provides signature generation for outbound payment forms, ITN signature
validation for inbound notifications, and server-to-server verification.
Uses only Python stdlib — no external PayFast library needed.
"""
from __future__ import annotations

import hashlib
import urllib.parse
import urllib.request
from typing import Dict, Optional


def generate_signature(data: Dict[str, str], passphrase: Optional[str] = None) -> str:
    """Generate an MD5 signature for a PayFast payment form.

    Args:
        data: Ordered dict of form fields (merchant_id, merchant_key, etc.).
              Insertion order is preserved and used for the signature string.
        passphrase: Merchant passphrase. Appended to the param string if provided.

    Returns:
        Lowercase hex MD5 digest.
    """
    # Build param string from data in insertion order
    params = []
    for key, value in data.items():
        if value is not None and value != '':
            params.append(f"{key}={urllib.parse.quote_plus(str(value))}")

    param_string = '&'.join(params)

    if passphrase:
        param_string += f"&passphrase={urllib.parse.quote_plus(passphrase)}"

    return hashlib.md5(param_string.encode()).hexdigest()


def validate_itn_signature(post_data: Dict[str, str], passphrase: Optional[str] = None) -> bool:
    """Validate the signature on an incoming PayFast ITN notification.

    Args:
        post_data: The full POST data dict from PayFast's ITN callback.
        passphrase: Merchant passphrase used to verify the signature.

    Returns:
        True if the computed signature matches the received signature.
    """
    received_signature = post_data.get('signature', '')
    if not received_signature:
        return False

    # Build param string from all fields except 'signature', in received order
    params = []
    for key, value in post_data.items():
        if key == 'signature':
            continue
        if value is not None and value != '':
            params.append(f"{key}={urllib.parse.quote_plus(str(value))}")

    param_string = '&'.join(params)

    if passphrase:
        param_string += f"&passphrase={urllib.parse.quote_plus(passphrase)}"

    computed = hashlib.md5(param_string.encode()).hexdigest()
    return computed == received_signature


def verify_itn_with_payfast(post_data: Dict[str, str], validate_url: str) -> bool:
    """Server-to-server verification of an ITN notification with PayFast.

    Posts the ITN data back to PayFast's validation endpoint and checks
    for a 'VALID' response.

    Args:
        post_data: The full POST data dict from PayFast's ITN callback.
        validate_url: PayFast's validation URL (sandbox or production).

    Returns:
        True if PayFast confirms the notification is valid.
    """
    encoded_data = urllib.parse.urlencode(post_data).encode()

    try:
        req = urllib.request.Request(validate_url, data=encoded_data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode().strip()
            return result == 'VALID'
    except Exception:
        return False
