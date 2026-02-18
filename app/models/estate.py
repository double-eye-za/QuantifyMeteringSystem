from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class Estate(db.Model):
    __tablename__ = "estates"

    id: Optional[int]
    code: Optional[str]
    name: str
    address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    total_units: Optional[int]
    bulk_electricity_meter_id: Optional[int]
    bulk_water_meter_id: Optional[int]
    electricity_rate_table_id: Optional[int]
    water_rate_table_id: Optional[int]
    electricity_markup_percentage: Optional[float]
    water_markup_percentage: Optional[float]
    solar_free_allocation_kwh: Optional[float]
    is_active: Optional[bool]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    code = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    contact_name = db.Column(db.String(200))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(255))
    total_units = db.Column(db.Integer, default=0, nullable=False)
    bulk_electricity_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    bulk_water_meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    electricity_rate_table_id = db.Column(db.Integer, db.ForeignKey("rate_tables.id"))
    water_rate_table_id = db.Column(db.Integer, db.ForeignKey("rate_tables.id"))
    electricity_markup_percentage = db.Column(db.Numeric(5, 2), default=0.00)
    water_markup_percentage = db.Column(db.Numeric(5, 2), default=0.00)
    solar_free_allocation_kwh = db.Column(db.Numeric(10, 2), default=50.00)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "total_units": self.total_units,
            "bulk_electricity_meter_id": self.bulk_electricity_meter_id,
            "bulk_water_meter_id": self.bulk_water_meter_id,
            "electricity_rate_table_id": self.electricity_rate_table_id,
            "water_rate_table_id": self.water_rate_table_id,
            "electricity_markup_percentage": float(self.electricity_markup_percentage)
            if self.electricity_markup_percentage is not None
            else None,
            "water_markup_percentage": float(self.water_markup_percentage)
            if self.water_markup_percentage is not None
            else None,
            "solar_free_allocation_kwh": float(self.solar_free_allocation_kwh)
            if self.solar_free_allocation_kwh is not None
            else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
