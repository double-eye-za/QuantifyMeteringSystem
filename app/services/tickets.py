"""
Ticket service for managing support tickets.

This service handles:
- Creating and managing support tickets
- Ticket messages/replies
- Category management
- Sending notifications on ticket events
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Tuple, Dict

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

from ..db import db
from ..models import (
    Ticket,
    TicketMessage,
    TicketCategory,
    Person,
    User,
    Unit,
    Notification,
)


# Notification types for tickets
TYPE_TICKET_CREATED = 'ticket_created'
TYPE_TICKET_REPLY = 'ticket_reply'
TYPE_TICKET_STATUS_CHANGED = 'ticket_status_changed'
TYPE_TICKET_ASSIGNED = 'ticket_assigned'


def list_tickets(
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    assigned_to_user_id: Optional[int] = None,
    created_by_person_id: Optional[int] = None,
    unit_id: Optional[int] = None,
    include_closed: bool = False,
):
    """
    List tickets with optional filters.

    Args:
        search: Search term for ticket number or subject
        status: Filter by status
        priority: Filter by priority
        category_id: Filter by category
        assigned_to_user_id: Filter by assigned staff member
        created_by_person_id: Filter by creator (person)
        unit_id: Filter by unit
        include_closed: Include closed tickets (default: False)

    Returns:
        SQLAlchemy query object
    """
    query = Ticket.query

    # Text search
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.ticket_number.ilike(like),
                Ticket.subject.ilike(like),
            )
        )

    # Status filter
    if status:
        query = query.filter(Ticket.status == status)
    elif not include_closed:
        # By default exclude closed tickets
        query = query.filter(Ticket.status != 'closed')

    # Priority filter
    if priority:
        query = query.filter(Ticket.priority == priority)

    # Category filter
    if category_id:
        query = query.filter(Ticket.category_id == category_id)

    # Assigned user filter
    if assigned_to_user_id:
        query = query.filter(Ticket.assigned_to_user_id == assigned_to_user_id)

    # Created by person filter
    if created_by_person_id:
        query = query.filter(Ticket.created_by_person_id == created_by_person_id)

    # Unit filter
    if unit_id:
        query = query.filter(Ticket.unit_id == unit_id)

    return query.order_by(Ticket.created_at.desc())


def get_ticket_by_id(ticket_id: int) -> Optional[Ticket]:
    """Get a single ticket by ID with fresh data including messages"""
    # Use filter instead of get() to ensure fresh query
    # and eager load messages to avoid lazy loading issues
    return Ticket.query.options(
        joinedload(Ticket.messages),
        joinedload(Ticket.category),
        joinedload(Ticket.created_by_person),
        joinedload(Ticket.assigned_to_user),
        joinedload(Ticket.unit),
    ).filter_by(id=ticket_id).first()


def get_ticket_by_number(ticket_number: str) -> Optional[Ticket]:
    """Get a single ticket by ticket number"""
    return Ticket.query.filter_by(ticket_number=ticket_number).first()


def create_ticket(
    subject: str,
    description: str,
    created_by_person_id: int,
    category_id: Optional[int] = None,
    priority: str = 'medium',
    unit_id: Optional[int] = None,
) -> Ticket:
    """
    Create a new support ticket.

    Args:
        subject: Ticket subject
        description: Detailed description
        created_by_person_id: ID of the person creating the ticket
        category_id: Optional category ID
        priority: Priority level (default: medium)
        unit_id: Optional related unit ID

    Returns:
        Created Ticket object
    """
    # Generate unique ticket number
    ticket_number = Ticket.generate_ticket_number()

    # Ensure uniqueness
    while Ticket.query.filter_by(ticket_number=ticket_number).first():
        ticket_number = Ticket.generate_ticket_number()

    ticket = Ticket(
        ticket_number=ticket_number,
        subject=subject,
        description=description,
        status='open',
        priority=priority,
        category_id=category_id,
        created_by_person_id=created_by_person_id,
        unit_id=unit_id,
    )

    db.session.add(ticket)
    db.session.commit()

    # Create notification for staff (in_app notification to system)
    _notify_ticket_created(ticket)

    return ticket


def update_ticket(
    ticket: Ticket,
    payload: dict,
    user_id: Optional[int] = None,
) -> Tuple[Ticket, List[str]]:
    """
    Update an existing ticket.

    Args:
        ticket: Ticket object to update
        payload: Dictionary containing updated data
        user_id: ID of the user making the update

    Returns:
        Tuple of (Updated Ticket object, list of changes made)
    """
    changes = []
    old_status = ticket.status
    old_assigned = ticket.assigned_to_user_id

    updatable_fields = ('subject', 'priority', 'category_id', 'unit_id')

    for field in updatable_fields:
        if field in payload and getattr(ticket, field) != payload[field]:
            old_value = getattr(ticket, field)
            setattr(ticket, field, payload[field])
            changes.append(f"{field}: {old_value} -> {payload[field]}")

    # Handle status changes separately for notifications
    if 'status' in payload and ticket.status != payload['status']:
        old_value = ticket.status
        ticket.status = payload['status']
        changes.append(f"status: {old_value} -> {payload['status']}")

        # Set resolved_at or closed_at timestamps
        if payload['status'] == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        elif payload['status'] == 'closed' and not ticket.closed_at:
            ticket.closed_at = datetime.utcnow()

        # Send notification about status change to person
        _notify_status_changed(ticket, old_value, payload['status'])

    # Handle assignment changes
    if 'assigned_to_user_id' in payload:
        if ticket.assigned_to_user_id != payload['assigned_to_user_id']:
            old_value = ticket.assigned_to_user_id
            ticket.assigned_to_user_id = payload['assigned_to_user_id']
            changes.append(f"assigned: {old_value} -> {payload['assigned_to_user_id']}")

            # Notify new assignee
            if payload['assigned_to_user_id']:
                _notify_ticket_assigned(ticket)

    db.session.commit()
    return ticket, changes


def add_message(
    ticket: Ticket,
    message: str,
    sender_type: str,
    sender_id: int,
    is_internal: bool = False,
) -> TicketMessage:
    """
    Add a message to a ticket.

    Args:
        ticket: Ticket to add message to
        message: Message content
        sender_type: 'staff' or 'customer'
        sender_id: User ID if staff, Person ID if customer
        is_internal: Whether this is an internal note (staff only)

    Returns:
        Created TicketMessage object
    """
    ticket_message = TicketMessage(
        ticket_id=ticket.id,
        message=message,
        sender_type=sender_type,
        sender_id=sender_id,
        is_internal=is_internal,
    )

    db.session.add(ticket_message)

    # Update ticket's updated_at timestamp
    ticket.updated_at = datetime.utcnow()

    # If staff is replying and ticket is in 'open' status, move to 'in_progress'
    if sender_type == 'staff' and ticket.status == 'open':
        ticket.status = 'in_progress'

    db.session.commit()

    # Send notification about reply
    if not is_internal:  # Don't notify for internal notes
        _notify_reply(ticket, ticket_message)

    return ticket_message


def close_ticket(ticket: Ticket, user_id: int) -> Ticket:
    """
    Close a ticket.

    Args:
        ticket: Ticket to close
        user_id: ID of user closing the ticket

    Returns:
        Updated Ticket object
    """
    ticket.status = 'closed'
    ticket.closed_at = datetime.utcnow()
    db.session.commit()

    _notify_status_changed(ticket, 'open', 'closed')

    return ticket


def reopen_ticket(ticket: Ticket) -> Ticket:
    """
    Reopen a closed ticket.

    Args:
        ticket: Ticket to reopen

    Returns:
        Updated Ticket object
    """
    old_status = ticket.status
    ticket.status = 'open'
    ticket.closed_at = None
    ticket.resolved_at = None
    db.session.commit()

    _notify_status_changed(ticket, old_status, 'open')

    return ticket


# ==================== Category Management ====================

def list_categories(include_inactive: bool = False):
    """
    List ticket categories.

    Args:
        include_inactive: Include inactive categories

    Returns:
        List of TicketCategory objects
    """
    query = TicketCategory.query

    if not include_inactive:
        query = query.filter(TicketCategory.is_active == True)

    return query.order_by(TicketCategory.display_order.asc()).all()


def get_category_by_id(category_id: int) -> Optional[TicketCategory]:
    """Get a single category by ID"""
    return TicketCategory.query.get(category_id)


def create_category(
    name: str,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
    display_order: int = 0,
    user_id: Optional[int] = None,
) -> TicketCategory:
    """
    Create a new ticket category.

    Args:
        name: Category name
        description: Optional description
        icon: Optional Font Awesome icon class
        color: Optional color class or hex
        display_order: Display order (lower = first)
        user_id: ID of user creating the category

    Returns:
        Created TicketCategory object
    """
    category = TicketCategory(
        name=name,
        description=description,
        icon=icon,
        color=color,
        display_order=display_order,
        is_active=True,
        created_by=user_id,
    )

    db.session.add(category)
    db.session.commit()

    return category


def update_category(
    category: TicketCategory,
    payload: dict,
) -> TicketCategory:
    """
    Update an existing category.

    Args:
        category: TicketCategory object to update
        payload: Dictionary containing updated data

    Returns:
        Updated TicketCategory object
    """
    updatable_fields = ('name', 'description', 'icon', 'color', 'is_active', 'display_order')

    for field in updatable_fields:
        if field in payload:
            setattr(category, field, payload[field])

    db.session.commit()
    return category


def delete_category(category: TicketCategory) -> Tuple[bool, Optional[str]]:
    """
    Delete a category if it has no associated tickets.

    Args:
        category: TicketCategory object to delete

    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    if category.tickets:
        return False, f"Category has {len(category.tickets)} associated tickets and cannot be deleted."

    db.session.delete(category)
    db.session.commit()
    return True, None


# ==================== Statistics ====================

def get_ticket_stats() -> Dict:
    """
    Get ticket statistics for dashboard.

    Returns:
        Dictionary with ticket statistics
    """
    total = Ticket.query.count()
    open_count = Ticket.query.filter(Ticket.status == 'open').count()
    in_progress = Ticket.query.filter(Ticket.status == 'in_progress').count()
    pending = Ticket.query.filter(Ticket.status == 'pending').count()
    resolved = Ticket.query.filter(Ticket.status == 'resolved').count()
    closed = Ticket.query.filter(Ticket.status == 'closed').count()

    # Priority breakdown
    urgent = Ticket.query.filter(
        Ticket.priority == 'urgent',
        Ticket.status.notin_(['resolved', 'closed'])
    ).count()
    high = Ticket.query.filter(
        Ticket.priority == 'high',
        Ticket.status.notin_(['resolved', 'closed'])
    ).count()

    return {
        'total': total,
        'open': open_count,
        'in_progress': in_progress,
        'pending': pending,
        'resolved': resolved,
        'closed': closed,
        'active': open_count + in_progress + pending,
        'urgent': urgent,
        'high_priority': high,
    }


# ==================== Notification Helpers ====================

def _notify_ticket_created(ticket: Ticket) -> None:
    """Send notification when a new ticket is created (for staff)."""
    # Create a system notification that staff can see
    person = Person.query.get(ticket.created_by_person_id)
    person_name = person.full_name if person else 'Unknown'

    notification = Notification(
        recipient_type='system',
        recipient_id=None,
        notification_type=TYPE_TICKET_CREATED,
        subject='New Support Ticket',
        message=f'New ticket #{ticket.ticket_number} created by {person_name}: {ticket.subject}',
        channel='in_app',
        priority='normal',
        status='sent',
        sent_at=datetime.utcnow(),
    )

    db.session.add(notification)
    db.session.commit()


def _notify_status_changed(ticket: Ticket, old_status: str, new_status: str) -> None:
    """Send notification when ticket status changes."""
    # Notify the person who created the ticket
    status_display = new_status.replace('_', ' ').title()

    notification = Notification(
        recipient_type='resident',
        recipient_id=ticket.created_by_person_id,
        notification_type=TYPE_TICKET_STATUS_CHANGED,
        subject=f'Ticket Status Updated',
        message=f'Your ticket #{ticket.ticket_number} status has been updated to: {status_display}',
        channel='in_app',
        priority='normal',
        status='sent',
        sent_at=datetime.utcnow(),
    )

    db.session.add(notification)
    db.session.commit()


def _notify_reply(ticket: Ticket, message: TicketMessage) -> None:
    """Send notification when a reply is added to a ticket."""
    if message.sender_type == 'staff':
        # Staff replied - notify the customer (person)
        user = User.query.get(message.sender_id)
        sender_name = f"{user.first_name} {user.last_name}" if user else 'Staff'

        notification = Notification(
            recipient_type='resident',
            recipient_id=ticket.created_by_person_id,
            notification_type=TYPE_TICKET_REPLY,
            subject=f'New Reply to Your Ticket',
            message=f'{sender_name} replied to your ticket #{ticket.ticket_number}',
            channel='in_app',
            priority='normal',
            status='sent',
            sent_at=datetime.utcnow(),
        )

        db.session.add(notification)
        db.session.commit()
    else:
        # Customer replied - notify staff (system notification)
        person = Person.query.get(message.sender_id)
        sender_name = person.full_name if person else 'Customer'

        notification = Notification(
            recipient_type='system',
            recipient_id=None,
            notification_type=TYPE_TICKET_REPLY,
            subject=f'Customer Reply on Ticket',
            message=f'{sender_name} replied to ticket #{ticket.ticket_number}',
            channel='in_app',
            priority='normal',
            status='sent',
            sent_at=datetime.utcnow(),
        )

        db.session.add(notification)
        db.session.commit()


def _notify_ticket_assigned(ticket: Ticket) -> None:
    """Send notification when a ticket is assigned to a staff member."""
    if not ticket.assigned_to_user_id:
        return

    person = Person.query.get(ticket.created_by_person_id)
    person_name = person.full_name if person else 'Unknown'

    notification = Notification(
        recipient_type='user',
        recipient_id=ticket.assigned_to_user_id,
        notification_type=TYPE_TICKET_ASSIGNED,
        subject='Ticket Assigned to You',
        message=f'Ticket #{ticket.ticket_number} from {person_name} has been assigned to you: {ticket.subject}',
        channel='in_app',
        priority='normal',
        status='sent',
        sent_at=datetime.utcnow(),
    )

    db.session.add(notification)
    db.session.commit()
