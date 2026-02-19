"""
Feature flag utility for safe, incremental rollout of new features.

Usage:
    from app.utils.feature_flags import is_feature_enabled

    if is_feature_enabled('credit_control'):
        # new behaviour
    else:
        # existing behaviour (safe default)

All flags default to False (disabled). Enable via SystemSetting:
    setting_key = 'feature_credit_control'
    setting_value = 'true'
    setting_type = 'boolean'
    category = 'features'
"""
from __future__ import annotations

from app.services.system_settings import get_setting


# Registry of known feature flags with descriptions.
# Used by admin UI to show available toggles.
FEATURE_FLAGS = {
    "credit_control": "Enable wallet credit limits and meter disconnect for zero-balance electricity",
}


def is_feature_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        flag_name: Short name without 'feature_' prefix (e.g., 'credit_control')

    Returns:
        True if enabled, False if disabled or not set
    """
    return get_setting(f"feature_{flag_name}", default_value=False) is True
