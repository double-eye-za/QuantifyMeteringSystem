from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import json

from ..db import db


@dataclass
class Role(db.Model):
    __tablename__ = "roles"

    id: Optional[int]
    name: str
    description: Optional[str]
    permissions: dict
    is_system_role: Optional[bool]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.Text, nullable=False, default="{}")
    is_system_role = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )
