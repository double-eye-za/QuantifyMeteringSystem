from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
from ..application import db


@dataclass
class MeterAlert(db.Model):
    __tablename__ = "meter_alerts"

    id: Optional[int]
    meter_id: int
    alert_type: str
    severity: str
    message: Optional[str]
    is_resolved: Optional[bool]
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    resolution_notes: Optional[str]
    created_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    resolution_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('communication_loss','tamper_detected','low_credit','disconnection','reconnection','abnormal_usage','meter_fault')",
            name="ck_meter_alerts_type",
        ),
        CheckConstraint(
            "severity IN ('info','warning','error','critical')",
            name="ck_meter_alerts_severity",
        ),
    )
