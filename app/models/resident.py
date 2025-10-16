from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from ..db import db


@dataclass
class Resident(db.Model):
    __tablename__ = "residents"

    id: Optional[int]
    id_number: Optional[str]
    first_name: str
    last_name: str
    email: str
    phone: str
    alternate_phone: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    lease_start_date: Optional[date]
    lease_end_date: Optional[date]
    is_active: Optional[bool]
    app_user_id: Optional[str]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    id_number = db.Column(db.String(20), unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    alternate_phone = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_phone = db.Column(db.String(20))
    lease_start_date = db.Column(db.Date)
    lease_end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    app_user_id = db.Column(db.String(36))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    @staticmethod
    def get_all(search: Optional[str] = None, is_active: Optional[bool] = None):
        query = Resident.query
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Resident.first_name.ilike(like),
                    Resident.last_name.ilike(like),
                    Resident.email.ilike(like),
                    Resident.phone.ilike(like),
                    Resident.id_number.ilike(like),
                )
            )
        if is_active is not None:
            query = query.filter(Resident.is_active == is_active)
        return query

    @staticmethod
    def get_by_id(resident_id: int):
        return Resident.query.get(resident_id)

    @staticmethod
    def create_from_payload(payload: dict, user_id: Optional[int] = None):
        r = Resident(
            id_number=payload.get("id_number"),
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            email=payload["email"],
            phone=payload["phone"],
            alternate_phone=payload.get("alternate_phone"),
            emergency_contact_name=payload.get("emergency_contact_name"),
            emergency_contact_phone=payload.get("emergency_contact_phone"),
            lease_start_date=payload.get("lease_start_date"),
            lease_end_date=payload.get("lease_end_date"),
            is_active=payload.get("is_active", True),
            app_user_id=payload.get("app_user_id"),
            created_by=user_id,
        )
        db.session.add(r)
        db.session.commit()
        return r

    def update_from_payload(self, payload: dict, user_id: Optional[int] = None):
        for field in (
            "id_number",
            "first_name",
            "last_name",
            "email",
            "phone",
            "alternate_phone",
            "emergency_contact_name",
            "emergency_contact_phone",
            "lease_start_date",
            "lease_end_date",
            "is_active",
            "app_user_id",
        ):
            if field in payload:
                setattr(self, field, payload[field])
        if user_id is not None:
            self.updated_by = user_id
        db.session.commit()
        return self

    def to_dict(self):
        return {
            "id": self.id,
            "id_number": self.id_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "alternate_phone": self.alternate_phone,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "lease_start_date": self.lease_start_date.isoformat()
            if self.lease_start_date
            else None,
            "lease_end_date": self.lease_end_date.isoformat()
            if self.lease_end_date
            else None,
            "is_active": self.is_active,
            "app_user_id": self.app_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def delete(self):
        """Delete resident if not assigned to a unit.
        Returns (True, None) on success, or (False, details) with details including code/unit_id.
        """
        from .unit import Unit
        from ..db import db

        assigned_unit = Unit.query.filter_by(resident_id=self.id).first()
        if assigned_unit:
            return False, {
                "code": 409,
                "message": "Resident is assigned to a unit and cannot be deleted. Unassign the resident first.",
                "unit_id": assigned_unit.id,
            }

        db.session.delete(self)
        db.session.commit()
        return True, None
