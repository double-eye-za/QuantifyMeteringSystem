from __future__ import annotations

from typing import Optional, Tuple, Dict

from sqlalchemy import or_

from app.db import db
from app.models import Person, UnitOwnership, UnitTenancy


def list_persons(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    unit_id: Optional[int] = None,
    is_owner: Optional[bool] = None,
    is_tenant: Optional[bool] = None,
):
    """
    List persons with optional filters.

    Args:
        search: Search term for name, email, phone, or ID number
        is_active: Filter by active status
        unit_id: Filter by associated unit (owner or tenant)
        is_owner: Filter to only owners
        is_tenant: Filter to only tenants

    Returns:
        SQLAlchemy query object
    """
    query = Person.query

    # Text search
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Person.first_name.ilike(like),
                Person.last_name.ilike(like),
                Person.email.ilike(like),
                Person.phone.ilike(like),
                Person.id_number.ilike(like),
            )
        )

    # Active status filter
    if is_active is not None:
        query = query.filter(Person.is_active == is_active)

    # Unit association filter
    if unit_id is not None:
        # Person associated with unit as owner OR tenant
        owner_ids = db.session.query(UnitOwnership.person_id).filter(
            UnitOwnership.unit_id == unit_id
        )
        tenant_ids = db.session.query(UnitTenancy.person_id).filter(
            UnitTenancy.unit_id == unit_id
        )
        query = query.filter(
            or_(Person.id.in_(owner_ids), Person.id.in_(tenant_ids))
        )

    # Owner filter
    if is_owner is True:
        owner_ids = db.session.query(UnitOwnership.person_id).distinct()
        query = query.filter(Person.id.in_(owner_ids))

    # Tenant filter
    if is_tenant is True:
        tenant_ids = db.session.query(UnitTenancy.person_id).distinct()
        query = query.filter(Person.id.in_(tenant_ids))

    return query.order_by(Person.first_name.asc(), Person.last_name.asc())


def list_persons_for_dropdown():
    """Get all active persons for dropdown menus"""
    return list_persons(is_active=True).all()


def get_person_by_id(person_id: int) -> Optional[Person]:
    """Get a single person by ID"""
    return Person.query.get(person_id)


def get_person_by_email(email: str) -> Optional[Person]:
    """Get a person by email address"""
    return Person.query.filter_by(email=email).first()


def get_person_by_app_user_id(app_user_id: str) -> Optional[Person]:
    """Get a person by app_user_id (for mobile authentication)"""
    return Person.query.filter_by(app_user_id=app_user_id).first()


def create_person(payload: dict, user_id: Optional[int] = None) -> Person:
    """
    Create a new person.

    Args:
        payload: Dictionary containing person data
        user_id: ID of the user creating the person

    Returns:
        Created Person object
    """
    person = Person(
        id_number=payload.get("id_number"),
        first_name=payload["first_name"],
        last_name=payload["last_name"],
        email=payload["email"],
        phone=payload["phone"],
        alternate_phone=payload.get("alternate_phone"),
        emergency_contact_name=payload.get("emergency_contact_name"),
        emergency_contact_phone=payload.get("emergency_contact_phone"),
        is_active=payload.get("is_active", True),
        app_user_id=payload.get("app_user_id"),
        password_hash=payload.get("password_hash"),  # For mobile authentication
        profile_photo_url=payload.get("profile_photo_url"),
        created_by=user_id,
    )
    db.session.add(person)
    db.session.commit()
    return person


def update_person(
    person: Person, payload: dict, user_id: Optional[int] = None
) -> Person:
    """
    Update an existing person.

    Args:
        person: Person object to update
        payload: Dictionary containing updated data
        user_id: ID of the user making the update

    Returns:
        Updated Person object
    """
    updatable_fields = (
        "id_number",
        "first_name",
        "last_name",
        "email",
        "phone",
        "alternate_phone",
        "emergency_contact_name",
        "emergency_contact_phone",
        "is_active",
        "app_user_id",
        "password_hash",
        "profile_photo_url",
    )

    for field in updatable_fields:
        if field in payload:
            setattr(person, field, payload[field])

    if user_id is not None:
        person.updated_by = user_id

    db.session.commit()
    return person


def delete_person(person: Person) -> Tuple[bool, Optional[Dict]]:
    """
    Delete a person if they have no active unit associations.

    Args:
        person: Person object to delete

    Returns:
        Tuple of (success: bool, error_info: dict or None)
    """
    # Check if person owns any units
    ownership_count = UnitOwnership.query.filter_by(person_id=person.id).count()
    if ownership_count > 0:
        return False, {
            "code": 409,
            "message": f"Person owns {ownership_count} unit(s) and cannot be deleted. Remove ownership records first.",
            "ownership_count": ownership_count,
        }

    # Check if person has any tenancy records (active or historical)
    tenancy_count = UnitTenancy.query.filter_by(person_id=person.id).count()
    if tenancy_count > 0:
        return False, {
            "code": 409,
            "message": f"Person has {tenancy_count} tenancy record(s) and cannot be deleted. Remove tenancy records first.",
            "tenancy_count": tenancy_count,
        }

    # Safe to delete
    db.session.delete(person)
    db.session.commit()
    return True, None


def can_person_be_deleted(person: Person) -> Tuple[bool, Optional[str]]:
    """
    Check if a person can be deleted without actually deleting.

    Args:
        person: Person object to check

    Returns:
        Tuple of (can_delete: bool, reason: str or None)
    """
    ownership_count = UnitOwnership.query.filter_by(person_id=person.id).count()
    if ownership_count > 0:
        return False, f"Person owns {ownership_count} unit(s)"

    tenancy_count = UnitTenancy.query.filter_by(person_id=person.id).count()
    if tenancy_count > 0:
        return False, f"Person has {tenancy_count} tenancy record(s)"

    return True, None
