from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from ...models import Notification
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.get("/notifications")
@login_required
def list_notifications():
    recipient_type = request.args.get("recipient_type")
    status = request.args.get("status")
    priority = request.args.get("priority")
    query = Notification.query
    if recipient_type:
        query = query.filter(Notification.recipient_type == recipient_type)
    if status:
        query = query.filter(Notification.status == status)
    if priority:
        query = query.filter(Notification.priority == priority)
    items, meta = paginate_query(query.order_by(Notification.created_at.desc()))
    return jsonify(
        {
            "data": [
                {
                    "id": n.id,
                    "recipient_type": n.recipient_type,
                    "status": n.status,
                    "priority": n.priority,
                    "subject": n.subject,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in items
            ],
            **meta,
        }
    )
