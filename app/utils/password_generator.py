"""Password generation and validation utilities for mobile users."""
import random
import string
import re
from typing import Tuple


def generate_temporary_password(length: int = 8) -> str:
    """
    Generate a temporary password that meets security requirements.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number

    Args:
        length: Length of password (default 8, minimum 8)

    Returns:
        Generated password as string

    Example:
        >>> pwd = generate_temporary_password()
        >>> len(pwd) >= 8
        True
        >>> validate_password_strength(pwd)[0]
        True
    """
    if length < 8:
        length = 8

    # Ensure we have at least one of each required character type
    password_chars = [
        random.choice(string.ascii_uppercase),  # At least 1 uppercase
        random.choice(string.ascii_lowercase),  # At least 1 lowercase
        random.choice(string.digits),           # At least 1 digit
    ]

    # Fill the rest with random mix
    remaining_length = length - len(password_chars)
    all_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

    password_chars.extend(random.choices(all_chars, k=remaining_length))

    # Shuffle to avoid predictable pattern
    random.shuffle(password_chars)

    return ''.join(password_chars)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate that a password meets the required strength criteria.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string

    Example:
        >>> validate_password_strength("Abc12345")
        (True, '')
        >>> validate_password_strength("abc123")
        (False, 'Password must be at least 8 characters long')
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    return True, ""


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number format.

    Accepts formats:
    - +27xxxxxxxxx (E.164 format)
    - 0xxxxxxxxx (South African format)
    - Removes spaces and dashes

    Args:
        phone: Phone number to validate

    Returns:
        Tuple of (is_valid: bool, normalized_phone: str)
        If invalid, normalized_phone is empty string

    Example:
        >>> validate_phone_number("+27821234567")
        (True, '+27821234567')
        >>> validate_phone_number("082 123 4567")
        (True, '+27821234567')
    """
    if not phone:
        return False, ""

    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)

    # South African mobile number starting with 0
    if re.match(r'^0\d{9}$', cleaned):
        # Convert 0821234567 to +27821234567
        return True, f"+27{cleaned[1:]}"

    # Already in E.164 format
    if re.match(r'^\+27\d{9}$', cleaned):
        return True, cleaned

    # Invalid format
    return False, ""


def generate_username_from_name(first_name: str, last_name: str) -> str:
    """
    Generate a username from first and last name.

    Format: firstname.lastname (lowercase, no spaces)

    Args:
        first_name: User's first name
        last_name: User's last name

    Returns:
        Generated username

    Example:
        >>> generate_username_from_name("John", "Smith")
        'john.smith'
    """
    first = re.sub(r'[^a-zA-Z]', '', first_name).lower()
    last = re.sub(r'[^a-zA-Z]', '', last_name).lower()
    return f"{first}.{last}"
