from __future__ import annotations

from typing import Optional

from sqlalchemy import or_

from app.db import db
from app.models import Resident, Unit


def list_residents(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    unit_id: Optional[int] = None,
):
    query = Resident.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Resident.first_name.ilike(like),
                Resident.last_name.ilike(like),
                Resident.email.ilike(like),
                Resident.phone.ilike(like),
                Resident.id_number.ilike(like),
            )
        )
    if is_active is not None:
        query = query.filter(Resident.is_active == is_active)
    if unit_id is not None:
        query = query.join(Unit, Resident.id == Unit.resident_id).filter(
            Unit.id == unit_id
        )
    return query.order_by(Resident.first_name.asc(), Resident.last_name.asc())


def list_residents_for_dropdown():
    return list_residents().all()


def get_resident_by_id(resident_id: int):
    return Resident.query.get(resident_id)


def create_resident(payload: dict, user_id: Optional[int] = None):
    status = (payload.get("status") or "active").lower()
    is_active = payload.get("is_active")
    if is_active is None:
        is_active = False if status == "vacated" else True
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
        status=status,
        is_active=is_active,
        app_user_id=payload.get("app_user_id"),
        created_by=user_id,
    )
    db.session.add(r)
    db.session.commit()
    return r


def update_resident(
    resident: Resident, payload: dict, user_id: Optional[int] = None
):
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
        "status",
        "is_active",
        "app_user_id",
    ):
        if field in payload:
            setattr(resident, field, payload[field])
    if "status" in payload and "is_active" not in payload:
        resident.is_active = (
            False if (payload.get("status") or "").lower() == "vacated" else True
        )
    if user_id is not None:
        resident.updated_by = user_id
    db.session.commit()
    return resident


def delete_resident(resident: Resident):
    assigned_unit = Unit.query.filter_by(resident_id=resident.id).first()
    if assigned_unit:
        return False, {
            "code": 409,
            "message": "Resident is assigned to a unit and cannot be deleted. Unassign the resident first.",
            "unit_id": assigned_unit.id,
        }
    db.session.delete(resident)
    db.session.commit()
    return True, None
