from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint
from ..db import db


@dataclass
class Meter(db.Model):
    __tablename__ = "meters"

    id: Optional[int]
    serial_number: str
    meter_type: str
    manufacturer: Optional[str]
    model: Optional[str]
    installation_date: Optional[date]
    last_reading: Optional[float]
    last_reading_date: Optional[datetime]
    communication_type: Optional[str]
    communication_status: Optional[str]
    last_communication: Optional[datetime]
    firmware_version: Optional[str]
    is_prepaid: Optional[bool]
    is_active: Optional[bool]
    device_eui: Optional[str]
    lorawan_device_type: Optional[str]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    meter_type = db.Column(db.String(20), nullable=False)
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    installation_date = db.Column(db.Date)
    last_reading = db.Column(db.Numeric(15, 3))
    last_reading_date = db.Column(db.DateTime)
    communication_type = db.Column(db.String(20), default="plc")
    communication_status = db.Column(db.String(20), default="online")
    last_communication = db.Column(db.DateTime)
    firmware_version = db.Column(db.String(50))
    is_prepaid = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)

    # LoRaWAN Device Fields (for backend MQTT integration)
    device_eui = db.Column(db.String(16), unique=True, nullable=True, index=True)
    lorawan_device_type = db.Column(db.String(50), nullable=True)  # milesight_em300, qalcosonic_w1

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "meter_type IN ('electricity','water','solar','hot_water','bulk_electricity','bulk_water')",
            name="ck_meters_type",
        ),
        CheckConstraint(
            "communication_type IN ('plc','cellular','wifi','manual','lora')",
            name="ck_meters_comm_type",
        ),
        CheckConstraint(
            "communication_status IN ('online','offline','error')",
            name="ck_meters_comm_status",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "serial_number": self.serial_number,
            "meter_type": self.meter_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "installation_date": self.installation_date.isoformat()
            if self.installation_date
            else None,
            "last_reading": float(self.last_reading)
            if self.last_reading is not None
            else None,
            "last_reading_date": self.last_reading_date.isoformat()
            if self.last_reading_date
            else None,
            "communication_type": self.communication_type,
            "communication_status": self.communication_status,
            "last_communication": self.last_communication.isoformat()
            if self.last_communication
            else None,
            "firmware_version": self.firmware_version,
            "is_prepaid": self.is_prepaid,
            "is_active": self.is_active,
            "device_eui": self.device_eui,
            "lorawan_device_type": self.lorawan_device_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
