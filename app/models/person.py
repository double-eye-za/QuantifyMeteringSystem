from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from ..db import db


@dataclass
class Person(db.Model):
    """
    Core identity model for all app users (owners, tenants, occupants).
    Replaces the old Resident model with support for multiple roles.
    """

    __tablename__ = "persons"

    id: Optional[int]
    first_name: str
    last_name: str
    email: str
    phone: str
    alternate_phone: Optional[str]
    id_number: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    is_active: Optional[bool]
    profile_photo_url: Optional[str]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    alternate_phone = db.Column(db.String(20))
    id_number = db.Column(db.String(20), unique=True, index=True)
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    profile_photo_url = db.Column(db.String(512))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    ownerships = db.relationship(
        "UnitOwnership", back_populates="person", cascade="all, delete-orphan"
    )
    tenancies = db.relationship(
        "UnitTenancy", back_populates="person", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def units_owned(self) -> List:
        """Get all units this person owns"""
        from .unit import Unit
        return [ownership.unit for ownership in self.ownerships]

    @property
    def units_rented(self) -> List:
        """Get all units this person rents"""
        from .unit import Unit
        active_tenancies = [t for t in self.tenancies if not t.move_out_date]
        return [tenancy.unit for tenancy in active_tenancies]

    @property
    def all_units(self) -> List:
        """Get all units this person has access to (owned + rented)"""
        owned_ids = {u.id for u in self.units_owned}
        rented_ids = {u.id for u in self.units_rented}
        all_unit_ids = owned_ids | rented_ids

        from .unit import Unit
        return Unit.query.filter(Unit.id.in_(all_unit_ids)).all() if all_unit_ids else []

    @property
    def is_owner(self) -> bool:
        """Check if person owns any units"""
        return len(self.ownerships) > 0

    @property
    def is_tenant(self) -> bool:
        """Check if person rents any units"""
        return len([t for t in self.tenancies if not t.move_out_date]) > 0

    @property
    def has_app_access(self) -> bool:
        """Check if person has mobile app access"""
        return hasattr(self, 'mobile_user') and self.mobile_user is not None and self.mobile_user.is_active

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "alternate_phone": self.alternate_phone,
            "id_number": self.id_number,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "is_active": self.is_active,
            "profile_photo_url": self.profile_photo_url,
            "has_app_access": self.has_app_access,
            "is_owner": self.is_owner,
            "is_tenant": self.is_tenant,
            "units_count": len(self.all_units),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_detailed(self):
        """Detailed dict with related units"""
        data = self.to_dict()
        data["ownerships"] = [o.to_dict() for o in self.ownerships]
        data["tenancies"] = [t.to_dict() for t in self.tenancies if not t.move_out_date]
        return data
