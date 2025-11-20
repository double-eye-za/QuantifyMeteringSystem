from __future__ import annotations

from typing import Optional, List, Tuple, Dict
from datetime import date, datetime

from app.db import db
from app.models import UnitTenancy, Person, Unit


def get_unit_tenants(
    unit_id: int,
    active_only: bool = False,
    include_moved_out: bool = False
) -> List[UnitTenancy]:
    """
    Get all tenants for a specific unit.

    Args:
        unit_id: ID of the unit
        active_only: Only return active tenancies
        include_moved_out: Include tenants who have moved out

    Returns:
        List of UnitTenancy records
    """
    query = UnitTenancy.query.filter_by(unit_id=unit_id)

    if active_only:
        query = query.filter(UnitTenancy.status == "active")
        if not include_moved_out:
            query = query.filter(UnitTenancy.move_out_date.is_(None))

    return query.order_by(
        UnitTenancy.is_primary_tenant.desc(),
        UnitTenancy.move_in_date.asc()
    ).all()


def get_person_tenancies(
    person_id: int,
    active_only: bool = False
) -> List[UnitTenancy]:
    """
    Get all tenancy records for a specific person.

    Args:
        person_id: ID of the person
        active_only: Only return active tenancies

    Returns:
        List of UnitTenancy records
    """
    query = UnitTenancy.query.filter_by(person_id=person_id)

    if active_only:
        query = query.filter(UnitTenancy.status == "active")

    return query.order_by(
        UnitTenancy.is_primary_tenant.desc(),
        UnitTenancy.created_at.desc()
    ).all()


def get_tenancy(unit_id: int, person_id: int) -> Optional[UnitTenancy]:
    """
    Get a specific tenancy record.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person

    Returns:
        UnitTenancy record or None
    """
    return UnitTenancy.query.filter_by(
        unit_id=unit_id,
        person_id=person_id
    ).first()


def add_tenant(
    unit_id: int,
    person_id: int,
    is_primary_tenant: bool = False,
    lease_start_date: Optional[date] = None,
    lease_end_date: Optional[date] = None,
    monthly_rent: Optional[float] = None,
    deposit_amount: Optional[float] = None,
    move_in_date: Optional[date] = None,
    status: str = "active",
    notes: Optional[str] = None,
) -> Tuple[bool, UnitTenancy | Dict]:
    """
    Add a tenant to a unit.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person
        is_primary_tenant: Whether this is the primary tenant
        lease_start_date: Lease start date
        lease_end_date: Lease end date
        monthly_rent: Monthly rent amount
        deposit_amount: Security deposit amount
        move_in_date: Actual move-in date
        status: Tenancy status (active, expired, terminated)
        notes: Additional notes

    Returns:
        Tuple of (success: bool, tenancy_record or error_dict)
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

    # Check if tenancy already exists
    existing = get_tenancy(unit_id, person_id)
    if existing:
        return False, {
            "code": 409,
            "message": f"{person.full_name} is already a tenant of this unit. Update the existing tenancy instead."
        }

    # Validate status
    valid_statuses = ["active", "expired", "terminated"]
    if status not in valid_statuses:
        return False, {
            "code": 400,
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        }

    # If this is the first tenant, make them primary automatically
    existing_tenants = get_unit_tenants(unit_id, active_only=True)
    if not existing_tenants:
        is_primary_tenant = True

    # If setting as primary tenant, unset other primary tenants
    if is_primary_tenant:
        for tenant in existing_tenants:
            if tenant.is_primary_tenant:
                tenant.is_primary_tenant = False

    # Create tenancy record
    tenancy = UnitTenancy(
        unit_id=unit_id,
        person_id=person_id,
        is_primary_tenant=is_primary_tenant,
        lease_start_date=lease_start_date,
        lease_end_date=lease_end_date,
        monthly_rent=monthly_rent,
        deposit_amount=deposit_amount,
        move_in_date=move_in_date or date.today(),
        status=status,
        notes=notes,
    )

    db.session.add(tenancy)
    db.session.commit()
    return True, tenancy


def update_tenancy(
    tenancy: UnitTenancy,
    is_primary_tenant: Optional[bool] = None,
    lease_start_date: Optional[date] = None,
    lease_end_date: Optional[date] = None,
    monthly_rent: Optional[float] = None,
    deposit_amount: Optional[float] = None,
    move_in_date: Optional[date] = None,
    move_out_date: Optional[date] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None,
) -> Tuple[bool, UnitTenancy | Dict]:
    """
    Update an existing tenancy record.

    Args:
        tenancy: UnitTenancy object to update
        is_primary_tenant: New primary tenant status
        lease_start_date: New lease start date
        lease_end_date: New lease end date
        monthly_rent: New monthly rent
        deposit_amount: New deposit amount
        move_in_date: New move-in date
        move_out_date: New move-out date
        status: New status
        notes: New notes

    Returns:
        Tuple of (success: bool, tenancy_record or error_dict)
    """
    # Validate status if provided
    if status is not None:
        valid_statuses = ["active", "expired", "terminated"]
        if status not in valid_statuses:
            return False, {
                "code": 400,
                "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }
        tenancy.status = status

    # Handle primary tenant change
    if is_primary_tenant is not None:
        if is_primary_tenant:
            # Unset other primary tenants for this unit
            for other_tenancy in get_unit_tenants(tenancy.unit_id, active_only=True):
                if other_tenancy.id != tenancy.id and other_tenancy.is_primary_tenant:
                    other_tenancy.is_primary_tenant = False

        tenancy.is_primary_tenant = is_primary_tenant

    # Update other fields
    if lease_start_date is not None:
        tenancy.lease_start_date = lease_start_date
    if lease_end_date is not None:
        tenancy.lease_end_date = lease_end_date
    if monthly_rent is not None:
        tenancy.monthly_rent = monthly_rent
    if deposit_amount is not None:
        tenancy.deposit_amount = deposit_amount
    if move_in_date is not None:
        tenancy.move_in_date = move_in_date
    if move_out_date is not None:
        tenancy.move_out_date = move_out_date
    if notes is not None:
        tenancy.notes = notes

    db.session.commit()
    return True, tenancy


def remove_tenant(unit_id: int, person_id: int) -> Tuple[bool, Optional[Dict]]:
    """
    Remove a tenant from a unit (delete the tenancy record).

    WARNING: This permanently deletes the tenancy record.
    Consider using terminate_tenancy() instead to preserve history.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person

    Returns:
        Tuple of (success: bool, error_dict or None)
    """
    tenancy = get_tenancy(unit_id, person_id)
    if not tenancy:
        return False, {
            "code": 404,
            "message": "Tenancy record not found"
        }

    db.session.delete(tenancy)
    db.session.commit()
    return True, None


def terminate_tenancy(
    unit_id: int,
    person_id: int,
    move_out_date: Optional[date] = None,
    termination_reason: Optional[str] = None
) -> Tuple[bool, UnitTenancy | Dict]:
    """
    Terminate a tenancy (sets status to terminated, preserves history).

    Args:
        unit_id: ID of the unit
        person_id: ID of the person
        move_out_date: Date tenant moved out (defaults to today)
        termination_reason: Reason for termination (stored in notes)

    Returns:
        Tuple of (success: bool, tenancy_record or error_dict)
    """
    tenancy = get_tenancy(unit_id, person_id)
    if not tenancy:
        return False, {
            "code": 404,
            "message": "Tenancy record not found"
        }

    if tenancy.status == "terminated":
        return False, {
            "code": 400,
            "message": "Tenancy is already terminated"
        }

    tenancy.status = "terminated"
    tenancy.move_out_date = move_out_date or date.today()

    if termination_reason:
        existing_notes = tenancy.notes or ""
        termination_note = f"Terminated: {termination_reason}"
        tenancy.notes = f"{existing_notes}\n{termination_note}".strip()

    # If this was the primary tenant, check if there are other active tenants
    # and promote one to primary
    if tenancy.is_primary_tenant:
        tenancy.is_primary_tenant = False
        remaining_tenants = get_unit_tenants(unit_id, active_only=True)
        if remaining_tenants:
            # Promote the tenant who moved in first
            remaining_tenants[0].is_primary_tenant = True

    db.session.commit()
    return True, tenancy


def set_primary_tenant(unit_id: int, person_id: int) -> Tuple[bool, UnitTenancy | Dict]:
    """
    Set a person as the primary tenant of a unit.

    Args:
        unit_id: ID of the unit
        person_id: ID of the person

    Returns:
        Tuple of (success: bool, tenancy_record or error_dict)
    """
    tenancy = get_tenancy(unit_id, person_id)
    if not tenancy:
        return False, {
            "code": 404,
            "message": "Tenancy record not found"
        }

    if tenancy.status != "active":
        return False, {
            "code": 400,
            "message": "Only active tenants can be set as primary"
        }

    # Unset other primary tenants
    for other_tenancy in get_unit_tenants(unit_id, active_only=True):
        if other_tenancy.id != tenancy.id and other_tenancy.is_primary_tenant:
            other_tenancy.is_primary_tenant = False

    tenancy.is_primary_tenant = True
    db.session.commit()
    return True, tenancy


def get_active_tenancies_count(person_id: int) -> int:
    """
    Get count of active tenancies for a person.

    Args:
        person_id: ID of the person

    Returns:
        Count of active tenancies
    """
    return UnitTenancy.query.filter_by(
        person_id=person_id,
        status="active"
    ).filter(UnitTenancy.move_out_date.is_(None)).count()
