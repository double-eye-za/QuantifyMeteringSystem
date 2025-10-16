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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "meter_type IN ('electricity','water','solar','bulk_electricity','bulk_water')",
            name="ck_meters_type",
        ),
        CheckConstraint(
            "communication_type IN ('plc','cellular','wifi','manual')",
            name="ck_meters_comm_type",
        ),
        CheckConstraint(
            "communication_status IN ('online','offline','error')",
            name="ck_meters_comm_status",
        ),
    )

    @staticmethod
    def get_all(
        meter_type: Optional[str] = None, communication_status: Optional[str] = None
    ):
        query = Meter.query
        if meter_type:
            query = query.filter(Meter.meter_type == meter_type)
        if communication_status:
            query = query.filter(Meter.communication_status == communication_status)
        return query

    @staticmethod
    def list_available_by_type(meter_type: str):
        """Meters of a type that are not assigned to any unit."""
        from .unit import Unit

        subq_ids = db.session.query(Unit.electricity_meter_id).union(
            db.session.query(Unit.water_meter_id), db.session.query(Unit.solar_meter_id)
        )
        return (
            Meter.query.filter(Meter.meter_type == meter_type)
            .filter(~Meter.id.in_(subq_ids))
            .order_by(Meter.serial_number.asc())
            .all()
        )

    @staticmethod
    def get_by_id(meter_id):
        return Meter.query.get(meter_id)

    @staticmethod
    def create_from_payload(payload: dict):
        meter = Meter(
            serial_number=payload["serial_number"],
            meter_type=payload["meter_type"],
            manufacturer=payload.get("manufacturer"),
            model=payload.get("model"),
            installation_date=payload.get("installation_date"),
            last_reading=None,
            last_reading_date=None,
            communication_type=payload.get("communication_type", "plc"),
            communication_status=payload.get("communication_status", "online"),
            last_communication=None,
            firmware_version=payload.get("firmware_version"),
            is_prepaid=payload.get("is_prepaid", True),
            is_active=payload.get("is_active", True),
        )
        db.session.add(meter)
        db.session.commit()
        return meter

    @staticmethod
    def get_electricity_meters():
        return (
            Meter.get_all(meter_type="electricity")
            .order_by(Meter.serial_number.asc())
            .all()
        )

    @staticmethod
    def get_water_meters():
        return (
            Meter.get_all(meter_type="water").order_by(Meter.serial_number.asc()).all()
        )

    @staticmethod
    def get_solar_meters():
        return (
            Meter.get_all(meter_type="solar").order_by(Meter.serial_number.asc()).all()
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def count_all():
        return Meter.query.count()

    @staticmethod
    def count_active_dc450s():
        return Meter.query.filter(
            Meter.communication_type == "plc", Meter.communication_status == "online"
        ).count()
