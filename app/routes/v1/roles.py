from __future__ import annotations

from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.role import Role
from app.models.permissions import Permission
from app.utils.decorators import requires_permission
from app.utils.audit import log_action
from app.utils.pagination import paginate_query

from . import api_v1


@api_v1.route("/roles", methods=["GET"])
@login_required
@requires_permission("roles.view")
def roles_page():
    search = request.args.get("search", "").strip()

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))

    roles, total = Role.get_all(
        search=search if search else None, page=page, per_page=per_page
    )

    roles_data = []
    for role in roles:
        perm_desc = role.permission.description if role.permission else None
        roles_data.append(
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system_role": role.is_system_role,
                "permission_id": role.permission_id,
                "permission_name": role.permission.name if role.permission else None,
                "permission_description": perm_desc,
                "permissions": role.permission.permissions if role.permission else {},
                "user_count": len(role.users) if hasattr(role, "users") else 0,
                "created_at": role.created_at.strftime("%Y-%m-%d %H:%M")
                if role.created_at
                else None,
            }
        )

    # Get permissions for dropdown
    permissions = Permission.get_all_permissions()

    modules_actions = {}
    for perm in permissions:
        perms_dict = getattr(perm, "permissions", {}) or {}
        for module, actions in perms_dict.items():
            if module not in modules_actions:
                modules_actions[module] = set()
            if isinstance(actions, dict):
                for action in actions.keys():
                    modules_actions[module].add(action)

    modules_actions = {m: sorted(list(a)) for m, a in sorted(modules_actions.items())}

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
    }

    return render_template(
        "roles&permissions/roles.html",
        roles=roles_data,
        permissions=permissions,
        modules_actions=modules_actions,
        pagination=pagination,
        current_filters={"search": search},
    )


@api_v1.route("/api/roles", methods=["POST"])
@login_required
@requires_permission("roles.create")
def create_role():
    data = request.get_json()

    try:
        if not data.get("name"):
            return jsonify({"error": "Role name is required"}), 400

        role = Role.create_role(
            name=data["name"],
            description=data.get("description", ""),
            permissions_data=data.get("permissions", {}),
            permission_id=data.get("permission_id"),
        )
        log_action(
            "role.create", entity_type="role", entity_id=role.id, new_values=data
        )
        return jsonify(
            {
                "success": True,
                "message": "Role created successfully",
                "role_id": role.id,
            }
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_v1.route("/api/roles/<int:role_id>", methods=["PUT"])
@login_required
@requires_permission("roles.edit")
def update_role(role_id):
    data = request.get_json()

    try:
        Role.update_role(
            role_id=role_id,
            name=data.get("name"),
            description=data.get("description"),
            permissions_data=data.get("permissions"),
            permission_id=data.get("permission_id"),
        )
        log_action(
            "role.update", entity_type="role", entity_id=role_id, new_values=data
        )
        return jsonify({"success": True, "message": "Role updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_v1.route("/api/roles/<int:role_id>", methods=["DELETE"])
@login_required
@requires_permission("roles.delete")
def delete_role(role_id):
    try:
        Role.delete_role(role_id)
        log_action("role.delete", entity_type="role", entity_id=role_id)
        return jsonify({"success": True, "message": "Role deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
