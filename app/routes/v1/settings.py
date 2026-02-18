from __future__ import annotations

from flask import render_template, request, jsonify
from flask_login import login_required, current_user

from ...services.system_settings import (
    list_settings_as_dict,
    save_settings as svc_save_settings,
)
from ...utils.audit import log_action
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.route("/settings", methods=["GET"])
@login_required
@requires_permission("settings.view")
def settings_page():
    return render_template("settings/settings.html")


@api_v1.route("/api/settings", methods=["GET"])
@login_required
@requires_permission("settings.view")
def get_settings():
    """Get all system settings"""
    try:
        settings = list_settings_as_dict()
        return jsonify({"settings": settings})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.route("/settings/general", methods=["POST"])
@login_required
@requires_permission("settings.edit")
def save_general_settings():
    """Save general settings"""
    try:
        data = request.get_json()

        settings_to_save = [
            ("org_name", data.get("org_name", "Quantify Metering"), "string"),
            (
                "contact_email",
                data.get("contact_email", "admin@quantifymetering.com"),
                "string",
            ),
            ("default_language", data.get("default_language", "English"), "string"),
            ("timezone", data.get("timezone", "Africa/Johannesburg (GMT+2)"), "string"),
            ("date_format", data.get("date_format", "YYYY-MM-DD"), "string"),
            ("session_timeout", str(data.get("session_timeout", 15)), "number"),
        ]

        svc_save_settings(settings_to_save, "general", current_user.id)

        log_action(
            "settings.general.update",
            entity_type="system_setting",
            entity_id=None,
            new_values={"settings_category": "general", "settings_data": data},
        )

        return jsonify({"message": "General settings saved successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.route("/settings/security", methods=["POST"])
@login_required
@requires_permission("settings.edit")
def save_security_settings():
    """Save security settings"""
    try:
        data = request.get_json()

        settings_to_save = [
            ("min_password_length", str(data.get("min_password_length", 8)), "number"),
            (
                "require_uppercase",
                str(data.get("require_uppercase", False)).lower(),
                "boolean",
            ),
            (
                "require_numbers",
                str(data.get("require_numbers", False)).lower(),
                "boolean",
            ),
            (
                "require_special_chars",
                str(data.get("require_special_chars", False)).lower(),
                "boolean",
            ),
            (
                "enable_2fa",
                str(data.get("enable_2fa", False)).lower(),
                "boolean",
            ),
            (
                "account_lockout",
                str(data.get("account_lockout", False)).lower(),
                "boolean",
            ),
            ("allowed_ips", data.get("allowed_ips", ""), "string"),
        ]

        svc_save_settings(settings_to_save, "security", current_user.id)

        log_action(
            "settings.security.update",
            entity_type="system_setting",
            entity_id=None,
            new_values={"settings_category": "security", "settings_data": data},
        )

        return jsonify({"message": "Security settings saved successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.route("/settings/notifications", methods=["POST"])
@login_required
@requires_permission("settings.edit")
def save_notification_settings():
    """Save notification settings"""
    try:
        data = request.get_json()

        settings_to_save = [
            ("sms_provider", data.get("sms_provider", "twilio"), "string"),
            ("emergency_contact", data.get("emergency_contact", ""), "string"),
            (
                "system_alerts",
                str(data.get("system_alerts", False)).lower(),
                "boolean",
            ),
            (
                "security_alerts",
                str(data.get("security_alerts", False)).lower(),
                "boolean",
            ),
            (
                "system_updates",
                str(data.get("system_updates", False)).lower(),
                "boolean",
            ),
        ]

        svc_save_settings(settings_to_save, "notifications", current_user.id)

        log_action(
            "settings.notifications.update",
            entity_type="system_setting",
            entity_id=None,
            new_values={"settings_category": "notifications", "settings_data": data},
        )

        return jsonify({"message": "Notification settings saved successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
