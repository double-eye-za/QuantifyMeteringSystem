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

    @staticmethod
    def get_all(
        estate_id: Optional[int] = None,
        occupancy_status: Optional[str] = None,
        search: Optional[str] = None,
    ):
        query = Unit.query
        if estate_id is not None:
            query = query.filter(Unit.estate_id == estate_id)
        if occupancy_status is not None:
            query = query.filter(Unit.occupancy_status == occupancy_status)
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(Unit.unit_number.ilike(like), Unit.building.ilike(like))
            )
        return query

    @staticmethod
    def get_by_id(unit_id):
        return Unit.query.get(unit_id)

    @staticmethod
    def create_from_payload(payload, user_id: Optional[int] = None):
        from .estate import Estate

        resident_id_val = payload.get("resident_id")
        occupancy = payload.get("occupancy_status")
        if occupancy is None and resident_id_val:
            occupancy = "occupied"

        estate = Estate.get_by_id(payload["estate_id"])

        unit = Unit(
            estate_id=payload["estate_id"],
            unit_number=payload["unit_number"],
            floor=payload.get("floor"),
            building=payload.get("building"),
            bedrooms=payload.get("bedrooms"),
            bathrooms=payload.get("bathrooms"),
            size_sqm=payload.get("size_sqm"),
            occupancy_status=occupancy or "vacant",
            resident_id=resident_id_val,
            electricity_meter_id=payload.get("electricity_meter_id"),
            water_meter_id=payload.get("water_meter_id"),
            solar_meter_id=payload.get("solar_meter_id"),
            hot_water_meter_id=payload.get("hot_water_meter_id"),
            electricity_rate_table_id=payload.get("electricity_rate_table_id")
            or (estate.electricity_rate_table_id if estate else None),
            water_rate_table_id=payload.get("water_rate_table_id")
            or (estate.water_rate_table_id if estate else None),
            is_active=payload.get("is_active", True),
            created_by=user_id,
        )
        db.session.add(unit)
        db.session.commit()
        return unit

    def update_from_payload(self, payload, user_id: Optional[int] = None):
        for field in (
            "estate_id",
            "unit_number",
            "floor",
            "building",
            "bedrooms",
            "bathrooms",
            "size_sqm",
            "occupancy_status",
            "resident_id",
            "electricity_meter_id",
            "water_meter_id",
            "solar_meter_id",
            "hot_water_meter_id",
            "electricity_rate_table_id",
            "water_rate_table_id",
            "is_active",
        ):
            if field in payload:
                setattr(self, field, payload[field])
        if user_id is not None:
            self.updated_by = user_id
        db.session.commit()
        return self

    def delete(self) -> None:
        from ..db import db

        db.session.delete(self)
        db.session.commit()

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

    @staticmethod
    def count_all() -> int:
        return Unit.query.count()

    @staticmethod
    def find_by_meter_id(meter_id: int):
        """Return the unit that has the given meter_id assigned to any meter FK."""
        if not meter_id:
            return None
        return Unit.query.filter(
            or_(
                Unit.electricity_meter_id == meter_id,
                Unit.water_meter_id == meter_id,
                Unit.solar_meter_id == meter_id,
                Unit.hot_water_meter_id == meter_id,
            )
        ).first()
