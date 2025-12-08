"""Mobile app ticket endpoints for customers (persons)."""
from __future__ import annotations

from flask import jsonify, request

from ...models import MobileUser, Ticket, TicketMessage, TicketCategory, Unit
from ...services.tickets import (
    list_tickets as svc_list_tickets,
    get_ticket_by_id,
    create_ticket as svc_create_ticket,
    add_message as svc_add_message,
    list_categories as svc_list_categories,
)
from ...services.mobile_users import can_access_unit
from .auth import require_mobile_auth
from . import mobile_api


@mobile_api.get("/tickets")
@require_mobile_auth
def get_my_tickets(mobile_user: MobileUser):
    """
    Get all tickets created by the authenticated person.

    Query parameters:
        - status: Filter by status (open, in_progress, pending, resolved, closed)
        - include_closed: Include closed tickets (default: false)
        - page: Page number (default: 1)
        - limit: Items per page (default: 20)

    Response:
        {
            "tickets": [...],
            "total": 10,
            "page": 1,
            "pages": 1
        }
    """
    # Get query parameters
    status = request.args.get('status')
    include_closed = request.args.get('include_closed', 'false').lower() == 'true'
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=20, type=int)

    # Get tickets for this person
    query = svc_list_tickets(
        created_by_person_id=mobile_user.person_id,
        status=status,
        include_closed=include_closed,
    )

    # Paginate
    total = query.count()
    tickets = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        'tickets': [
            {
                'id': t.id,
                'ticket_number': t.ticket_number,
                'subject': t.subject,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'category': {
                    'id': t.category.id,
                    'name': t.category.name,
                    'icon': t.category.icon,
                    'color': t.category.color,
                } if t.category else None,
                'unit': {
                    'id': t.unit.id,
                    'unit_number': t.unit.unit_number,
                } if t.unit else None,
                'message_count': t.message_count,
                'has_staff_reply': t.last_staff_response is not None,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'updated_at': t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tickets
        ],
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit,
    }), 200


@mobile_api.get("/tickets/<int:ticket_id>")
@require_mobile_auth
def get_ticket_detail(ticket_id: int, mobile_user: MobileUser):
    """
    Get detailed information about a specific ticket including messages.

    Requires that the ticket was created by the authenticated person.

    Response:
        {
            "ticket": {
                "id": 1,
                "ticket_number": "TKT-2024-ABC123",
                "subject": "Issue with meter",
                "description": "...",
                "status": "open",
                "priority": "medium",
                "category": {...},
                "messages": [...]
            }
        }
    """
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({
            'error': 'Ticket not found',
            'message': f'Ticket with ID {ticket_id} not found'
        }), 404

    # Verify ownership
    if ticket.created_by_person_id != mobile_user.person_id:
        return jsonify({
            'error': 'Access denied',
            'message': 'You do not have access to this ticket'
        }), 403

    # Get messages (exclude internal notes)
    messages = [
        {
            'id': m.id,
            'message': m.message,
            'sender_type': m.sender_type,
            'sender_name': m.sender_name,
            'created_at': m.created_at.isoformat() if m.created_at else None,
        }
        for m in ticket.messages if not m.is_internal
    ]

    return jsonify({
        'ticket': {
            'id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'category': {
                'id': ticket.category.id,
                'name': ticket.category.name,
                'icon': ticket.category.icon,
                'color': ticket.category.color,
            } if ticket.category else None,
            'unit': {
                'id': ticket.unit.id,
                'unit_number': ticket.unit.unit_number,
            } if ticket.unit else None,
            'assigned_to': ticket.assigned_to_user.first_name if ticket.assigned_to_user else None,
            'messages': messages,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None,
            'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            'closed_at': ticket.closed_at.isoformat() if ticket.closed_at else None,
        }
    }), 200


@mobile_api.post("/tickets")
@require_mobile_auth
def create_ticket(mobile_user: MobileUser):
    """
    Create a new support ticket.

    Request body:
        {
            "subject": "Issue with meter reading",
            "description": "My meter is showing incorrect readings...",
            "category_id": 2,
            "unit_id": 10,  // optional
            "priority": "medium"  // optional, default: medium
        }

    Response:
        {
            "success": true,
            "ticket": {...}
        }
    """
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('subject'):
        return jsonify({
            'success': False,
            'error': 'Subject is required'
        }), 400

    if not data.get('description'):
        return jsonify({
            'success': False,
            'error': 'Description is required'
        }), 400

    # Validate category if provided
    category_id = data.get('category_id')
    if category_id:
        category = TicketCategory.query.get(category_id)
        if not category or not category.is_active:
            return jsonify({
                'success': False,
                'error': 'Invalid category'
            }), 400

    # Validate unit access if provided
    unit_id = data.get('unit_id')
    if unit_id:
        if not can_access_unit(mobile_user.person_id, unit_id):
            return jsonify({
                'success': False,
                'error': 'You do not have access to this unit'
            }), 403

    # Create ticket
    try:
        ticket = svc_create_ticket(
            subject=data['subject'],
            description=data['description'],
            created_by_person_id=mobile_user.person_id,
            category_id=category_id,
            priority=data.get('priority', 'medium'),
            unit_id=unit_id,
        )

        return jsonify({
            'success': True,
            'ticket': {
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            }
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mobile_api.post("/tickets/<int:ticket_id>/messages")
@require_mobile_auth
def add_ticket_reply(ticket_id: int, mobile_user: MobileUser):
    """
    Add a reply/message to an existing ticket.

    Request body:
        {
            "message": "Thank you for the update..."
        }

    Response:
        {
            "success": true,
            "message": {...}
        }
    """
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({
            'success': False,
            'error': 'Ticket not found'
        }), 404

    # Verify ownership
    if ticket.created_by_person_id != mobile_user.person_id:
        return jsonify({
            'success': False,
            'error': 'Access denied'
        }), 403

    # Check if ticket is closed
    if ticket.status == 'closed':
        return jsonify({
            'success': False,
            'error': 'Cannot reply to a closed ticket'
        }), 400

    data = request.get_json() or {}

    if not data.get('message'):
        return jsonify({
            'success': False,
            'error': 'Message is required'
        }), 400

    try:
        message = svc_add_message(
            ticket=ticket,
            message=data['message'],
            sender_type='customer',
            sender_id=mobile_user.person_id,
            is_internal=False,
        )

        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'message': message.message,
                'sender_type': message.sender_type,
                'sender_name': message.sender_name,
                'created_at': message.created_at.isoformat() if message.created_at else None,
            }
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mobile_api.get("/tickets/categories")
@require_mobile_auth
def get_ticket_categories(mobile_user: MobileUser):
    """
    Get available ticket categories.

    Response:
        {
            "categories": [
                {
                    "id": 1,
                    "name": "Billing & Payments",
                    "description": "...",
                    "icon": "fa-credit-card",
                    "color": "blue"
                }
            ]
        }
    """
    categories = svc_list_categories(include_inactive=False)

    return jsonify({
        'categories': [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'icon': c.icon,
                'color': c.color,
            }
            for c in categories
        ]
    }), 200


@mobile_api.get("/tickets/stats")
@require_mobile_auth
def get_my_ticket_stats(mobile_user: MobileUser):
    """
    Get ticket statistics for the authenticated person.

    Response:
        {
            "stats": {
                "total": 10,
                "open": 3,
                "in_progress": 2,
                "resolved": 4,
                "closed": 1
            }
        }
    """
    # Count tickets by status for this person
    from sqlalchemy import func
    from ...db import db

    stats = db.session.query(
        Ticket.status,
        func.count(Ticket.id)
    ).filter(
        Ticket.created_by_person_id == mobile_user.person_id
    ).group_by(Ticket.status).all()

    stats_dict = {status: count for status, count in stats}

    return jsonify({
        'stats': {
            'total': sum(stats_dict.values()),
            'open': stats_dict.get('open', 0),
            'in_progress': stats_dict.get('in_progress', 0),
            'pending': stats_dict.get('pending', 0),
            'resolved': stats_dict.get('resolved', 0),
            'closed': stats_dict.get('closed', 0),
        }
    }), 200
