from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class CommunicationType(db.Model):
    """
    Communication Type reference table for managing meter communication methods.
    Allows admins to add new communication types without code changes.
    """
    __tablename__ = "communication_types"

    id: Optional[int]
    code: str
    name: str
    description: Optional[str]
    requires_device_eui: Optional[bool]
    requires_gateway: Optional[bool]
    supports_remote_control: Optional[bool]
    is_active: Optional[bool]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # e.g., "lora"
    name = db.Column(db.String(100), nullable=False)  # e.g., "LoRaWAN (Cellular)"
    description = db.Column(db.Text, nullable=True)
    requires_device_eui = db.Column(db.Boolean, default=False)  # LoRa, cellular need EUI
    requires_gateway = db.Column(db.Boolean, default=False)  # LoRa needs gateway
    supports_remote_control = db.Column(db.Boolean, default=False)  # Can send commands
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "requires_device_eui": self.requires_device_eui,
            "requires_gateway": self.requires_gateway,
            "supports_remote_control": self.supports_remote_control,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
