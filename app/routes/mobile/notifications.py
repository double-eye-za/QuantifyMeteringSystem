"""Mobile app notification endpoints."""
from __future__ import annotations

from flask import jsonify, request
from datetime import datetime

from ...models import Notification, MobileUser
from ...db import db
from .auth import require_mobile_auth
from . import mobile_api


@mobile_api.get("/notifications")
@require_mobile_auth
def get_notifications(mobile_user: MobileUser):
    """
    Get notifications for the authenticated user.

    Query parameters:
        - is_read: Filter by read status (true/false)
        - page: Page number for pagination (default: 1)
        - limit: Items per page (default: 50)

    Response:
        {
            "success": true,
            "data": {
                "notifications": [...],
                "unread_count": 3,
                "pagination": {...}
            }
        }
    """
    # Get query parameters
    is_read_param = request.args.get('is_read')
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=50, type=int)

    # Build query - notifications for this user (resident type with person_id)
    query = Notification.query.filter(
        Notification.recipient_type == 'resident',
        Notification.recipient_id == mobile_user.person_id,
        Notification.channel == 'in_app'
    )

    # Filter by read status if provided
    if is_read_param is not None:
        is_read = is_read_param.lower() == 'true'
        if is_read:
            query = query.filter(Notification.read_at.isnot(None))
        else:
            query = query.filter(Notification.read_at.is_(None))

    # Get total count for pagination
    total_items = query.count()
    total_pages = (total_items + limit - 1) // limit if limit > 0 else 1

    # Get unread count
    unread_count = Notification.query.filter(
        Notification.recipient_type == 'resident',
        Notification.recipient_id == mobile_user.person_id,
        Notification.channel == 'in_app',
        Notification.read_at.is_(None)
    ).count()

    # Get notifications with pagination
    offset = (page - 1) * limit
    notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    return jsonify({
        'success': True,
        'data': {
            'notifications': [
                {
                    'id': n.id,
                    'type': n.notification_type,
                    'title': n.subject or _get_default_title(n.notification_type),
                    'message': n.message,
                    'is_read': n.read_at is not None,
                    'created_at': n.created_at.isoformat() + 'Z' if n.created_at else None,
                }
                for n in notifications
            ],
            'unread_count': unread_count,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_items': total_items,
                'items_per_page': limit
            }
        }
    }), 200


@mobile_api.post("/notifications/mark-all-read")
@require_mobile_auth
def mark_all_notifications_read(mobile_user: MobileUser):
    """
    Mark all notifications as read for the authenticated user.

    Response:
        {
            "success": true,
            "message": "All notifications marked as read",
            "data": {
                "updated_count": 3
            }
        }
    """
    # Update all unread notifications for this user
    updated_count = Notification.query.filter(
        Notification.recipient_type == 'resident',
        Notification.recipient_id == mobile_user.person_id,
        Notification.channel == 'in_app',
        Notification.read_at.is_(None)
    ).update({
        'read_at': datetime.utcnow(),
        'status': 'read'
    })

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'All notifications marked as read',
        'data': {
            'updated_count': updated_count
        }
    }), 200


@mobile_api.patch("/notifications/<int:notification_id>/read")
@require_mobile_auth
def mark_notification_read(notification_id: int, mobile_user: MobileUser):
    """
    Mark a single notification as read.

    Response:
        {
            "success": true,
            "message": "Notification marked as read"
        }
    """
    # Find the notification
    notification = Notification.query.filter(
        Notification.id == notification_id,
        Notification.recipient_type == 'resident',
        Notification.recipient_id == mobile_user.person_id
    ).first()

    if not notification:
        return jsonify({
            'success': False,
            'error': 'Notification not found',
            'message': 'Notification not found or access denied'
        }), 404

    # Mark as read
    notification.read_at = datetime.utcnow()
    notification.status = 'read'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Notification marked as read'
    }), 200


def _get_default_title(notification_type: str) -> str:
    """Get default title based on notification type."""
    titles = {
        'low_credit': 'Low Credit Warning',
        'purchase_success': 'Purchase Successful',
        'topup_success': 'Wallet Top-Up Successful',
        'meter_reading': 'Meter Reading Updated',
        'usage_alert': 'Usage Alert',
        'maintenance': 'System Maintenance',
        'solar_report': 'Solar Generation Report',
        'high_usage': 'High Usage Alert',
    }
    return titles.get(notification_type, 'Notification')
