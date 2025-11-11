"""
Device Type management routes
"""
from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required
from . import api_v1
from app.utils.decorators import requires_permission
from app.services import device_types as svc
from app.utils.audit import log_action


@api_v1.route("/device-types", methods=["GET"])
@login_required
@requires_permission("settings.view")
def device_types_page():
    """Device types management page"""
    device_types = svc.list_device_types(active_only=False)
    return render_template(
        "settings/device-types.html",
        device_types=device_types
    )


@api_v1.route("/api/device-types", methods=["GET"])
@login_required
@requires_permission("settings.view")
def get_device_types():
    """Get all device types (JSON API)"""
    active_only = request.args.get("active_only", "true").lower() == "true"
    device_types = svc.list_device_types(active_only=active_only)
    return jsonify([dt.to_dict() for dt in device_types])


@api_v1.route("/api/device-types/<int:device_type_id>", methods=["GET"])
@login_required
@requires_permission("settings.view")
def get_device_type(device_type_id):
    """Get a specific device type"""
    device_type = svc.get_device_type_by_id(device_type_id)
    if not device_type:
        return jsonify({"error": "Device type not found"}), 404
    return jsonify(device_type.to_dict())


@api_v1.route("/api/device-types", methods=["POST"])
@login_required
@requires_permission("settings.edit")
def create_device_type():
    """Create a new device type"""
    data = request.get_json() or request.form.to_dict()

    # Validate required fields
    if not data.get("code") or not data.get("name"):
        return jsonify({"error": "Code and name are required"}), 400

    # Check if code already exists
    existing = svc.get_device_type_by_code(data.get("code"))
    if existing:
        return jsonify({"error": "Device type with this code already exists"}), 400

    try:
        device_type = svc.create_device_type(data)
        log_action("create", "device_type", device_type.id, f"Created device type: {device_type.name}")

        if request.is_json:
            return jsonify(device_type.to_dict()), 201
        else:
            flash(f"Device type '{device_type.name}' created successfully", "success")
            return redirect(url_for("api_v1.device_types_page"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.route("/api/device-types/<int:device_type_id>", methods=["PUT", "PATCH"])
@login_required
@requires_permission("settings.edit")
def update_device_type(device_type_id):
    """Update an existing device type"""
    data = request.get_json() or request.form.to_dict()

    device_type = svc.update_device_type(device_type_id, data)
    if not device_type:
        return jsonify({"error": "Device type not found"}), 404

    log_action("update", "device_type", device_type.id, f"Updated device type: {device_type.name}")

    if request.is_json:
        return jsonify(device_type.to_dict())
    else:
        flash(f"Device type '{device_type.name}' updated successfully", "success")
        return redirect(url_for("api_v1.device_types_page"))


@api_v1.route("/api/device-types/<int:device_type_id>", methods=["DELETE"])
@login_required
@requires_permission("settings.edit")
def delete_device_type(device_type_id):
    """Delete (deactivate) a device type"""
    device_type = svc.get_device_type_by_id(device_type_id)
    if not device_type:
        return jsonify({"error": "Device type not found"}), 404

    success = svc.delete_device_type(device_type_id)
    if success:
        log_action("delete", "device_type", device_type_id, f"Deactivated device type: {device_type.name}")
        return jsonify({"message": "Device type deactivated successfully"})
    else:
        return jsonify({"error": "Failed to deactivate device type"}), 500
