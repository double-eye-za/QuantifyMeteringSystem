from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..db import db


@dataclass
class Permission(db.Model):
    __tablename__ = "permissions"

    id: Optional[int]
    name: str
    description: Optional[str]
    permissions: dict

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.JSON, nullable=False, default=dict)
    roles = db.relationship("Role", back_populates="permission")
