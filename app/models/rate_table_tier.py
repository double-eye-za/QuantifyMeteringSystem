from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from ..db import db


@dataclass
class RateTableTier(db.Model):
    __tablename__ = "rate_table_tiers"

    id: Optional[int]
    rate_table_id: int
    tier_number: int
    from_kwh: float
    to_kwh: Optional[float]
    rate_per_kwh: float
    description: Optional[str]
    created_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    rate_table_id = db.Column(
        db.Integer, db.ForeignKey("rate_tables.id"), nullable=False
    )
    tier_number = db.Column(db.Integer, nullable=False)
    from_kwh = db.Column(db.Numeric(10, 2), nullable=False)
    to_kwh = db.Column(db.Numeric(10, 2))
    rate_per_kwh = db.Column(db.Numeric(10, 4), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "rate_table_id", "tier_number", name="uq_rate_table_tier_unique"
        ),
    )
