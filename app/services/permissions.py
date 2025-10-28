from __future__ import annotations

from typing import Optional, List

from app.db import db
from app.models.permissions import Permission


def list_permissions() -> List[Permission]:
    return Permission.query.order_by(Permission.name.asc()).all()


def get_permission_by_id(permission_id: int) -> Optional[Permission]:
    return Permission.query.get(permission_id)


def create_permission(
    name: str, description: str, permissions_data: dict
) -> Permission:
    perm = Permission(name=name, description=description, permissions=permissions_data)
    db.session.add(perm)
    db.session.commit()
    return perm


def update_permission(permission: Permission, permissions_data: dict) -> Permission:
    permission.permissions = permissions_data
    db.session.commit()
    return permission


def delete_permission(permission: Permission) -> None:
    db.session.delete(permission)
    db.session.commit()
