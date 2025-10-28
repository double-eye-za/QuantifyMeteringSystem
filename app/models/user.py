from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from ..db import db


@dataclass
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Optional[int]
    username: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role_id: Optional[str]
    is_active: Optional[bool]
    is_super_admin: Optional[bool]
    last_login: Optional[datetime]
    failed_login_attempts: Optional[int]
    locked_until: Optional[datetime]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    is_active = db.Column(db.Boolean, default=True)
    is_super_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )
    role = db.relationship("Role", backref="users")

    def get_id(self):
        return str(self.id)

    # Static methods removed; use app.services.users for user operations

    def has_permission(self, permission_code):
        """Check if user has specific permission"""
        if self.is_super_admin:
            return True

        if not self.role or not self.role.permission:
            return False

        permissions = self.role.permission.permissions
        return permissions.get(permission_code, False)
