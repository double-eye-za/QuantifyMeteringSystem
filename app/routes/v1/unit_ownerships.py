from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required, current_user

from ...services.unit_ownerships import (
    get_unit_owners,
    add_owner,
    update_ownership,
    remove_owner,
    set_primary_owner,
)
from ...services.mobile_users import (
    get_mobile_user_by_person_id,
    create_mobile_user,
)
from ...utils.audit import log_action
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.get("/api/units/<int:unit_id>/owners")
@login_required
@requires_permission("units.view")
def get_owners(unit_id: int):
    """Get all owners for a unit"""
    owners = get_unit_owners(unit_id)
    return jsonify({
        "data": [
            {
                "id": o.id,
                "person_id": o.person_id,
                "person_name": o.person.full_name,
                "ownership_percentage": float(o.ownership_percentage),
                "is_primary_owner": o.is_primary_owner,
                "purchase_date": o.purchase_date.isoformat() if o.purchase_date else None,
                "purchase_price": float(o.purchase_price) if o.purchase_price else None,
            }
            for o in owners
        ]
    })


@api_v1.post("/api/units/<int:unit_id>/owners")
@login_required
@requires_permission("units.edit")
def add_unit_owner(unit_id: int):
    """Add an owner to a unit"""
    payload = request.get_json(force=True) or {}

    required = ["person_id"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    success, result = add_owner(
        unit_id=unit_id,
        person_id=payload["person_id"],
        ownership_percentage=payload.get("ownership_percentage", 100.0),
        is_primary_owner=payload.get("is_primary_owner", False),
        purchase_date=payload.get("purchase_date"),
        purchase_price=payload.get("purchase_price"),
        notes=payload.get("notes"),
    )

    if not success:
        return jsonify({"error": result.get("message", "Failed to add owner")}), result.get("code", 400)

    log_action(
        "unit.owner_added",
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
                "message": "Mobile app account created. Please provide the temporary password to the owner."
            }
        else:
            # Log but don't fail the owner addition if mobile user creation fails
            mobile_user_info = {
                "mobile_user_created": False,
                "error": user_result.get("message", "Failed to create mobile user account")
            }

    response_data = {
        "message": "Owner added successfully",
        "data": {
            "id": result.id,
            "person_id": result.person_id,
            "ownership_percentage": float(result.ownership_percentage),
        }
    }

    if mobile_user_info:
        response_data["mobile_user"] = mobile_user_info

    return jsonify(response_data), 201


@api_v1.delete("/api/units/<int:unit_id>/owners/<int:person_id>")
@login_required
@requires_permission("units.edit")
def remove_unit_owner(unit_id: int, person_id: int):
    """Remove an owner from a unit"""
    success, error = remove_owner(unit_id, person_id)

    if not success:
        return jsonify({"error": error.get("message", "Failed to remove owner")}), error.get("code", 400)

    log_action(
        "unit.owner_removed",
        entity_type="unit",
        entity_id=unit_id,
        new_values={"person_id": person_id},
    )

    return jsonify({"message": "Owner removed successfully"})


@api_v1.post("/api/units/<int:unit_id>/owners/<int:person_id>/set-primary")
@login_required
@requires_permission("units.edit")
def set_unit_primary_owner(unit_id: int, person_id: int):
    """Set a person as the primary owner of a unit"""
    success, result = set_primary_owner(unit_id, person_id)

    if not success:
        return jsonify({"error": result.get("message", "Failed to set primary owner")}), result.get("code", 400)

    log_action(
        "unit.primary_owner_set",
        entity_type="unit",
        entity_id=unit_id,
        new_values={"person_id": person_id},
    )

    return jsonify({"message": "Primary owner set successfully"})
