from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
import json

from ..db import db


@dataclass
class Notification(db.Model):
    __tablename__ = "notifications"

    id: Optional[int]
    recipient_type: str
    recipient_id: Optional[int]
    notification_type: str
    subject: Optional[str]
    message: str
    priority: Optional[str]
    channel: str
    status: Optional[str]
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    error_message: Optional[str]
    push_token: Optional[str]
    push_provider: Optional[str]
    push_payload: Optional[str]
    created_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    recipient_type = db.Column(db.String(20), nullable=False)
    recipient_id = db.Column(db.Integer)
    notification_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="normal")
    channel = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="pending")
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    push_token = db.Column(db.Text)
    push_provider = db.Column(db.String(20))
    push_payload = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "recipient_type IN ('user','resident','system')",
            name="ck_notifications_recipient_type",
        ),
        CheckConstraint(
            "priority IN ('low','normal','high','critical')",
            name="ck_notifications_priority",
        ),
        CheckConstraint(
            "channel IN ('email','sms','push','in_app')",
            name="ck_notifications_channel",
        ),
        CheckConstraint(
            "status IN ('pending','sent','delivered','failed','read')",
            name="ck_notifications_status",
        ),
    )
