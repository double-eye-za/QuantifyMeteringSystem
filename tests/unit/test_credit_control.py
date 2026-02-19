"""
Tests for credit control tasks (disconnect/reconnect).

These tests verify the feature flag gating logic. They do NOT test
actual relay commands (that requires a live ChirpStack + physical meters).

We call the _run_* helper functions directly to bypass Celery task
registry and proxy issues in the test environment.
"""
from __future__ import annotations


def test_disconnect_returns_dry_run_when_flag_disabled(app):
    """With feature flag off, disconnect task should return dry_run=True."""
    with app.app_context():
        from app.services.system_settings import save_setting
        save_setting("feature_credit_control", "false", "boolean", "features", 1)

        from app.tasks.prepaid_disconnect_tasks import _run_disconnect
        result = _run_disconnect()
        assert result["dry_run"] is True
        assert result["credit_control_active"] is False
        assert result["status"] == "success"


def test_disconnect_reports_credit_control_active_when_flag_enabled(app):
    """With feature flag on, disconnect task should report credit_control_active=True."""
    with app.app_context():
        from app.services.system_settings import save_setting
        save_setting("feature_credit_control", "true", "boolean", "features", 1)

        from app.tasks.prepaid_disconnect_tasks import _run_disconnect
        result = _run_disconnect()
        assert result["credit_control_active"] is True
        assert result["dry_run"] is False
        assert result["status"] == "success"
        # No meters to process in test DB, so counts should be 0
        assert result["meters_processed"] == 0


def test_reconnect_returns_dry_run_when_flag_disabled(app):
    """With feature flag off, reconnect task should return dry_run=True."""
    with app.app_context():
        from app.services.system_settings import save_setting
        save_setting("feature_credit_control", "false", "boolean", "features", 1)

        from app.tasks.prepaid_disconnect_tasks import _run_reconnect
        result = _run_reconnect()
        assert result["dry_run"] is True
        assert result["credit_control_active"] is False
        assert result["status"] == "success"


def test_reconnect_reports_credit_control_active_when_flag_enabled(app):
    """With feature flag on, reconnect task should report credit_control_active=True."""
    with app.app_context():
        from app.services.system_settings import save_setting
        save_setting("feature_credit_control", "true", "boolean", "features", 1)

        from app.tasks.prepaid_disconnect_tasks import _run_reconnect
        result = _run_reconnect()
        assert result["credit_control_active"] is True
        assert result["dry_run"] is False
        assert result["status"] == "success"
        assert result["meters_processed"] == 0


def test_zero_balance_report_works(app):
    """Zero balance report task should return successfully."""
    with app.app_context():
        from app.tasks.prepaid_disconnect_tasks import _run_report
        result = _run_report()
        assert result["status"] == "success"
        assert result["total_meters"] == 0  # No meters in test DB
