from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class TimeOfUseRate(db.Model):
    __tablename__ = "time_of_use_rates"

    id: Optional[int]
    rate_table_id: int
    period_name: str
    start_time: datetime
    end_time: datetime
    weekdays: Optional[bool]
    weekends: Optional[bool]
    rate_per_kwh: float
    created_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    rate_table_id = db.Column(
        db.Integer, db.ForeignKey("rate_tables.id"), nullable=False
    )
    period_name = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    weekdays = db.Column(db.Boolean, default=True)
    weekends = db.Column(db.Boolean, default=False)
    rate_per_kwh = db.Column(db.Numeric(10, 4), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
