from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class Estate(db.Model):
    __tablename__ = "estates"

    id: Optional[int]
    code: str
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
    code = db.Column(db.String(20), unique=True, nullable=False)
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

    @staticmethod
    def get_all(search: Optional[str] = None, is_active: Optional[bool] = None):
        query = Estate.query
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(Estate.name.ilike(like), Estate.code.ilike(like))
            )
        if is_active is not None:
            query = query.filter(Estate.is_active == is_active)
        return query

    @staticmethod
    def get_by_id(estate_id: int):
        return Estate.query.get(estate_id)

    @staticmethod
    def create_from_payload(payload, user_id: Optional[int] = None):
        estate = Estate(
            code=payload.get("code"),
            name=payload.get("name"),
            address=payload.get("address"),
            city=payload.get("city"),
            postal_code=payload.get("postal_code"),
            contact_name=payload.get("contact_name"),
            contact_phone=payload.get("contact_phone"),
            contact_email=payload.get("contact_email"),
            total_units=payload.get("total_units", 0),
            electricity_rate_table_id=payload.get("electricity_rate_table_id"),
            water_rate_table_id=payload.get("water_rate_table_id"),
            bulk_electricity_meter_id=payload.get("bulk_electricity_meter_id"),
            bulk_water_meter_id=payload.get("bulk_water_meter_id"),
            electricity_markup_percentage=payload.get(
                "electricity_markup_percentage", 0.00
            ),
            water_markup_percentage=payload.get("water_markup_percentage", 0.00),
            solar_free_allocation_kwh=payload.get("solar_free_allocation_kwh", 50.00),
            is_active=payload.get("is_active", True),
            created_by=user_id,
        )
        db.session.add(estate)
        db.session.commit()
        return estate

    def update_from_payload(self, payload, user_id: Optional[int] = None):
        for field in (
            "code",
            "name",
            "address",
            "city",
            "postal_code",
            "contact_name",
            "contact_phone",
            "contact_email",
            "total_units",
            "electricity_rate_table_id",
            "water_rate_table_id",
            "bulk_electricity_meter_id",
            "bulk_water_meter_id",
            "electricity_markup_percentage",
            "water_markup_percentage",
            "solar_free_allocation_kwh",
            "is_active",
        ):
            if field in payload:
                setattr(self, field, payload[field])
        if user_id is not None:
            self.updated_by = user_id
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def count_all() -> int:
        return Estate.query.count()

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
