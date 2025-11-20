from __future__ import annotations

from typing import Optional, List, Tuple, Dict
from decimal import Decimal

from sqlalchemy import func

from app.db import db
from app.models import UnitOwnership, Person, Unit


def get_unit_owners(unit_id: int) -> List[UnitOwnership]:
    """
    Get all owners for a specific unit.

    Args:
        unit_id: ID of the unit

    Returns:
        List of UnitOwnership records
    """
    return UnitOwnership.query.filter_by(unit_id=unit_id).order_by(
        UnitOwnership.is_primary_owner.desc(),
        UnitOwnership.ownership_percentage.desc()
    ).all()


def get_person_ownerships(person_id: int) -> List[UnitOwnership]:
    """
    Get all units owned by a specific person.

    Args:
        person_id: ID of the person

    Returns:
        List of UnitOwnership records
    """
    return UnitOwnership.query.filter_by(person_id=person_id).order_by(
        UnitOwnership.is_primary_owner.desc(),
        UnitOwnership.created_at.asc()
    ).all()


def get_ownership(unit_id: int, person_id: int) -> Optional[UnitOwnership]:
    """
    Get a specific ownership record.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person

    Returns:
        UnitOwnership record or None
    """
    return UnitOwnership.query.filter_by(
        unit_id=unit_id,
        person_id=person_id
    ).first()


def calculate_total_ownership(unit_id: int, exclude_person_id: Optional[int] = None) -> Decimal:
    """
    Calculate total ownership percentage for a unit.

    Args:
        unit_id: ID of the unit
        exclude_person_id: Optional person ID to exclude from calculation

    Returns:
        Total ownership percentage as Decimal
    """
    query = db.session.query(
        func.sum(UnitOwnership.ownership_percentage)
    ).filter(UnitOwnership.unit_id == unit_id)

    if exclude_person_id is not None:
        query = query.filter(UnitOwnership.person_id != exclude_person_id)

    result = query.scalar()
    return Decimal(result) if result else Decimal("0.00")


def add_owner(
    unit_id: int,
    person_id: int,
    ownership_percentage: float = 100.0,
    is_primary_owner: bool = False,
    purchase_date: Optional[str] = None,
    purchase_price: Optional[float] = None,
    notes: Optional[str] = None,
) -> Tuple[bool, UnitOwnership | Dict]:
    """
    Add an owner to a unit.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person
        ownership_percentage: Percentage of ownership (0-100)
        is_primary_owner: Whether this is the primary owner
        purchase_date: Date of purchase
        purchase_price: Purchase price
        notes: Additional notes

    Returns:
        Tuple of (success: bool, ownership_record or error_dict)
    """
    # Validate unit exists
    unit = Unit.query.get(unit_id)
    if not unit:
        return False, {
            "code": 404,
            "message": f"Unit with ID {unit_id} not found"
        }

    # Validate person exists
    person = Person.query.get(person_id)
    if not person:
        return False, {
            "code": 404,
            "message": f"Person with ID {person_id} not found"
        }

    # Check if ownership already exists
    existing = get_ownership(unit_id, person_id)
    if existing:
        return False, {
            "code": 409,
            "message": f"{person.full_name} already owns this unit. Update the existing ownership instead."
        }

    # Validate ownership percentage
    ownership_percentage = Decimal(str(ownership_percentage))
    if ownership_percentage < 0 or ownership_percentage > 100:
        return False, {
            "code": 400,
            "message": "Ownership percentage must be between 0 and 100"
        }

    # Check if total ownership would exceed 100%
    current_total = calculate_total_ownership(unit_id)
    new_total = current_total + ownership_percentage
    if new_total > 100:
        return False, {
            "code": 400,
            "message": f"Total ownership would exceed 100% (current: {current_total}%, adding: {ownership_percentage}%)"
        }

    # If this is the first owner, make them primary automatically
    existing_owners = get_unit_owners(unit_id)
    if not existing_owners:
        is_primary_owner = True

    # If setting as primary owner, unset other primary owners
    if is_primary_owner:
        for owner in existing_owners:
            if owner.is_primary_owner:
                owner.is_primary_owner = False

    # Create ownership record
    ownership = UnitOwnership(
        unit_id=unit_id,
        person_id=person_id,
        ownership_percentage=ownership_percentage,
        is_primary_owner=is_primary_owner,
        purchase_date=purchase_date,
        purchase_price=purchase_price,
        notes=notes,
    )

    db.session.add(ownership)
    db.session.commit()
    return True, ownership


def update_ownership(
    ownership: UnitOwnership,
    ownership_percentage: Optional[float] = None,
    is_primary_owner: Optional[bool] = None,
    purchase_date: Optional[str] = None,
    purchase_price: Optional[float] = None,
    notes: Optional[str] = None,
) -> Tuple[bool, UnitOwnership | Dict]:
    """
    Update an existing ownership record.

    Args:
        ownership: UnitOwnership object to update
        ownership_percentage: New ownership percentage
        is_primary_owner: New primary owner status
        purchase_date: New purchase date
        purchase_price: New purchase price
        notes: New notes

    Returns:
        Tuple of (success: bool, ownership_record or error_dict)
    """
    # Validate ownership percentage if provided
    if ownership_percentage is not None:
        ownership_percentage = Decimal(str(ownership_percentage))
        if ownership_percentage < 0 or ownership_percentage > 100:
            return False, {
                "code": 400,
                "message": "Ownership percentage must be between 0 and 100"
            }

        # Check if total ownership would exceed 100%
        current_total = calculate_total_ownership(
            ownership.unit_id,
            exclude_person_id=ownership.person_id
        )
        new_total = current_total + ownership_percentage
        if new_total > 100:
            return False, {
                "code": 400,
                "message": f"Total ownership would exceed 100% (other owners: {current_total}%, new: {ownership_percentage}%)"
            }

        ownership.ownership_percentage = ownership_percentage

    # Handle primary owner change
    if is_primary_owner is not None:
        if is_primary_owner:
            # Unset other primary owners for this unit
            for other_ownership in get_unit_owners(ownership.unit_id):
                if other_ownership.id != ownership.id and other_ownership.is_primary_owner:
                    other_ownership.is_primary_owner = False

        ownership.is_primary_owner = is_primary_owner

    # Update other fields
    if purchase_date is not None:
        ownership.purchase_date = purchase_date
    if purchase_price is not None:
        ownership.purchase_price = purchase_price
    if notes is not None:
        ownership.notes = notes

    db.session.commit()
    return True, ownership


def remove_owner(unit_id: int, person_id: int) -> Tuple[bool, Optional[Dict]]:
    """
    Remove an owner from a unit.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person

    Returns:
        Tuple of (success: bool, error_dict or None)
    """
    ownership = get_ownership(unit_id, person_id)
    if not ownership:
        return False, {
            "code": 404,
            "message": "Ownership record not found"
        }

    db.session.delete(ownership)
    db.session.commit()
    return True, None


def set_primary_owner(unit_id: int, person_id: int) -> Tuple[bool, UnitOwnership | Dict]:
    """
    Set a person as the primary owner of a unit.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person

    Returns:
        Tuple of (success: bool, ownership_record or error_dict)
    """
    ownership = get_ownership(unit_id, person_id)
    if not ownership:
        return False, {
            "code": 404,
            "message": "Ownership record not found"
        }

    # Unset other primary owners
    for other_ownership in get_unit_owners(unit_id):
        if other_ownership.id != ownership.id and other_ownership.is_primary_owner:
            other_ownership.is_primary_owner = False

    ownership.is_primary_owner = True
    db.session.commit()
    return True, ownership
