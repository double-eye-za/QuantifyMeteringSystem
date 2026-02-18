from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import CheckConstraint, UniqueConstraint, or_
from ..db import db

if TYPE_CHECKING:
    from .person import Person
    from .unit_ownership import UnitOwnership
    from .unit_tenancy import UnitTenancy


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

    # Relationships
    wallet = db.relationship(
        "Wallet",
        uselist=False,
        backref="unit",
        primaryjoin="Unit.id==Wallet.unit_id",
    )
    ownerships = db.relationship(
        "UnitOwnership",
        back_populates="unit",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    tenancies = db.relationship(
        "UnitTenancy",
        back_populates="unit",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

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

    @property
    def owners(self) -> List[Person]:
        """Get all persons who own this unit"""
        return [ownership.person for ownership in self.ownerships]

    @property
    def tenants(self) -> List[Person]:
        """Get all active tenants of this unit"""
        return [
            tenancy.person
            for tenancy in self.tenancies
            if tenancy.status == "active" and not tenancy.move_out_date
        ]

    @property
    def all_tenants(self) -> List[Person]:
        """Get all tenants (including inactive) of this unit"""
        return [tenancy.person for tenancy in self.tenancies]

    @property
    def primary_owner(self) -> Optional[Person]:
        """Get the primary owner of this unit"""
        for ownership in self.ownerships:
            if ownership.is_primary_owner:
                return ownership.person
        # If no primary owner set, return first owner
        return self.owners[0] if self.owners else None

    @property
    def primary_tenant(self) -> Optional[Person]:
        """Get the primary active tenant of this unit"""
        for tenancy in self.tenancies:
            if tenancy.is_primary_tenant and tenancy.status == "active" and not tenancy.move_out_date:
                return tenancy.person
        # If no primary tenant set, return first active tenant
        return self.tenants[0] if self.tenants else None

    @property
    def residents(self) -> List[Person]:
        """
        Get all current residents (tenants).
        Alias for backward compatibility.
        """
        return self.tenants

    @property
    def resident(self) -> Optional[Person]:
        """
        Get the primary tenant.
        Alias for backward compatibility with old code that expects single resident.
        """
        return self.primary_tenant

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
            # Person relationships
            "owners": [
                {
                    "id": owner.id,
                    "first_name": owner.first_name,
                    "last_name": owner.last_name,
                    "email": owner.email,
                    "phone": owner.phone,
                }
                for owner in self.owners
            ],
            "tenants": [
                {
                    "id": tenant.id,
                    "first_name": tenant.first_name,
                    "last_name": tenant.last_name,
                    "email": tenant.email,
                    "phone": tenant.phone,
                }
                for tenant in self.tenants
            ],
            # Backward compatibility: single resident (primary tenant)
            "resident_id": self.primary_tenant.id if self.primary_tenant else None,
            "resident": {
                "id": self.primary_tenant.id,
                "first_name": self.primary_tenant.first_name,
                "last_name": self.primary_tenant.last_name,
                "phone": self.primary_tenant.phone,
            }
            if self.primary_tenant
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
