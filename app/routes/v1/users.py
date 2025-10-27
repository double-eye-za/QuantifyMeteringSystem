from __future__ import annotations

from flask import render_template, request, jsonify
from flask_login import login_required
from app.models.user import User
from app.models.role import Role
from app.utils.decorators import requires_permission
from app.utils.audit import log_action
from app.utils.pagination import paginate_query

from . import api_v1


@api_v1.route("/users", methods=["GET"])
@login_required
@requires_permission("users.view")
def users_page():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip().lower()
    role_id = request.args.get("role_id", "").strip()

    is_active = None
    if status == "active":
        is_active = True
    elif status == "disabled":
        is_active = False

    role_id_int = None
    if role_id:
        try:
            role_id_int = int(role_id)
        except ValueError:
            pass

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))

    users, total = User.get_all(
        search=search if search else None,
        is_active=is_active,
        role_id=role_id_int,
        page=page,
        per_page=per_page,
    )

    users_data = []
    for user in users:
        users_data.append(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}",
                "phone": user.phone,
                "is_active": user.is_active,
                "is_super_admin": user.is_super_admin,
                "role_id": user.role_id,
                "role_name": user.role.name if user.role else None,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M")
                if user.created_at
                else None,
            }
        )

    roles = Role.get_roles_for_dropdown()

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1),
    }

    return render_template(
        "users/users.html",
        users=users_data,
        roles=roles,
        pagination=pagination,
        current_filters={"search": search, "status": status, "role_id": role_id},
    )


@api_v1.route("/api/users", methods=["POST"])
@login_required
@requires_permission("users.create")
def create_user():
    data = request.get_json()

    try:
        required_fields = ["username", "email", "first_name", "last_name", "password"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        user = User.create_user(
            username=data["username"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            password=data["password"],
            role_id=data.get("role_id"),
            phone=data.get("phone"),
            is_active=data.get("is_active", True),
        )

        # audit
        log_action(
            "user.create",
            entity_type="user",
            entity_id=user.id,
            new_values={k: v for k, v in data.items() if k != "password"},
        )

        return jsonify(
            {
                "success": True,
                "message": "User created successfully",
                "user_id": user.id,
            }
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_v1.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required
@requires_permission("users.edit")
def update_user(user_id):
    data = request.get_json()

    try:
        before = User.get_by_id(user_id)
        before_dict = before.to_dict() if hasattr(before, "to_dict") and before else {}
        User.update_user(user_id, data)
        log_action(
            "user.update",
            entity_type="user",
            entity_id=user_id,
            old_values=before_dict,
            new_values=data,
        )
        return jsonify({"success": True, "message": "User updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_v1.route("/api/users/<int:user_id>", methods=["DELETE"])
@login_required
@requires_permission("users.delete")
def delete_user(user_id):
    try:
        User.delete_user(user_id)
        log_action("user.delete", entity_type="user", entity_id=user_id)
        return jsonify({"success": True, "message": "User deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_v1.route("/api/users/<int:user_id>/enable", methods=["PUT"])
@login_required
@requires_permission("users.enable")
def enable_user(user_id):
    try:
        User.set_active_status(user_id, True)
        log_action("user.enable", entity_type="user", entity_id=user_id)
        return jsonify({"success": True, "message": "User enabled successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_v1.route("/api/users/<int:user_id>/disable", methods=["PUT"])
@login_required
@requires_permission("users.disable")
def disable_user(user_id):
    try:
        User.set_active_status(user_id, False)
        log_action("user.disable", entity_type="user", entity_id=user_id)
        return jsonify({"success": True, "message": "User disabled successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
