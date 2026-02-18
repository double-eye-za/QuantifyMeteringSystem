from __future__ import annotations

import re
from typing import Tuple, Optional
from ..models import SystemSetting


def validate_password_policy(password: str):
    """
    Validate password against system security settings with defaults.
    Returns (is_valid, error_message)
    """
    try:
        # Get password policy settings with defaults
        settings = SystemSetting.get_all_settings()

        min_length = settings.get("min_password_length", 8)
        require_uppercase = settings.get("require_uppercase", False)
        require_numbers = settings.get("require_numbers", False)
        require_special_chars = settings.get("require_special_chars", False)

        # Check minimum length
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters long"

        # Check for uppercase letters
        if require_uppercase and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        # Check for numbers
        if require_numbers and not re.search(r"[0-9]", password):
            return False, "Password must contain at least one number"

        # Check for special characters
        if require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, ""

    except Exception as e:
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        return True, ""


def get_password_requirements():
    """Get password requirements for display to users with defaults"""
    try:
        settings = SystemSetting.get_all_settings()

        return {
            "min_length": settings.get("min_password_length", 8),
            "require_uppercase": settings.get("require_uppercase", False),
            "require_numbers": settings.get("require_numbers", False),
            "require_special_chars": settings.get("require_special_chars", False),
        }
    except Exception:
        return {
            "min_length": 8,
            "require_uppercase": False,
            "require_numbers": False,
            "require_special_chars": False,
        }
