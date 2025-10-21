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

    @staticmethod
    def update_profile(user, payload):
        if not user or not payload:
            return user
        for field in ("first_name", "last_name", "email", "phone"):
            if field in payload and payload[field] is not None:
                setattr(user, field, payload[field])
        db.session.commit()
        return user

    @staticmethod
    def change_password(user, current_password, new_password, confirm_password):
        if not current_password or not new_password or not confirm_password:
            return False, "All password fields are required"
        if new_password != confirm_password:
            return False, "New passwords do not match"
        if not user.check_password(current_password):
            return False, "Current password is incorrect"

        # Validate new password against security settings
        from ..utils.password import validate_password_policy

        is_valid, error_message = validate_password_policy(new_password)
        if not is_valid:
            return False, error_message

        user.set_password(new_password)
        db.session.commit()
        return True, None

    @staticmethod
    def get_all(search=None, is_active=None, role_id=None, page=1, per_page=25):
        """Get all users with optional filtering and pagination"""
        query = User.query

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.username.ilike(search_term),
                )
            )

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if role_id is not None:
            query = query.filter(User.role_id == role_id)

        query = query.order_by(User.created_at.desc())

        # Apply pagination
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        total = query.count()

        return items, total

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        return User.query.get_or_404(user_id)

    @staticmethod
    def create_user(
        username,
        email,
        first_name,
        last_name,
        password,
        role_id=None,
        phone=None,
        is_active=True,
    ):
        """Create a new user"""
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role_id=role_id,
            is_active=is_active,
            is_super_admin=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user(user_id, data):
        """Update user details"""
        user = User.get_by_id(user_id)

        for field in [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role_id",
        ]:
            if field in data and data[field] is not None:
                setattr(user, field, data[field])

        if "is_active" in data:
            user.is_active = bool(data["is_active"])

        if "role_id" in data and user.role:
            user.is_super_admin = user.role.name == "Super Administrator"

        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        """Delete a user"""
        user = User.get_by_id(user_id)

        # Prevent deletion of super admin users
        if user.is_super_admin:
            raise ValueError("Cannot delete super administrator users")

        db.session.delete(user)
        db.session.commit()
        return True

    @staticmethod
    def set_active_status(user_id, is_active):
        """Set user active status"""
        user = User.get_by_id(user_id)
        user.is_active = is_active
        db.session.commit()
        return user

    @staticmethod
    def get_roles_for_dropdown():
        """Get roles for dropdown selection"""
        from .role import Role

        return Role.query.all()

    def has_permission(self, permission_code):
        """Check if user has specific permission"""
        if self.is_super_admin:
            return True

        if not self.role or not self.role.permission:
            return False

        permissions = self.role.permission.permissions
        return permissions.get(permission_code, False)
