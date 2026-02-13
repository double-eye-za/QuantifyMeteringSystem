"""Portal messages routes."""
from flask import render_template, abort, request, redirect, url_for
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...models import Message, MessageRecipient, Person
from ...db import db


@portal.route('/messages')
@portal_login_required
def portal_messages():
    """Message inbox."""
    page = request.args.get('page', 1, type=int)
    is_read = request.args.get('is_read', None)

    query = (
        MessageRecipient.query
        .filter_by(person_id=current_user.person_id)
        .join(Message, Message.id == MessageRecipient.message_id)
        .order_by(Message.created_at.desc())
    )

    if is_read is not None:
        query = query.filter(MessageRecipient.is_read == (is_read == 'true'))

    pagination = query.paginate(page=page, per_page=20, error_out=False)

    # Get unread count
    unread_count = MessageRecipient.query.filter_by(
        person_id=current_user.person_id,
        is_read=False,
    ).count()

    return render_template(
        'portal/messages.html',
        recipients=pagination.items,
        pagination=pagination,
        unread_count=unread_count,
        filter_is_read=is_read,
    )


@portal.route('/messages/<int:message_id>')
@portal_login_required
def portal_message_detail(message_id):
    """View a specific message and mark as read."""
    recipient = MessageRecipient.query.filter_by(
        message_id=message_id,
        person_id=current_user.person_id,
    ).first_or_404()

    # Mark as read
    if not recipient.is_read:
        recipient.is_read = True
        recipient.read_at = db.func.now()
        db.session.commit()

    message = Message.query.get_or_404(message_id)

    return render_template(
        'portal/message_detail.html',
        message=message,
        recipient=recipient,
    )
