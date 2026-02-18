"""
Message service for managing broadcast messages.

This service handles:
- Creating and sending messages (broadcast, estate, individual)
- Tracking message recipients and read status
- Message statistics
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Tuple

from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

from ..db import db
from ..models import (
    Message,
    MessageRecipient,
    Person,
    User,
    Estate,
    Unit,
    UnitOwnership,
    UnitTenancy,
    Notification,
)


def list_messages(
    search: Optional[str] = None,
    message_type: Optional[str] = None,
    estate_id: Optional[int] = None,
    sender_user_id: Optional[int] = None,
):
    """
    List messages with optional filters.

    Args:
        search: Search term for subject
        message_type: Filter by message type (broadcast, estate, individual)
        estate_id: Filter by estate
        sender_user_id: Filter by sender

    Returns:
        SQLAlchemy query object
    """
    query = Message.query.options(
        joinedload(Message.sender),
        joinedload(Message.estate),
        joinedload(Message.recipient_person),
    )

    # Text search
    if search:
        like = f"%{search}%"
        query = query.filter(Message.subject.ilike(like))

    # Message type filter
    if message_type:
        query = query.filter(Message.message_type == message_type)

    # Estate filter
    if estate_id:
        query = query.filter(Message.estate_id == estate_id)

    # Sender filter
    if sender_user_id:
        query = query.filter(Message.sender_user_id == sender_user_id)

    return query.order_by(Message.created_at.desc())


def get_message_by_id(message_id: int) -> Optional[Message]:
    """Get a single message by ID with relationships loaded"""
    return Message.query.options(
        joinedload(Message.sender),
        joinedload(Message.estate),
        joinedload(Message.recipient_person),
    ).filter_by(id=message_id).first()


def create_message(
    subject: str,
    content: str,
    message_type: str,
    sender_user_id: int,
    estate_id: Optional[int] = None,
    recipient_person_id: Optional[int] = None,
) -> Tuple[Message, int]:
    """
    Create and send a new message.

    Args:
        subject: Message subject
        content: Message content
        message_type: 'broadcast', 'estate', or 'individual'
        sender_user_id: ID of the user sending the message
        estate_id: Estate ID (required for 'estate' type)
        recipient_person_id: Person ID (required for 'individual' type)

    Returns:
        Tuple of (Message object, recipient count)
    """
    # Create the message
    message = Message(
        subject=subject,
        content=content,
        message_type=message_type,
        sender_user_id=sender_user_id,
        estate_id=estate_id if message_type == 'estate' else None,
        recipient_person_id=recipient_person_id if message_type == 'individual' else None,
        recipient_count=0,
        created_at=datetime.utcnow(),
    )

    db.session.add(message)
    db.session.flush()  # Get the message ID

    # Create recipients based on message type
    if message_type == 'broadcast':
        recipient_count = _send_to_all_users(message)
    elif message_type == 'estate':
        recipient_count = _send_to_estate(message, estate_id)
    elif message_type == 'individual':
        recipient_count = _send_to_individual(message, recipient_person_id)
    else:
        recipient_count = 0

    # Update recipient count and mark as sent
    message.recipient_count = recipient_count
    message.sent_at = datetime.utcnow()

    db.session.commit()

    # Create notifications for recipients
    _create_notifications(message)

    return message, recipient_count


def _send_to_all_users(message: Message) -> int:
    """
    Create recipients for all active persons.

    Returns:
        Number of recipients created
    """
    # Get all persons with active mobile accounts
    persons = Person.query.filter(
        Person.is_active == True
    ).all()

    count = 0
    for person in persons:
        recipient = MessageRecipient(
            message_id=message.id,
            person_id=person.id,
            is_read=False,
            created_at=datetime.utcnow(),
        )
        db.session.add(recipient)
        count += 1

    return count


def _send_to_estate(message: Message, estate_id: int) -> int:
    """
    Create recipients for all persons in an estate.

    Returns:
        Number of recipients created
    """
    # Get all units in the estate
    units = Unit.query.filter_by(estate_id=estate_id).all()
    unit_ids = [u.id for u in units]

    if not unit_ids:
        return 0

    # Get persons who own or tenant units in this estate
    person_ids = set()

    # Owners (all ownerships are considered active)
    ownerships = UnitOwnership.query.filter(
        UnitOwnership.unit_id.in_(unit_ids)
    ).all()
    for ownership in ownerships:
        person_ids.add(ownership.person_id)

    # Tenants (filter by status='active')
    tenancies = UnitTenancy.query.filter(
        UnitTenancy.unit_id.in_(unit_ids),
        UnitTenancy.status == 'active'
    ).all()
    for tenancy in tenancies:
        person_ids.add(tenancy.person_id)

    count = 0
    for person_id in person_ids:
        recipient = MessageRecipient(
            message_id=message.id,
            person_id=person_id,
            is_read=False,
            created_at=datetime.utcnow(),
        )
        db.session.add(recipient)
        count += 1

    return count


def _send_to_individual(message: Message, person_id: int) -> int:
    """
    Create recipient for a single person.

    Returns:
        Number of recipients created (0 or 1)
    """
    print(f"[DEBUG] _send_to_individual: message_id={message.id}, person_id={person_id}")

    person = Person.query.get(person_id)
    if not person:
        print(f"[DEBUG] Person not found for person_id={person_id}")
        return 0

    print(f"[DEBUG] Creating MessageRecipient for person: {person.full_name} (id={person.id})")

    recipient = MessageRecipient(
        message_id=message.id,
        person_id=person_id,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.session.add(recipient)

    print(f"[DEBUG] MessageRecipient created successfully")
    return 1


def _create_notifications(message: Message) -> None:
    """Create in-app notifications for message recipients"""
    recipients = MessageRecipient.query.filter_by(message_id=message.id).all()

    for recipient in recipients:
        notification = Notification(
            recipient_type='resident',
            recipient_id=recipient.person_id,
            notification_type='message',
            subject=message.subject,
            message=message.content[:200] + ('...' if len(message.content) > 200 else ''),
            channel='in_app',
            priority='normal',
            status='sent',
            sent_at=datetime.utcnow(),
        )
        db.session.add(notification)

    db.session.commit()


def delete_message(message: Message) -> bool:
    """
    Delete a message and all its recipients.

    Returns:
        True if deleted successfully
    """
    db.session.delete(message)
    db.session.commit()
    return True


def get_message_stats() -> Dict:
    """
    Get message statistics for dashboard.

    Returns:
        Dictionary with message statistics
    """
    total = Message.query.count()
    broadcast = Message.query.filter(Message.message_type == 'broadcast').count()
    estate = Message.query.filter(Message.message_type == 'estate').count()
    individual = Message.query.filter(Message.message_type == 'individual').count()

    # Total recipients across all messages
    total_recipients = db.session.query(func.sum(Message.recipient_count)).scalar() or 0

    # Total read
    total_read = MessageRecipient.query.filter(MessageRecipient.is_read == True).count()

    return {
        'total': total,
        'broadcast': broadcast,
        'estate': estate,
        'individual': individual,
        'total_recipients': total_recipients,
        'total_read': total_read,
    }


def get_recipients_for_message(
    message_id: int,
    is_read: Optional[bool] = None,
    page: int = 1,
    per_page: int = 50,
) -> Tuple[List[MessageRecipient], int]:
    """
    Get recipients for a message with pagination.

    Args:
        message_id: Message ID
        is_read: Filter by read status
        page: Page number
        per_page: Items per page

    Returns:
        Tuple of (list of recipients, total count)
    """
    query = MessageRecipient.query.options(
        joinedload(MessageRecipient.person)
    ).filter_by(message_id=message_id)

    if is_read is not None:
        query = query.filter(MessageRecipient.is_read == is_read)

    total = query.count()
    recipients = query.order_by(MessageRecipient.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return recipients, total


# ==================== Mobile App Functions ====================

def get_messages_for_person(
    person_id: int,
    is_read: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20,
):
    """
    Get messages for a specific person (mobile app).

    Args:
        person_id: Person ID
        is_read: Filter by read status
        page: Page number
        per_page: Items per page

    Returns:
        Tuple of (list of message recipients, total count)
    """
    query = MessageRecipient.query.options(
        joinedload(MessageRecipient.message).joinedload(Message.sender)
    ).filter_by(person_id=person_id)

    if is_read is not None:
        query = query.filter(MessageRecipient.is_read == is_read)

    # Order by sent_at descending (newest first)
    query = query.join(Message).order_by(Message.sent_at.desc())

    total = query.count()
    recipients = query.offset((page - 1) * per_page).limit(per_page).all()

    return recipients, total


def get_message_for_person(person_id: int, message_id: int) -> Optional[MessageRecipient]:
    """
    Get a specific message for a person and mark it as read.

    Args:
        person_id: Person ID
        message_id: Message ID

    Returns:
        MessageRecipient object or None
    """
    recipient = MessageRecipient.query.options(
        joinedload(MessageRecipient.message).joinedload(Message.sender)
    ).filter_by(
        person_id=person_id,
        message_id=message_id
    ).first()

    if recipient and not recipient.is_read:
        recipient.mark_as_read()
        db.session.commit()

    return recipient


def mark_message_as_read(person_id: int, message_id: int) -> bool:
    """
    Mark a message as read for a person.

    Returns:
        True if successful, False if not found
    """
    recipient = MessageRecipient.query.filter_by(
        person_id=person_id,
        message_id=message_id
    ).first()

    if not recipient:
        return False

    recipient.mark_as_read()
    db.session.commit()
    return True


def get_unread_count(person_id: int) -> int:
    """
    Get count of unread messages for a person.

    Args:
        person_id: Person ID

    Returns:
        Number of unread messages
    """
    return MessageRecipient.query.filter_by(
        person_id=person_id,
        is_read=False
    ).count()


def search_persons(search: str, limit: int = 20) -> List[Person]:
    """
    Search for persons by name or email (for individual message recipient selection).

    Args:
        search: Search term
        limit: Maximum results

    Returns:
        List of Person objects
    """
    if not search or len(search) < 2:
        return []

    like = f"%{search}%"
    return Person.query.filter(
        Person.is_active == True,
        or_(
            Person.first_name.ilike(like),
            Person.last_name.ilike(like),
            Person.email.ilike(like),
        )
    ).limit(limit).all()


def get_recipient_count_preview(message_type: str, estate_id: Optional[int] = None) -> int:
    """
    Get preview of how many recipients a message will have.

    Args:
        message_type: 'broadcast', 'estate', or 'individual'
        estate_id: Estate ID (for estate type)

    Returns:
        Estimated recipient count
    """
    if message_type == 'broadcast':
        return Person.query.filter(Person.is_active == True).count()

    elif message_type == 'estate' and estate_id:
        # Get all units in the estate
        units = Unit.query.filter_by(estate_id=estate_id).all()
        unit_ids = [u.id for u in units]

        if not unit_ids:
            return 0

        person_ids = set()

        # Owners (all ownerships are considered active)
        ownerships = UnitOwnership.query.filter(
            UnitOwnership.unit_id.in_(unit_ids)
        ).all()
        for ownership in ownerships:
            person_ids.add(ownership.person_id)

        # Tenants (filter by status='active')
        tenancies = UnitTenancy.query.filter(
            UnitTenancy.unit_id.in_(unit_ids),
            UnitTenancy.status == 'active'
        ).all()
        for tenancy in tenancies:
            person_ids.add(tenancy.person_id)

        return len(person_ids)

    elif message_type == 'individual':
        return 1

    return 0
