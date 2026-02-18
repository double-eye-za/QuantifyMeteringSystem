"""Portal tickets routes."""
from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...models import Ticket, TicketMessage, TicketCategory
from ...services.mobile_users import get_user_units
from ...db import db
from datetime import datetime


@portal.route('/tickets')
@portal_login_required
def portal_tickets():
    """Support tickets list."""
    status = request.args.get('status', None)
    page = request.args.get('page', 1, type=int)

    query = Ticket.query.filter_by(created_by_person_id=current_user.person_id)

    if status:
        query = query.filter(Ticket.status == status)
    else:
        # Exclude closed by default
        query = query.filter(Ticket.status != 'closed')

    query = query.order_by(Ticket.updated_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    # Stats
    from sqlalchemy import func
    stats_query = (
        db.session.query(Ticket.status, func.count(Ticket.id))
        .filter(Ticket.created_by_person_id == current_user.person_id)
        .group_by(Ticket.status)
        .all()
    )
    stats = {s: c for s, c in stats_query}

    return render_template(
        'portal/tickets.html',
        tickets=pagination.items,
        pagination=pagination,
        stats=stats,
        filter_status=status,
    )


@portal.route('/tickets/<int:ticket_id>')
@portal_login_required
def portal_ticket_detail(ticket_id):
    """View ticket details and message thread."""
    ticket = Ticket.query.get_or_404(ticket_id)

    # Verify ownership
    if ticket.created_by_person_id != current_user.person_id:
        abort(403)

    messages = (
        TicketMessage.query
        .filter_by(ticket_id=ticket.id, is_internal=False)
        .order_by(TicketMessage.created_at.asc())
        .all()
    )

    return render_template(
        'portal/ticket_detail.html',
        ticket=ticket,
        messages=messages,
    )


@portal.route('/tickets/create', methods=['GET'])
@portal_login_required
def portal_ticket_create():
    """Show create ticket form."""
    categories = TicketCategory.query.filter_by(is_active=True).all()
    units = get_user_units(current_user.person_id)

    return render_template(
        'portal/ticket_create.html',
        categories=categories,
        units=units,
    )


@portal.route('/tickets', methods=['POST'])
@portal_login_required
def portal_ticket_submit():
    """Create a new ticket."""
    subject = request.form.get('subject')
    description = request.form.get('description')
    category_id = request.form.get('category_id', type=int)
    unit_id = request.form.get('unit_id', type=int)
    priority = request.form.get('priority', 'medium')

    if not subject or not description:
        flash('Subject and description are required.', 'error')
        return redirect(url_for('portal.portal_ticket_create'))

    import random, string
    ticket_number = f"TKT-{datetime.now().strftime('%Y')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

    ticket = Ticket(
        ticket_number=ticket_number,
        subject=subject,
        description=description,
        status='open',
        priority=priority,
        category_id=category_id,
        unit_id=unit_id,
        created_by_person_id=current_user.person_id,
    )
    db.session.add(ticket)
    db.session.commit()

    # Add initial message
    initial_message = TicketMessage(
        ticket_id=ticket.id,
        sender_type='customer',
        sender_id=current_user.person_id,
        message=description,
        is_internal=False,
    )
    db.session.add(initial_message)
    db.session.commit()

    flash('Ticket created successfully.', 'success')
    return redirect(url_for('portal.portal_ticket_detail', ticket_id=ticket.id))


@portal.route('/tickets/<int:ticket_id>/reply', methods=['POST'])
@portal_login_required
def portal_ticket_reply(ticket_id):
    """Add a reply to a ticket."""
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.created_by_person_id != current_user.person_id:
        abort(403)

    message_text = request.form.get('message')
    if not message_text:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('portal.portal_ticket_detail', ticket_id=ticket_id))

    reply = TicketMessage(
        ticket_id=ticket.id,
        sender_type='customer',
        sender_id=current_user.person_id,
        message=message_text,
        is_internal=False,
    )
    db.session.add(reply)

    # Update ticket timestamp
    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    flash('Reply sent.', 'success')
    return redirect(url_for('portal.portal_ticket_detail', ticket_id=ticket_id))
