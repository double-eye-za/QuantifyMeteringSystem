from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class Role(db.Model):
    __tablename__ = "roles"

    id: Optional[int]
    name: str
    description: Optional[str]
    is_system_role: Optional[bool]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permission_id = db.Column(db.Integer, db.ForeignKey("permissions.id"))
    is_system_role = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )
    permission = db.relationship("Permission", back_populates="roles", lazy="joined")

    @staticmethod
    def get_all(search=None, page=1, per_page=25):
        """Get all roles with optional filtering and pagination"""
        query = Role.query

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Role.name.ilike(search_term), Role.description.ilike(search_term)
                )
            )

        query = query.order_by(Role.name.asc())

        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        total = query.count()

        return items, total

    @staticmethod
    def get_by_id(role_id):
        """Get role by ID"""
        return Role.query.get_or_404(role_id)

    @staticmethod
    def create_role(name, description, permissions_data, permission_id=None):
        """Create a new role"""
        # If permissions_data is provided but no permission_id, create a new Permission record
        if permissions_data and not permission_id:
            from app.models.permissions import Permission

            permission = Permission.create_permission(
                name=f"{name} Permissions",
                description=f"Permissions for {name} role",
                permissions_data=permissions_data,
            )
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

    @staticmethod
    def update_role(
        role_id, name=None, description=None, permissions_data=None, permission_id=None
    ):
        """Update role details"""
        role = Role.get_by_id(role_id)

        if name is not None:
            role.name = name
        if description is not None:
            role.description = description

        # Handle permissions update
        if permissions_data is not None:
            from app.models.permissions import Permission

            if role.permission_id:
                # Update existing permission
                permission = Permission.query.get(role.permission_id)
                if permission:
                    permission.update_permissions(permissions_data)
            else:
                # Create new permission if none exists
                permission = Permission.create_permission(
                    name=f"{role.name} Permissions",
                    description=f"Permissions for {role.name} role",
                    permissions_data=permissions_data,
                )
                role.permission_id = permission.id

        if permission_id is not None:
            role.permission_id = permission_id

        db.session.commit()
        return role

    @staticmethod
    def delete_role(role_id):
        """Delete a role"""
        role = Role.get_by_id(role_id)

        # Prevent deletion of system roles
        if role.is_system_role:
            raise ValueError("Cannot delete system roles")

        # Check if role has users
        if role.users:
            raise ValueError("Cannot delete role that has assigned users")

        db.session.delete(role)
        db.session.commit()
        return True

    @staticmethod
    def get_roles_for_dropdown():
        """Get roles for dropdown selection"""
        return Role.query.order_by(Role.name.asc()).all()
