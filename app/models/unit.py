from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint, or_
from ..db import db


@dataclass
class Unit(db.Model):
    __tablename__ = "units"

    id: Optional[int]
    estate_id: int
    unit_number: str
    floor: Optional[str]
    building: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    size_sqm: Optional[float]
    occupancy_status: Optional[str]
    resident_id: Optional[int]
    electricity_meter_id: Optional[int]
    water_meter_id: Optional[int]
    solar_meter_id: Optional[int]
    hot_water_meter_id: Optional[int]
    electricity_rate_table_id: Optional[int]
    water_rate_table_id: Optional[int]
    is_active: Optional[bool]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    estate_id = db.Column(db.Integer, db.ForeignKey("estates.id"), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.String(20))
    building = db.Column(db.String(50))
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    size_sqm = db.Column(db.Numeric(10, 2))
    occupancy_status = db.Column(db.String(20), default="vacant")
    resident_id = db.Column(db.Integer, db.ForeignKey("residents.id"))
    wallet = db.relationship(
        "Wallet",
        uselist=False,
        backref="unit",
        primaryjoin="Unit.id==Wallet.unit_id",
    )
    resident = db.relationship("Resident", backref="unit")
    electricity_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    water_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    solar_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    hot_water_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    electricity_rate_table_id = db.Column(db.Integer, db.ForeignKey("rate_tables.id"))
    water_rate_table_id = db.Column(db.Integer, db.ForeignKey("rate_tables.id"))
    estate = db.relationship("Estate", backref="units")
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "estate_id", "unit_number", name="uq_units_estate_unit_number"
        ),
        CheckConstraint(
            "occupancy_status IN ('occupied','vacant','maintenance')",
            name="ck_units_occupancy_status",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "estate_id": self.estate_id,
            "unit_number": self.unit_number,
            "floor": self.floor,
            "building": self.building,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "size_sqm": float(self.size_sqm) if self.size_sqm is not None else None,
            "occupancy_status": self.occupancy_status,
            "resident_id": self.resident_id,
            "resident": {
                "id": self.resident_id,
            }
            if self.resident_id
            else None,
            "wallet_id": self.wallet.id if getattr(self, "wallet", None) else None,
            "wallet": self.wallet.to_dict() if getattr(self, "wallet", None) else None,
            "electricity_meter_id": self.electricity_meter_id,
            "water_meter_id": self.water_meter_id,
            "solar_meter_id": self.solar_meter_id,
            "hot_water_meter_id": self.hot_water_meter_id,
            "electricity_rate_table_id": self.electricity_rate_table_id,
            "water_rate_table_id": self.water_rate_table_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
