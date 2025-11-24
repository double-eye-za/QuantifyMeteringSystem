"""Service layer for mobile user management."""
from __future__ import annotations

from typing import Optional, List, Tuple, Dict
from datetime import datetime

from app.db import db
from app.models import MobileUser, Person, UnitOwnership, UnitTenancy
from app.utils.password_generator import (
    generate_temporary_password,
    validate_password_strength,
    validate_phone_number
)


def get_mobile_user_by_phone(phone_number: str) -> Optional[MobileUser]:
    """
    Get a mobile user by phone number.

    Args:
        phone_number: Phone number to search for

    Returns:
        MobileUser if found, None otherwise
    """
    return MobileUser.query.filter_by(phone_number=phone_number).first()


def get_mobile_user_by_person_id(person_id: int) -> Optional[MobileUser]:
    """
    Get a mobile user by person ID.

    Args:
        person_id: Person ID to search for

    Returns:
        MobileUser if found, None otherwise
    """
    return MobileUser.query.filter_by(person_id=person_id).first()


def get_mobile_user_by_id(user_id: int) -> Optional[MobileUser]:
    """
    Get a mobile user by ID.

    Args:
        user_id: User ID to search for

    Returns:
        MobileUser if found, None otherwise
    """
    return MobileUser.query.get(user_id)


def create_mobile_user(
    person_id: int,
    send_sms: bool = True
) -> Tuple[bool, MobileUser | Dict]:
    """
    Create a new mobile user account for a person.

    Generates a temporary password and optionally sends it via SMS.

    Args:
        person_id: ID of the person to create account for
        send_sms: Whether to send welcome SMS with password (default: True)

    Returns:
        Tuple of (success: bool, mobile_user or error_dict)
        On success, also returns the temporary password in the dict

    Example:
        >>> success, result = create_mobile_user(person_id=5)
        >>> if success:
        ...     print(f"User created: {result['user'].phone_number}")
        ...     print(f"Temp password: {result['temp_password']}")
    """
    # Validate person exists
    person = Person.query.get(person_id)
    if not person:
        return False, {
            "code": 404,
            "message": f"Person with ID {person_id} not found"
        }

    # Validate person has phone number
    if not person.phone:
        return False, {
            "code": 400,
            "message": "Person must have a phone number to create mobile account"
        }

    # Validate and normalize phone number
    is_valid, normalized_phone = validate_phone_number(person.phone)
    if not is_valid:
        return False, {
            "code": 400,
            "message": f"Invalid phone number format: {person.phone}"
        }

    # Check if mobile user already exists for this person
    existing = get_mobile_user_by_person_id(person_id)
    if existing:
        return False, {
            "code": 409,
            "message": "Mobile user account already exists for this person"
        }

    # Check if phone number is already in use
    existing_phone = get_mobile_user_by_phone(normalized_phone)
    if existing_phone:
        return False, {
            "code": 409,
            "message": "This phone number is already registered to another mobile user"
        }

    # Generate temporary password
    temp_password = generate_temporary_password()

    # Create mobile user
    mobile_user = MobileUser(
        person_id=person_id,
        phone_number=normalized_phone,
        password_hash="",  # Will be set by set_temporary_password
    )

    mobile_user.set_temporary_password(temp_password)

    db.session.add(mobile_user)
    db.session.commit()

    # TODO: Send SMS in Phase 2
    if send_sms:
        # from app.services.sms_service import send_welcome_sms
        # send_welcome_sms(normalized_phone, temp_password)
        pass

    return True, {
        "user": mobile_user,
        "temp_password": temp_password,  # Return so caller can send SMS if needed
        "person": person
    }


def authenticate_mobile_user(
    phone_number: str,
    password: str
) -> Tuple[bool, MobileUser | Dict]:
    """
    Authenticate a mobile user with phone number and password.

    Args:
        phone_number: User's phone number
        password: User's password (can be temp or permanent)

    Returns:
        Tuple of (success: bool, mobile_user or error_dict)
    """
    # Validate phone format
    is_valid, normalized_phone = validate_phone_number(phone_number)
    if not is_valid:
        return False, {
            "code": 400,
            "message": "Invalid phone number format"
        }

    # Find user
    mobile_user = get_mobile_user_by_phone(normalized_phone)
    if not mobile_user:
        return False, {
            "code": 401,
            "message": "Invalid phone number or password"
        }

    # Check if account is active
    if not mobile_user.is_active:
        return False, {
            "code": 403,
            "message": "Account is inactive. Please contact support."
        }

    # Check password
    if not mobile_user.check_password(password):
        return False, {
            "code": 401,
            "message": "Invalid phone number or password"
        }

    # Update last login
    mobile_user.update_last_login()
    db.session.commit()

    return True, mobile_user


def change_password(
    mobile_user: MobileUser,
    new_password: str,
    current_password: Optional[str] = None
) -> Tuple[bool, Dict]:
    """
    Change a mobile user's password.

    Args:
        mobile_user: MobileUser object
        new_password: New password to set
        current_password: Current password (optional, for verification)

    Returns:
        Tuple of (success: bool, result_dict)
    """
    # Validate new password strength
    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        return False, {
            "code": 400,
            "message": error_message
        }

    # If current password provided, verify it
    if current_password:
        if not mobile_user.check_password(current_password):
            return False, {
                "code": 401,
                "message": "Current password is incorrect"
            }

    # Set new password (clears temp password and password_must_change flag)
    mobile_user.set_password(new_password)
    db.session.commit()

    return True, {
        "message": "Password changed successfully"
    }


def get_user_units(person_id: int) -> List[Dict]:
    """
    Get all units that a person owns or rents.

    Args:
        person_id: ID of the person

    Returns:
        List of unit dictionaries with role information
    """
    units = []

    # Get owned units
    ownerships = UnitOwnership.query.filter_by(person_id=person_id).all()
    for ownership in ownerships:
        units.append({
            'unit_id': ownership.unit_id,
            'unit_number': ownership.unit.unit_number,
            'estate_id': ownership.unit.estate_id,
            'estate_name': ownership.unit.estate.name if ownership.unit.estate else None,
            'role': 'owner',
            'is_primary': ownership.is_primary_owner,
            'ownership_percentage': float(ownership.ownership_percentage) if ownership.ownership_percentage else None,
        })

    # Get rented units (active tenancies only)
    tenancies = UnitTenancy.query.filter_by(
        person_id=person_id,
        status='active'
    ).all()
    for tenancy in tenancies:
        units.append({
            'unit_id': tenancy.unit_id,
            'unit_number': tenancy.unit.unit_number,
            'estate_id': tenancy.unit.estate_id,
            'estate_name': tenancy.unit.estate.name if tenancy.unit.estate else None,
            'role': 'tenant',
            'is_primary': tenancy.is_primary_tenant,
            'monthly_rent': float(tenancy.monthly_rent) if tenancy.monthly_rent else None,
            'lease_start_date': tenancy.lease_start_date.isoformat() if tenancy.lease_start_date else None,
            'lease_end_date': tenancy.lease_end_date.isoformat() if tenancy.lease_end_date else None,
        })

    return units


def can_access_unit(person_id: int, unit_id: int) -> bool:
    """
    Check if a person has access to a unit (as owner or tenant).

    Args:
        person_id: ID of the person
        unit_id: ID of the unit

    Returns:
        True if person owns or rents the unit, False otherwise
    """
    # Check if person owns the unit
    ownership = UnitOwnership.query.filter_by(
        person_id=person_id,
        unit_id=unit_id
    ).first()
    if ownership:
        return True

    # Check if person rents the unit (active tenancy only)
    tenancy = UnitTenancy.query.filter_by(
        person_id=person_id,
        unit_id=unit_id,
        status='active'
    ).first()
    if tenancy:
        return True

    return False


def deactivate_mobile_user(mobile_user: MobileUser) -> Tuple[bool, Dict]:
    """
    Deactivate a mobile user account.

    Args:
        mobile_user: MobileUser object to deactivate

    Returns:
        Tuple of (success: bool, result_dict)
    """
    mobile_user.deactivate()
    db.session.commit()

    return True, {
        "message": "Mobile user account deactivated successfully"
    }


def activate_mobile_user(mobile_user: MobileUser) -> Tuple[bool, Dict]:
    """
    Activate a mobile user account.

    Args:
        mobile_user: MobileUser object to activate

    Returns:
        Tuple of (success: bool, result_dict)
    """
    mobile_user.activate()
    db.session.commit()

    return True, {
        "message": "Mobile user account activated successfully"
    }
