from __future__ import annotations

from flask import render_template, request, jsonify
from flask_login import login_required

from ...models.audit_log import AuditLog
from ...models.user import User
from ...utils.pagination import paginate_query
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.route("/audit-logs", methods=["GET"])
@login_required
@requires_permission("audit_logs.view")
def audit_logs_page():
    action = (request.args.get("action") or "").strip() or None
    user_id = request.args.get("user_id", type=int) or None
    start_date = request.args.get("start_date") or None
    end_date = request.args.get("end_date") or None

    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    # Date filters (inclusive start/end). If only start provided, end = end of that day
    from datetime import datetime, timedelta

    def parse_date(s: str):
        try:
            return datetime.fromisoformat(s)
        except Exception:
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except Exception:
                return None

    start_dt = parse_date(start_date) if start_date else None
    end_dt = parse_date(end_date) if end_date else None
    if start_dt and not end_dt:
        end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    if start_dt:
        query = query.filter(AuditLog.created_at >= start_dt)
    if end_dt:
        query = query.filter(AuditLog.created_at <= end_dt)

    query = query.order_by(AuditLog.created_at.desc())
    items, meta = paginate_query(query)

    logs = [
        {
            "id": a.id,
            "user_id": a.user_id,
            "user_name": None,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "ip_address": a.ip_address,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if a.created_at
            else None,
        }
        for a in items
    ]

    user_ids = {row["user_id"] for row in logs if row["user_id"]}
    users_map = {}
    if user_ids:
        users = User.query.filter(User.id.in_(list(user_ids))).all()
        users_map = {u.id: f"{u.first_name} {u.last_name}".strip() for u in users}
        for row in logs:
            if row["user_id"] in users_map:
                row["user_name"] = users_map[row["user_id"]]

    users_for_filter = [
        {"id": u.id, "name": f"{u.first_name} {u.last_name}".strip() or u.email}
        for u in User.query.order_by(User.first_name.asc(), User.last_name.asc()).all()
    ]

    return render_template(
        "audit-logs/audit-logs.html",
        logs=logs,
        pagination=meta,
        users=users_for_filter,
        current_filters={
            "action": action,
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@api_v1.get("/api/audit-logs")
@login_required
@requires_permission("audit_logs.view")
def list_audit_logs():
    action = request.args.get("action")
    user_id = request.args.get("user_id", type=int)
    entity_type = request.args.get("entity_type")

    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    query = query.order_by(AuditLog.created_at.desc())
    items, meta = paginate_query(query)
    data = [
        {
            "id": a.id,
            "user_id": a.user_id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "ip_address": a.ip_address,
            "user_agent": a.user_agent,
            "request_id": a.request_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in items
    ]
    return jsonify({"data": data, **meta})


@api_v1.get("/api/audit-logs/<int:audit_id>")
@login_required
@requires_permission("audit_logs.view")
def get_audit_log(audit_id: int):
    a = AuditLog.query.get(audit_id)
    if not a:
        return jsonify({"error": "Not Found", "code": 404}), 404
    user_name = None
    if a.user_id:
        u = User.query.get(a.user_id)
        if u:
            user_name = f"{u.first_name} {u.last_name}".strip() or u.email
    return jsonify(
        {
            "data": {
                "id": a.id,
                "user_id": a.user_id,
                "user_name": user_name,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "old_values": a.old_values,
                "new_values": a.new_values,
                "ip_address": a.ip_address,
                "user_agent": a.user_agent,
                "request_id": a.request_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        }
    )
