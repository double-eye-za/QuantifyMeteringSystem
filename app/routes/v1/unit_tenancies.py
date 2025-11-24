from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required, current_user

from ...services.unit_tenancies import (
    get_unit_tenants,
    add_tenant,
    update_tenancy,
    remove_tenant,
    terminate_tenancy,
    set_primary_tenant,
)
from ...services.mobile_users import (
    get_mobile_user_by_person_id,
    create_mobile_user,
)
from ...utils.audit import log_action
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.get("/api/units/<int:unit_id>/tenants")
@login_required
@requires_permission("units.view")
def get_tenants(unit_id: int):
    """Get all tenants for a unit"""
    tenants = get_unit_tenants(unit_id, active_only=False)
    return jsonify({
        "data": [
            {
                "id": t.id,
                "person_id": t.person_id,
                "person_name": t.person.full_name,
                "is_primary_tenant": t.is_primary_tenant,
                "lease_start_date": t.lease_start_date.isoformat() if t.lease_start_date else None,
                "lease_end_date": t.lease_end_date.isoformat() if t.lease_end_date else None,
                "move_in_date": t.move_in_date.isoformat() if t.move_in_date else None,
                "move_out_date": t.move_out_date.isoformat() if t.move_out_date else None,
                "status": t.status,
                "monthly_rent": float(t.monthly_rent) if t.monthly_rent else None,
            }
            for t in tenants
        ]
    })


@api_v1.post("/api/units/<int:unit_id>/tenants")
@login_required
@requires_permission("units.edit")
def add_unit_tenant(unit_id: int):
    """Add a tenant to a unit"""
    payload = request.get_json(force=True) or {}

    required = ["person_id"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    success, result = add_tenant(
        unit_id=unit_id,
        person_id=payload["person_id"],
        is_primary_tenant=payload.get("is_primary_tenant", False),
        lease_start_date=payload.get("lease_start_date"),
        lease_end_date=payload.get("lease_end_date"),
        monthly_rent=payload.get("monthly_rent"),
        deposit_amount=payload.get("deposit_amount"),
        move_in_date=payload.get("move_in_date"),
        status=payload.get("status", "active"),
        notes=payload.get("notes"),
    )

    if not success:
        return jsonify({"error": result.get("message", "Failed to add tenant")}), result.get("code", 400)

    log_action(
        "unit.tenant_added",
        entity_type="unit",
        entity_id=unit_id,
        new_values={"person_id": payload["person_id"]},
    )

    # Auto-create mobile user account if person doesn't have one
    mobile_user_info = None
    existing_mobile_user = get_mobile_user_by_person_id(payload["person_id"])

    if not existing_mobile_user:
        # Create mobile user account (without SMS for now)
        user_success, user_result = create_mobile_user(
            person_id=payload["person_id"],
            send_sms=False
        )

        if user_success:
            mobile_user_info = {
                "mobile_user_created": True,
                "phone_number": user_result["user"].phone_number,
                "temporary_password": user_result["temp_password"],
                "password_must_change": True,
                "message": "Mobile app account created. Please provide the temporary password to the tenant."
            }
        else:
            # Log but don't fail the tenant addition if mobile user creation fails
            mobile_user_info = {
                "mobile_user_created": False,
                "error": user_result.get("message", "Failed to create mobile user account")
            }

    response_data = {
        "message": "Tenant added successfully",
        "data": {
            "id": result.id,
            "person_id": result.person_id,
            "status": result.status,
        }
    }

    if mobile_user_info:
        response_data["mobile_user"] = mobile_user_info

    return jsonify(response_data), 201


@api_v1.delete("/api/units/<int:unit_id>/tenants/<int:person_id>")
@login_required
@requires_permission("units.edit")
def remove_unit_tenant(unit_id: int, person_id: int):
    """Remove a tenant from a unit"""
    success, error = remove_tenant(unit_id, person_id)

    if not success:
        return jsonify({"error": error.get("message", "Failed to remove tenant")}), error.get("code", 400)

    log_action(
        "unit.tenant_removed",
        entity_type="unit",
        entity_id=unit_id,
        new_values={"person_id": person_id},
    )

    return jsonify({"message": "Tenant removed successfully"})


@api_v1.post("/api/units/<int:unit_id>/tenants/<int:person_id>/terminate")
@login_required
@requires_permission("units.edit")
def terminate_unit_tenancy(unit_id: int, person_id: int):
    """Terminate a tenancy (preserves history)"""
    payload = request.get_json(force=True) or {}

    success, result = terminate_tenancy(
        unit_id=unit_id,
        person_id=person_id,
        move_out_date=payload.get("move_out_date"),
        termination_reason=payload.get("termination_reason"),
    )

    if not success:
        return jsonify({"error": result.get("message", "Failed to terminate tenancy")}), result.get("code", 400)

    log_action(
        "unit.tenancy_terminated",
        entity_type="unit",
        entity_id=unit_id,
        new_values={"person_id": person_id},
    )

    return jsonify({"message": "Tenancy terminated successfully"})


@api_v1.post("/api/units/<int:unit_id>/tenants/<int:person_id>/set-primary")
@login_required
@requires_permission("units.edit")
def set_unit_primary_tenant(unit_id: int, person_id: int):
    """Set a person as the primary tenant of a unit"""
    success, result = set_primary_tenant(unit_id, person_id)

    if not success:
        return jsonify({"error": result.get("message", "Failed to set primary tenant")}), result.get("code", 400)

    log_action(
        "unit.primary_tenant_set",
        entity_type="unit",
        entity_id=unit_id,
        new_values={"person_id": person_id},
    )

    return jsonify({"message": "Primary tenant set successfully"})
