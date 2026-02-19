from __future__ import annotations


def test_flag_defaults_to_false(app):
    """Unset flags should return False."""
    with app.app_context():
        from app.utils.feature_flags import is_feature_enabled

        assert is_feature_enabled("credit_control") is False
        assert is_feature_enabled("nonexistent_flag") is False


def test_flag_enabled_when_set(app):
    """Flags return True when set to 'true' in system_settings."""
    with app.app_context():
        from app.services.system_settings import save_setting
        from app.utils.feature_flags import is_feature_enabled

        save_setting("feature_credit_control", "true", "boolean", "features", 1)
        assert is_feature_enabled("credit_control") is True


def test_flag_disabled_when_set_false(app):
    """Flags return False when explicitly set to 'false'."""
    with app.app_context():
        from app.services.system_settings import save_setting
        from app.utils.feature_flags import is_feature_enabled

        save_setting("feature_credit_control", "false", "boolean", "features", 1)
        assert is_feature_enabled("credit_control") is False
