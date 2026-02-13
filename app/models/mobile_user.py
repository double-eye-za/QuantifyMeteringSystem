"""MobileUser model for mobile app authentication (Owners/Tenants)."""
from __future__ import annotations

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.db import db


class MobileUser(UserMixin, db.Model):
    """
    MobileUser model for mobile app authentication (Owners and Tenants only).

    Separate from the web portal User model (for admin/staff).
    Links to Person model and provides authentication credentials.
    Supports temporary passwords that must be changed on first login.

    Extends UserMixin for Flask-Login session support on the web portal.
    Uses 'mobile:{id}' prefix in get_id() to distinguish from admin User sessions.
    """
    __tablename__ = 'mobile_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    temporary_password_hash = db.Column(db.String(255), nullable=True)
    password_must_change = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    person = db.relationship('Person', backref=db.backref('mobile_user', uselist=False))

    def __repr__(self):
        return f'<MobileUser {self.phone_number} (Person ID: {self.person_id})>'

    def get_id(self) -> str:
        """Return prefixed ID for Flask-Login to distinguish from admin User model.

        The 'mobile:' prefix ensures no collision with User.get_id() which
        returns a plain integer string. The user_loader in auth.py parses
        this prefix to know which model to query.
        """
        return f'mobile:{self.id}'

    @property
    def first_name(self) -> str:
        """Proxy to person.first_name so base.html header works for both user types."""
        return self.person.first_name if self.person else ''

    @property
    def last_name(self) -> str:
        """Proxy to person.last_name so base.html header works for both user types."""
        return self.person.last_name if self.person else ''

    @property
    def email(self) -> str:
        """Proxy to person.email for profile display."""
        return self.person.email if self.person else ''

    @property
    def username(self) -> str:
        """Return phone_number as username equivalent for audit logging."""
        return self.phone_number

    def set_password(self, password: str) -> None:
        """
        Set the user's permanent password.

        This clears any temporary password and removes the password_must_change flag.

        Args:
            password: The new password to set
        """
        self.password_hash = generate_password_hash(password)
        self.temporary_password_hash = None
        self.password_must_change = False

    def set_temporary_password(self, temp_password: str) -> None:
        """
        Set a temporary password that must be changed on first login.

        Sets the password_must_change flag to True.

        Args:
            temp_password: The temporary password to set
        """
        self.temporary_password_hash = generate_password_hash(temp_password)
        self.password_must_change = True

    def check_password(self, password: str) -> bool:
        """
        Check if the provided password is valid.

        Checks temporary password first (if set), then permanent password.

        Args:
            password: The password to check

        Returns:
            True if password matches, False otherwise
        """
        # If temporary password is set and matches, use it
        if self.temporary_password_hash and check_password_hash(self.temporary_password_hash, password):
            return True

        # Otherwise check permanent password
        return check_password_hash(self.password_hash, password)

    def update_last_login(self) -> None:
        """Update the last_login timestamp to now."""
        self.last_login = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the user account (prevents login)."""
        self.is_active = False

    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True

    def to_dict(self) -> dict:
        """
        Convert mobile user to dictionary representation.

        Note: Does not include password hashes for security.

        Returns:
            Dictionary with user data
        """
        return {
            'id': self.id,
            'person_id': self.person_id,
            'phone_number': self.phone_number,
            'password_must_change': self.password_must_change,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
