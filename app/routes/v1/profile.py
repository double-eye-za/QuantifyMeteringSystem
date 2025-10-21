from __future__ import annotations

from flask import render_template, request, jsonify
from flask_login import login_required, current_user

from . import api_v1
from ...models.user import User
from ...utils.audit import log_action


@api_v1.route("/profile", methods=["GET"])
@login_required
def profile_page():
    user = current_user
    role_name = getattr(getattr(user, "role", None), "name", None)
    return render_template(
        "profile/profile.html",
        user={
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "username": user.username,
            "role": role_name,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    )


@api_v1.route("/profile", methods=["POST"])
@login_required
def update_profile():
    payload = request.get_json(force=True) or {}

    before_data = {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
    }

    user = User.update_profile(current_user, payload)

    # Audit log profile update
    log_action(
        "user.profile.update",
        entity_type="user",
        entity_id=user.id,
        old_values=before_data,
        new_values=payload,
    )

    return jsonify(
        {
            "data": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone,
            }
        }
    )


@api_v1.route(
    "/profile/change-password", methods=["POST"], endpoint="profile_change_password"
)
@login_required
def profile_change_password():
    payload = request.get_json(force=True) or {}
    ok, err = User.change_password(
        current_user,
        payload.get("current_password"),
        payload.get("new_password"),
        payload.get("confirm_password"),
    )
    if not ok:
        return jsonify({"error": err}), 400

    log_action(
        "user.profile.password_change",
        entity_type="user",
        entity_id=current_user.id,
        new_values={
            "username": current_user.username,
            "email": current_user.email,
        },
    )

    return jsonify({"message": "Password updated successfully"})


@api_v1.route("/profile/password-requirements", methods=["GET"])
@login_required
def get_password_requirements():
    """Get password requirements for the current user"""
    from ...utils.password import get_password_requirements

    requirements = get_password_requirements()
    return jsonify({"requirements": requirements})
