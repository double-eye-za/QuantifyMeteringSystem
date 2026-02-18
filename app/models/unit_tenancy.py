from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint

from ..db import db


@dataclass
class UnitTenancy(db.Model):
    """
    Tracks tenancy/rental relationships between persons and units.
    Includes lease information and billing responsibility.
    """

    __tablename__ = "unit_tenancies"

    id: Optional[int]
    unit_id: int
    person_id: int
    lease_start_date: Optional[date]
    lease_end_date: Optional[date]
    monthly_rent: Optional[float]
    deposit_amount: Optional[float]
    is_primary_tenant: Optional[bool]
    status: Optional[str]
    move_in_date: Optional[date]
    move_out_date: Optional[date]
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    unit_id = db.Column(
        db.Integer, db.ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lease_start_date = db.Column(db.Date)
    lease_end_date = db.Column(db.Date)  # Nullable for month-to-month leases
    monthly_rent = db.Column(db.Numeric(10, 2))
    deposit_amount = db.Column(db.Numeric(10, 2))
    is_primary_tenant = db.Column(
        db.Boolean, default=False
    )  # Responsible for billing
    status = db.Column(
        db.String(20), default="active"
    )  # active, expired, terminated
    move_in_date = db.Column(db.Date)
    move_out_date = db.Column(db.Date)  # Nullable if still living there
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    unit = db.relationship("Unit", back_populates="tenancies")
    person = db.relationship("Person", back_populates="tenancies")

    __table_args__ = (
        UniqueConstraint("unit_id", "person_id", name="uq_unit_tenancy"),
        CheckConstraint(
            "status IN ('active','expired','terminated')", name="ck_tenancy_status"
        ),
    )

    @property
    def is_active(self) -> bool:
        """Check if tenancy is currently active"""
        return self.status == "active" and not self.move_out_date

    @property
    def is_expired(self) -> bool:
        """Check if lease has expired"""
        if not self.lease_end_date:
            return False  # Month-to-month never expires
        return datetime.now().date() > self.lease_end_date

    def to_dict(self):
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "person_id": self.person_id,
            "person_name": self.person.full_name if self.person else None,
            "lease_start_date": self.lease_start_date.isoformat()
            if self.lease_start_date
            else None,
            "lease_end_date": self.lease_end_date.isoformat()
            if self.lease_end_date
            else None,
            "monthly_rent": float(self.monthly_rent) if self.monthly_rent else None,
            "deposit_amount": float(self.deposit_amount) if self.deposit_amount else None,
            "is_primary_tenant": self.is_primary_tenant,
            "status": self.status,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "move_in_date": self.move_in_date.isoformat()
            if self.move_in_date
            else None,
            "move_out_date": self.move_out_date.isoformat()
            if self.move_out_date
            else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
