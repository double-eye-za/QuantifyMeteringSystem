from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import json

from ..db import db


@dataclass
class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: Optional[int]
    user_id: Optional[int]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    old_values: Optional[str]
    new_values: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    created_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    ip_address = db.Column(db.String)
    user_agent = db.Column(db.Text)
    request_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
