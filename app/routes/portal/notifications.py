"""Portal notifications routes."""
from flask import render_template, request, redirect, url_for
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...models import Notification
from ...db import db
from datetime import datetime


@portal.route('/notifications')
@portal_login_required
def portal_notifications():
    """Notification list."""
    page = request.args.get('page', 1, type=int)
    is_read = request.args.get('is_read', None)

    query = (
        Notification.query
        .filter_by(recipient_type='resident', recipient_id=current_user.person_id)
        .order_by(Notification.created_at.desc())
    )

    if is_read is not None:
        if is_read == 'true':
            query = query.filter(Notification.status == 'read')
        else:
            query = query.filter(Notification.status != 'read')

    pagination = query.paginate(page=page, per_page=50, error_out=False)

    unread_count = Notification.query.filter(
        Notification.recipient_type == 'resident',
        Notification.recipient_id == current_user.person_id,
        Notification.status != 'read',
    ).count()

    return render_template(
        'portal/notifications.html',
        notifications=pagination.items,
        pagination=pagination,
        unread_count=unread_count,
    )


@portal.route('/notifications/mark-all-read', methods=['POST'])
@portal_login_required
def portal_mark_all_notifications_read():
    """Mark all notifications as read."""
    Notification.query.filter(
        Notification.recipient_type == 'resident',
        Notification.recipient_id == current_user.person_id,
        Notification.status != 'read',
    ).update({'status': 'read', 'read_at': datetime.utcnow()})
    db.session.commit()

    return redirect(url_for('portal.portal_notifications'))
