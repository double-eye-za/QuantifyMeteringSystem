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
    status: Optional[str]
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
    status = db.Column(db.String(20), default="active")
    is_active = db.Column(db.Boolean, default=True)
    app_user_id = db.Column(db.String(36))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

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
            "status": self.status,
            "is_active": self.is_active,
            "app_user_id": self.app_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
