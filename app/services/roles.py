from __future__ import annotations

from typing import Optional, Tuple, List

from app.db import db
from app.models.role import Role
from app.models.permissions import Permission


def list_roles(
    search: Optional[str] = None, page: int = 1, per_page: int = 25
) -> Tuple[List[Role], int]:
    query = Role.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Role.name.ilike(like), Role.description.ilike(like))
        )
    query = query.order_by(Role.name.asc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_role_by_id(role_id: int) -> Optional[Role]:
    return Role.query.get(role_id)


def create_role(
    name: str,
    description: str = "",
    permissions_data: dict | None = None,
    permission_id: int | None = None,
) -> Role:
    if permissions_data and not permission_id:
        permission = Permission(
            name=f"{name} Permissions",
            description=f"Permissions for {name} role",
            permissions=permissions_data,
        )
        db.session.add(permission)
        db.session.flush()
        permission_id = permission.id
    role = Role(
        name=name,
        description=description,
        permission_id=permission_id,
        is_system_role=False,
    )
    db.session.add(role)
    db.session.commit()
    return role


def update_role(
    role_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permissions_data: dict | None = None,
    permission_id: int | None = None,
) -> Role:
    role = Role.query.get(role_id)
    if not role:
        raise ValueError("Role not found")
    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    if permissions_data is not None:
        if role.permission_id:
            perm = Permission.query.get(role.permission_id)
            if perm:
                perm.permissions = permissions_data
        else:
            perm = Permission(
                name=f"{role.name} Permissions",
                description=f"Permissions for {role.name} role",
                permissions=permissions_data,
            )
            db.session.add(perm)
            db.session.flush()
            role.permission_id = perm.id
    if permission_id is not None:
        role.permission_id = permission_id
    db.session.commit()
    return role


def delete_role(role_id: int) -> None:
    role = Role.query.get(role_id)
    if not role:
        return
    if role.is_system_role:
        raise ValueError("Cannot delete system roles")
    if getattr(role, "users", []):
        raise ValueError("Cannot delete role that has assigned users")
    db.session.delete(role)
    db.session.commit()
