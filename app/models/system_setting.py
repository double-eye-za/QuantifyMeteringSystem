from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
from ..db import db


@dataclass
class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id: Optional[int]
    setting_key: str
    setting_value: Optional[str]
    setting_type: Optional[str]
    description: Optional[str]
    category: Optional[str]
    is_encrypted: Optional[bool]
    updated_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(20))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    is_encrypted = db.Column(db.Boolean, default=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "setting_type IN ('string','number','boolean','json')",
            name="ck_system_settings_type",
        ),
    )

    # Static methods removed; use app.services.system_settings for reading and writing settings
