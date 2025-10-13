from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
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
    wallet_id: Optional[int]
    electricity_meter_id: Optional[int]
    water_meter_id: Optional[int]
    solar_meter_id: Optional[int]
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
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"))
    electricity_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    water_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    solar_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
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
