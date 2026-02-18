"""MobileInvite model for tracking mobile app invitations with temporary passwords."""
from __future__ import annotations

from datetime import datetime

from app.db import db


class MobileInvite(db.Model):
    """
    MobileInvite model for tracking mobile app invitations.

    Stores temporary passwords in plaintext for admin viewing during testing.
    Records are automatically marked as used when the user logs in for the first time.

    This is a temporary feature for internal testing - passwords are stored
    in plaintext and should be deleted after first login or after a set period.
    """
    __tablename__ = 'mobile_invites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mobile_user_id = db.Column(db.Integer, db.ForeignKey('mobile_users.id', ondelete='CASCADE'), nullable=False, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False)
    temporary_password = db.Column(db.String(50), nullable=False)  # Plaintext for testing

    # Context info
    estate_id = db.Column(db.Integer, db.ForeignKey('estates.id', ondelete='SET NULL'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='SET NULL'), nullable=True)
    role = db.Column(db.String(20), nullable=True)  # 'owner' or 'tenant'

    # SMS status
    sms_sent = db.Column(db.Boolean, default=False, nullable=False)
    sms_error = db.Column(db.String(500), nullable=True)

    # Status tracking
    is_used = db.Column(db.Boolean, default=False, nullable=False)  # True after first login
    used_at = db.Column(db.DateTime, nullable=True)

    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    mobile_user = db.relationship('MobileUser', backref=db.backref('invite', uselist=False))
    person = db.relationship('Person', backref=db.backref('invites', lazy='dynamic'))
    estate = db.relationship('Estate', backref=db.backref('invites', lazy='dynamic'))
    unit = db.relationship('Unit', backref=db.backref('invites', lazy='dynamic'))
    created_by_user = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<MobileInvite {self.phone_number} (Person ID: {self.person_id})>'

    def mark_as_used(self) -> None:
        """Mark the invite as used (after first login)."""
        self.is_used = True
        self.used_at = datetime.utcnow()
        # Clear the password for security
        self.temporary_password = "***USED***"

    def to_dict(self) -> dict:
        """
        Convert invite to dictionary representation.

        Returns:
            Dictionary with invite data including related entity names
        """
        return {
            'id': self.id,
            'mobile_user_id': self.mobile_user_id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'phone_number': self.phone_number,
            'temporary_password': self.temporary_password if not self.is_used else None,
            'estate_id': self.estate_id,
            'estate_name': self.estate.name if self.estate else None,
            'unit_id': self.unit_id,
            'unit_number': self.unit.unit_number if self.unit else None,
            'role': self.role,
            'sms_sent': self.sms_sent,
            'sms_error': self.sms_error,
            'is_used': self.is_used,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_by': self.created_by,
            'created_by_name': f"{self.created_by_user.first_name} {self.created_by_user.last_name}" if self.created_by_user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
