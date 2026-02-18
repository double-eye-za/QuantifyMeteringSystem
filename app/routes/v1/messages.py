"""
Message routes for the website staff interface.

Staff members can:
- View all sent messages
- Compose and send new messages
- View message details and read receipts
- Delete messages
"""
from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Message, MessageRecipient, Person, User, Estate
from ...services.messages import (
    list_messages as svc_list_messages,
    get_message_by_id,
    create_message as svc_create_message,
    delete_message as svc_delete_message,
    get_message_stats,
    get_recipients_for_message,
    search_persons,
    get_recipient_count_preview,
)
from ...utils.audit import log_action
from ...utils.pagination import paginate_query
from ...utils.decorators import requires_permission
from . import api_v1


# ==================== Page Routes ====================

@api_v1.route("/messages", methods=["GET"])
@login_required
@requires_permission("messages.view")
def messages_page():
    """Render the messages management page"""
    search = request.args.get("q") or None
    message_type = request.args.get("type") or None
    estate_id = request.args.get("estate_id", type=int)

    # Get messages with filters
    query = svc_list_messages(
        search=search,
        message_type=message_type,
        estate_id=estate_id,
    )
    items, meta = paginate_query(query)

    # Build messages data
    messages = []
    for msg in items:
        msg_data = msg.to_dict_summary()
        msg_data['sender_name'] = f"{msg.sender.first_name} {msg.sender.last_name}" if msg.sender else "Unknown"
        msg_data['estate_name'] = msg.estate.name if msg.estate else None
        messages.append(msg_data)

    # Get estates for filter dropdown
    estates = Estate.query.order_by(Estate.name.asc()).all()

    # Get stats for dashboard
    stats = get_message_stats()

    return render_template(
        "messages/messages.html",
        messages=messages,
        estates=[{"id": e.id, "name": e.name} for e in estates],
        stats=stats,
        pagination=meta,
        current_filters={
            "q": search,
            "type": message_type,
            "estate_id": estate_id,
        },
    )


@api_v1.route("/messages/compose", methods=["GET"])
@login_required
@requires_permission("messages.create")
def compose_message_page():
    """Render the compose message page"""
    # Get estates for dropdown
    estates = Estate.query.order_by(Estate.name.asc()).all()

    return render_template(
        "messages/compose.html",
        estates=[{"id": e.id, "name": e.name} for e in estates],
    )


@api_v1.route("/messages/<int:message_id>", methods=["GET"])
@login_required
@requires_permission("messages.view")
def message_detail_page(message_id: int):
    """Render the message detail page"""
    message = get_message_by_id(message_id)
    if not message:
        return render_template("errors/404.html"), 404

    # Get recipients with pagination
    page = request.args.get("page", 1, type=int)
    is_read_filter = request.args.get("is_read")
    is_read = None
    if is_read_filter == "true":
        is_read = True
    elif is_read_filter == "false":
        is_read = False

    recipients, total = get_recipients_for_message(
        message_id=message_id,
        is_read=is_read,
        page=page,
        per_page=50,
    )

    return render_template(
        "messages/message-detail.html",
        message=message.to_dict(),
        recipients=[r.to_dict() for r in recipients],
        recipients_total=total,
        recipients_page=page,
        recipients_pages=(total + 49) // 50,
        is_read_filter=is_read_filter,
    )


# ==================== API Routes ====================

@api_v1.get("/api/messages")
@login_required
@requires_permission("messages.view")
def list_messages():
    """API endpoint to list messages"""
    search = request.args.get("q") or None
    message_type = request.args.get("type") or None
    estate_id = request.args.get("estate_id", type=int)

    query = svc_list_messages(
        search=search,
        message_type=message_type,
        estate_id=estate_id,
    )
    items, meta = paginate_query(query)

    messages = [msg.to_dict_summary() for msg in items]
    return jsonify({"data": messages, **meta})


@api_v1.post("/api/messages")
@login_required
@requires_permission("messages.create")
def create_message():
    """API endpoint to create and send a message"""
    payload = request.get_json(force=True) or {}

    # Validate required fields
    if not payload.get("subject"):
        return jsonify({"error": "Subject is required"}), 400
    if not payload.get("content"):
        return jsonify({"error": "Content is required"}), 400
    if not payload.get("message_type"):
        return jsonify({"error": "Message type is required"}), 400

    message_type = payload["message_type"]

    # Validate type-specific fields
    if message_type == "estate" and not payload.get("estate_id"):
        return jsonify({"error": "Estate is required for estate messages"}), 400
    if message_type == "individual" and not payload.get("recipient_person_id"):
        return jsonify({"error": "Recipient is required for individual messages"}), 400

    try:
        message, recipient_count = svc_create_message(
            subject=payload["subject"],
            content=payload["content"],
            message_type=message_type,
            sender_user_id=current_user.id,
            estate_id=payload.get("estate_id"),
            recipient_person_id=payload.get("recipient_person_id"),
        )

        log_action(
            "message.create",
            entity_type="message",
            entity_id=message.id,
            new_values={
                "subject": payload["subject"],
                "type": message_type,
                "recipients": recipient_count,
            },
        )

        return jsonify({
            "success": True,
            "data": message.to_dict(),
            "recipient_count": recipient_count,
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.get("/api/messages/<int:message_id>")
@login_required
@requires_permission("messages.view")
def get_message(message_id: int):
    """API endpoint to get a single message"""
    message = get_message_by_id(message_id)
    if not message:
        return jsonify({"error": "Message not found"}), 404
    return jsonify({"data": message.to_dict()})


@api_v1.delete("/api/messages/<int:message_id>")
@login_required
@requires_permission("messages.delete")
def delete_message(message_id: int):
    """API endpoint to delete a message"""
    message = get_message_by_id(message_id)
    if not message:
        return jsonify({"error": "Message not found"}), 404

    try:
        svc_delete_message(message)

        log_action(
            "message.delete",
            entity_type="message",
            entity_id=message_id,
        )

        return jsonify({
            "success": True,
            "message": "Message deleted successfully",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.get("/api/messages/stats")
@login_required
@requires_permission("messages.view")
def messages_stats():
    """API endpoint to get message statistics"""
    stats = get_message_stats()
    return jsonify({"data": stats})


@api_v1.get("/api/messages/search-persons")
@login_required
@requires_permission("messages.create")
def search_message_persons():
    """API endpoint to search for persons (for individual message recipient)"""
    search = request.args.get("q", "")
    persons = search_persons(search, limit=20)

    return jsonify({
        "data": [
            {
                "id": p.id,
                "name": p.full_name,
                "email": p.email,
            }
            for p in persons
        ]
    })


@api_v1.get("/api/messages/recipient-count")
@login_required
@requires_permission("messages.create")
def get_recipient_count():
    """API endpoint to get recipient count preview"""
    message_type = request.args.get("type", "broadcast")
    estate_id = request.args.get("estate_id", type=int)

    count = get_recipient_count_preview(message_type, estate_id)
    return jsonify({"count": count})
