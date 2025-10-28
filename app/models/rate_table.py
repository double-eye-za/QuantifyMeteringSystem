from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import CheckConstraint
import json

from ..db import db


@dataclass
class RateTable(db.Model):
    __tablename__ = "rate_tables"

    id: Optional[int]
    name: str
    utility_type: str
    rate_structure: str
    is_default: Optional[bool]
    effective_from: date
    effective_to: Optional[date]
    is_active: Optional[bool]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: date
    updated_at: Optional[date]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    utility_type = db.Column(db.String(20), nullable=False)
    rate_structure = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "utility_type IN ('electricity','water','solar')",
            name="ck_rate_tables_utility_type",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "utility_type": self.utility_type,
            "rate_structure": (
                json.loads(self.rate_structure)
                if isinstance(self.rate_structure, str)
                else self.rate_structure
            ),
            "is_default": self.is_default,
            "effective_from": self.effective_from.isoformat()
            if self.effective_from
            else None,
            "effective_to": self.effective_to.isoformat()
            if self.effective_to
            else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
