"""Service layer for mobile invite management."""
from __future__ import annotations

from typing import Optional, List, Tuple, Dict
from datetime import datetime

from app.db import db
from app.models import MobileInvite, MobileUser


def create_invite(
    mobile_user_id: int,
    person_id: int,
    phone_number: str,
    temporary_password: str,
    estate_id: Optional[int] = None,
    unit_id: Optional[int] = None,
    role: Optional[str] = None,
    sms_sent: bool = False,
    sms_error: Optional[str] = None,
    created_by: Optional[int] = None,
) -> MobileInvite:
    """
    Create a new mobile invite record.

    Args:
        mobile_user_id: ID of the associated mobile user
        person_id: ID of the person
        phone_number: Phone number the invite was sent to
        temporary_password: The plaintext temporary password
        estate_id: Optional estate ID
        unit_id: Optional unit ID
        role: 'owner' or 'tenant'
        sms_sent: Whether SMS was successfully sent
        sms_error: Error message if SMS failed
        created_by: User ID who created the invite

    Returns:
        The created MobileInvite object
    """
    invite = MobileInvite(
        mobile_user_id=mobile_user_id,
        person_id=person_id,
        phone_number=phone_number,
        temporary_password=temporary_password,
        estate_id=estate_id,
        unit_id=unit_id,
        role=role,
        sms_sent=sms_sent,
        sms_error=sms_error,
        created_by=created_by,
    )

    db.session.add(invite)
    db.session.commit()

    return invite


def get_invite_by_id(invite_id: int) -> Optional[MobileInvite]:
    """Get an invite by ID."""
    return MobileInvite.query.get(invite_id)


def get_invite_by_mobile_user_id(mobile_user_id: int) -> Optional[MobileInvite]:
    """Get an invite by mobile user ID."""
    return MobileInvite.query.filter_by(mobile_user_id=mobile_user_id).first()


def list_invites(
    is_used: Optional[bool] = None,
    estate_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[MobileInvite], int]:
    """
    List mobile invites with optional filtering.

    Args:
        is_used: Filter by used status (None = all)
        estate_id: Filter by estate
        search: Search by phone number or person name
        limit: Maximum results to return
        offset: Offset for pagination

    Returns:
        Tuple of (list of invites, total count)
    """
    query = MobileInvite.query

    if is_used is not None:
        query = query.filter(MobileInvite.is_used == is_used)

    if estate_id is not None:
        query = query.filter(MobileInvite.estate_id == estate_id)

    if search:
        # Join to Person to search by name
        from app.models import Person
        query = query.join(Person, MobileInvite.person_id == Person.id)
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                MobileInvite.phone_number.ilike(search_term),
                Person.first_name.ilike(search_term),
                Person.last_name.ilike(search_term),
            )
        )

    # Get total count before pagination
    total = query.count()

    # Apply ordering and pagination
    invites = (
        query
        .order_by(MobileInvite.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return invites, total


def mark_invite_as_used(mobile_user_id: int) -> bool:
    """
    Mark an invite as used when the user logs in.

    Args:
        mobile_user_id: The mobile user ID

    Returns:
        True if invite was found and marked, False otherwise
    """
    invite = get_invite_by_mobile_user_id(mobile_user_id)
    if invite and not invite.is_used:
        invite.mark_as_used()
        db.session.commit()
        return True
    return False


def delete_invite(invite_id: int) -> bool:
    """
    Delete an invite record.

    Args:
        invite_id: ID of the invite to delete

    Returns:
        True if deleted, False if not found
    """
    invite = get_invite_by_id(invite_id)
    if invite:
        db.session.delete(invite)
        db.session.commit()
        return True
    return False


def delete_used_invites() -> int:
    """
    Delete all used invite records.

    Returns:
        Number of records deleted
    """
    count = MobileInvite.query.filter_by(is_used=True).delete()
    db.session.commit()
    return count


def get_invite_stats() -> Dict:
    """
    Get statistics about invites.

    Returns:
        Dictionary with invite statistics
    """
    total = MobileInvite.query.count()
    pending = MobileInvite.query.filter_by(is_used=False).count()
    used = MobileInvite.query.filter_by(is_used=True).count()
    sms_sent = MobileInvite.query.filter_by(sms_sent=True).count()
    sms_failed = MobileInvite.query.filter(
        MobileInvite.sms_sent == False,
        MobileInvite.sms_error.isnot(None)
    ).count()

    return {
        'total': total,
        'pending': pending,
        'used': used,
        'sms_sent': sms_sent,
        'sms_failed': sms_failed,
    }
