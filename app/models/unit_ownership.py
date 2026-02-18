from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint

from ..db import db


@dataclass
class UnitOwnership(db.Model):
    """
    Tracks ownership relationships between persons and units.
    Supports joint ownership with ownership percentages.
    """

    __tablename__ = "unit_ownerships"

    id: Optional[int]
    unit_id: int
    person_id: int
    ownership_percentage: float
    purchase_date: Optional[date]
    purchase_price: Optional[float]
    is_primary_owner: Optional[bool]
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
    ownership_percentage = db.Column(
        db.Numeric(5, 2), nullable=False, default=100.00
    )  # 0.00 to 100.00
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Numeric(15, 2))
    is_primary_owner = db.Column(
        db.Boolean, default=False
    )  # Primary contact for correspondence
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    unit = db.relationship("Unit", back_populates="ownerships")
    person = db.relationship("Person", back_populates="ownerships")

    __table_args__ = (
        UniqueConstraint("unit_id", "person_id", name="uq_unit_ownership"),
        CheckConstraint(
            "ownership_percentage >= 0 AND ownership_percentage <= 100",
            name="ck_ownership_percentage",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "person_id": self.person_id,
            "person_name": self.person.full_name if self.person else None,
            "ownership_percentage": float(self.ownership_percentage) if self.ownership_percentage else None,
            "purchase_date": self.purchase_date.isoformat()
            if self.purchase_date
            else None,
            "purchase_price": float(self.purchase_price) if self.purchase_price else None,
            "is_primary_owner": self.is_primary_owner,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
