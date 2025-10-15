from __future__ import annotations

from flask import render_template, request, jsonify
from flask_login import login_required, current_user

from . import api_v1
from ...models.user import User


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
    user = User.update_profile(current_user, payload)
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
    return jsonify({"message": "Password updated successfully"})
