from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from ..db import db


@dataclass
class ReconciliationReport(db.Model):
    __tablename__ = "reconciliation_reports"

    id: Optional[int]
    estate_id: int
    report_date: date
    utility_type: str
    bulk_meter_reading: float
    sum_unit_readings: float
    variance: float
    variance_percentage: Optional[float]
    loss_amount: Optional[float]
    notes: Optional[str]
    created_at: Optional[datetime]
    created_by: Optional[int]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    estate_id = db.Column(db.Integer, db.ForeignKey("estates.id"), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    utility_type = db.Column(db.String(20), nullable=False)
    bulk_meter_reading = db.Column(db.Numeric(15, 3), nullable=False)
    sum_unit_readings = db.Column(db.Numeric(15, 3), nullable=False)
    variance = db.Column(db.Numeric(15, 3), nullable=False)
    variance_percentage = db.Column(db.Numeric(5, 2))
    loss_amount = db.Column(db.Numeric(15, 3))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint(
            "estate_id", "report_date", "utility_type", name="uq_reconciliation_unique"
        ),
        CheckConstraint(
            "utility_type IN ('electricity','water')",
            name="ck_reconciliation_utility",
        ),
    )
