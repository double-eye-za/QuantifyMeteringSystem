from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class Role(db.Model):
    __tablename__ = "roles"

    id: Optional[int]
    name: str
    description: Optional[str]
    is_system_role: Optional[bool]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permission_id = db.Column(db.Integer, db.ForeignKey("permissions.id"))
    is_system_role = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )
    permission = db.relationship("Permission", back_populates="roles", lazy="joined")
