from __future__ import annotations

from flask import render_template, request, jsonify
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.role import Role
from app.utils.decorators import requires_permission, get_user_estate_filter, get_allowed_estates
from app.utils.audit import log_action
from app.utils.pagination import paginate_query

from . import api_v1

from ...services.users import (
    list_users as svc_list_users,
    create_user as svc_create_user,
    update_user as svc_update_user,
    delete_user as svc_delete_user,
    get_user_by_id as svc_get_user_by_id,
    set_active_status as svc_set_active_status,
    list_roles_for_dropdown as svc_list_roles_for_dropdown,
)


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

    # Estate-scoped users only see users from their estate
    estate_scope = get_user_estate_filter()

    users, total = svc_list_users(
        search=search if search else None,
        is_active=is_active,
        role_id=role_id_int,
        estate_id=estate_scope,
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
                "estate_id": user.estate_id,
                "estate_name": user.estate.name if user.estate else None,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M")
                if user.created_at
                else None,
            }
        )

    roles = svc_list_roles_for_dropdown()
    estates = [{"id": e.id, "name": e.name} for e in get_allowed_estates()]

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
        estates=estates,
        pagination=pagination,
        current_filters={"search": search, "status": status, "role_id": role_id},
    )


@api_v1.route("/api/users", methods=["GET"])
@login_required
@requires_permission("users.view")
def list_users_api():
    """JSON API endpoint to list users with filtering and pagination."""
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

    # Estate-scoped users only see users from their estate
    estate_scope = get_user_estate_filter()

    users, total = svc_list_users(
        search=search if search else None,
        is_active=is_active,
        role_id=role_id_int,
        estate_id=estate_scope,
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
                "estate_id": user.estate_id,
                "estate_name": user.estate.name if user.estate else None,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M")
                if user.created_at
                else None,
            }
        )

    return jsonify({
        "data": users_data,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
    })


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

        user = svc_create_user(**data)

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

    except IntegrityError as e:
        # Handle database constraint violations with user-friendly messages
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

        if 'users_email_key' in error_msg or 'duplicate' in error_msg and 'email' in error_msg:
            return jsonify({"error": "This email address is already in use. Please use a different email."}), 400
        elif 'users_username_key' in error_msg or 'duplicate' in error_msg and 'username' in error_msg:
            return jsonify({"error": "This username is already taken. Please choose a different username."}), 400
        elif 'users_phone_key' in error_msg or 'duplicate' in error_msg and 'phone' in error_msg:
            return jsonify({"error": "This phone number is already registered. Please use a different phone number."}), 400
        else:
            return jsonify({"error": "A user with this information already exists. Please check your input."}), 400

    except ValueError as e:
        # Handle validation errors
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500


@api_v1.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required
@requires_permission("users.edit")
def update_user(user_id):
    data = request.get_json()

    try:
        before = svc_get_user_by_id(user_id)
        if not before:
            return jsonify({"error": "User not found"}), 404

        before_dict = before.to_dict() if hasattr(before, "to_dict") and before else {}
        svc_update_user(user_id, data)
        log_action(
            "user.update",
            entity_type="user",
            entity_id=user_id,
            old_values=before_dict,
            new_values=data,
        )
        return jsonify({"success": True, "message": "User updated successfully"}), 200

    except IntegrityError as e:
        # Handle database constraint violations with user-friendly messages
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

        if 'users_email_key' in error_msg or 'duplicate' in error_msg and 'email' in error_msg:
            return jsonify({"error": "This email address is already in use. Please use a different email."}), 400
        elif 'users_username_key' in error_msg or 'duplicate' in error_msg and 'username' in error_msg:
            return jsonify({"error": "This username is already taken. Please choose a different username."}), 400
        elif 'users_phone_key' in error_msg or 'duplicate' in error_msg and 'phone' in error_msg:
            return jsonify({"error": "This phone number is already registered. Please use a different phone number."}), 400
        else:
            return jsonify({"error": "A user with this information already exists. Please check your input."}), 400

    except ValueError as e:
        # Handle validation errors
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500


@api_v1.route("/api/users/<int:user_id>", methods=["DELETE"])
@login_required
@requires_permission("users.delete")
def delete_user(user_id):
    try:
        svc_delete_user(user_id)
        log_action("user.delete", entity_type="user", entity_id=user_id)
        return jsonify({"success": True, "message": "User deleted successfully"}), 200

    except IntegrityError as e:
        # Handle foreign key constraint violations
        return jsonify({"error": "Cannot delete this user because they have associated records. Please remove or reassign their data first."}), 400

    except ValueError as e:
        # Handle validation errors (e.g., cannot delete super admin)
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500


@api_v1.route("/api/users/<int:user_id>/enable", methods=["PUT"])
@login_required
@requires_permission("users.enable")
def enable_user(user_id):
    try:
        svc_set_active_status(user_id, True)
        log_action("user.enable", entity_type="user", entity_id=user_id)
        return jsonify({"success": True, "message": "User enabled successfully"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500


@api_v1.route("/api/users/<int:user_id>/disable", methods=["PUT"])
@login_required
@requires_permission("users.disable")
def disable_user(user_id):
    try:
        svc_set_active_status(user_id, False)
        log_action("user.disable", entity_type="user", entity_id=user_id)
        return jsonify({"success": True, "message": "User disabled successfully"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500
