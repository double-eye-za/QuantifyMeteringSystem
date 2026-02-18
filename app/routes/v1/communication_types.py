"""
Communication Type management routes
"""
from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required
from . import api_v1
from app.utils.decorators import requires_permission
from app.services import communication_types as svc
from app.utils.audit import log_action


@api_v1.route("/communication-types", methods=["GET"])
@login_required
@requires_permission("settings.view")
def communication_types_page():
    """Communication types management page"""
    communication_types = svc.list_communication_types(active_only=False)
    return render_template(
        "settings/communication-types.html",
        communication_types=communication_types
    )


@api_v1.route("/api/communication-types", methods=["GET"])
@login_required
@requires_permission("settings.view")
def get_communication_types():
    """Get all communication types (JSON API)"""
    active_only = request.args.get("active_only", "true").lower() == "true"
    communication_types = svc.list_communication_types(active_only=active_only)
    return jsonify([ct.to_dict() for ct in communication_types])


@api_v1.route("/api/communication-types/<int:comm_type_id>", methods=["GET"])
@login_required
@requires_permission("settings.view")
def get_communication_type(comm_type_id):
    """Get a specific communication type"""
    comm_type = svc.get_communication_type_by_id(comm_type_id)
    if not comm_type:
        return jsonify({"error": "Communication type not found"}), 404
    return jsonify(comm_type.to_dict())


@api_v1.route("/api/communication-types", methods=["POST"])
@login_required
@requires_permission("settings.edit")
def create_communication_type():
    """Create a new communication type"""
    data = request.get_json() or request.form.to_dict()

    # Validate required fields
    if not data.get("code") or not data.get("name"):
        return jsonify({"error": "Code and name are required"}), 400

    # Check if code already exists
    existing = svc.get_communication_type_by_code(data.get("code"))
    if existing:
        return jsonify({"error": "Communication type with this code already exists"}), 400

    try:
        comm_type = svc.create_communication_type(data)
        log_action("create", "communication_type", comm_type.id, f"Created communication type: {comm_type.name}")

        if request.is_json:
            return jsonify(comm_type.to_dict()), 201
        else:
            flash(f"Communication type '{comm_type.name}' created successfully", "success")
            return redirect(url_for("api_v1.communication_types_page"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.route("/api/communication-types/<int:comm_type_id>", methods=["PUT", "PATCH"])
@login_required
@requires_permission("settings.edit")
def update_communication_type(comm_type_id):
    """Update an existing communication type"""
    data = request.get_json() or request.form.to_dict()

    comm_type = svc.update_communication_type(comm_type_id, data)
    if not comm_type:
        return jsonify({"error": "Communication type not found"}), 404

    log_action("update", "communication_type", comm_type.id, f"Updated communication type: {comm_type.name}")

    if request.is_json:
        return jsonify(comm_type.to_dict())
    else:
        flash(f"Communication type '{comm_type.name}' updated successfully", "success")
        return redirect(url_for("api_v1.communication_types_page"))


@api_v1.route("/api/communication-types/<int:comm_type_id>", methods=["DELETE"])
@login_required
@requires_permission("settings.edit")
def delete_communication_type(comm_type_id):
    """Delete (deactivate) a communication type"""
    comm_type = svc.get_communication_type_by_id(comm_type_id)
    if not comm_type:
        return jsonify({"error": "Communication type not found"}), 404

    success = svc.delete_communication_type(comm_type_id)
    if success:
        log_action("delete", "communication_type", comm_type_id, f"Deactivated communication type: {comm_type.name}")
        return jsonify({"message": "Communication type deactivated successfully"})
    else:
        return jsonify({"error": "Failed to deactivate communication type"}), 500
