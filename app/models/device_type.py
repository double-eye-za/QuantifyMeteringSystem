from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class DeviceType(db.Model):
    """
    Device Type reference table for managing LoRaWAN device types.
    Allows admins to add new device types without code changes.
    """
    __tablename__ = "device_types"

    id: Optional[int]
    code: str
    name: str
    description: Optional[str]
    manufacturer: Optional[str]
    default_model: Optional[str]
    supports_temperature: Optional[bool]
    supports_pulse: Optional[bool]
    supports_modbus: Optional[bool]
    is_active: Optional[bool]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., "milesight_em300"
    name = db.Column(db.String(100), nullable=False)  # e.g., "Milesight EM300-DI (Pulse Counter)"
    description = db.Column(db.Text, nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)  # e.g., "Milesight"
    default_model = db.Column(db.String(100), nullable=True)  # e.g., "EM300-DI"
    supports_temperature = db.Column(db.Boolean, default=False)
    supports_pulse = db.Column(db.Boolean, default=False)
    supports_modbus = db.Column(db.Boolean, default=False)
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
            "manufacturer": self.manufacturer,
            "default_model": self.default_model,
            "supports_temperature": self.supports_temperature,
            "supports_pulse": self.supports_pulse,
            "supports_modbus": self.supports_modbus,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
