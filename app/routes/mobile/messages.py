"""
Mobile API routes for messages.

Residents can:
- View their messages
- Read message details
- Mark messages as read
- Get unread count
"""
from __future__ import annotations

from flask import jsonify, request

from ...models import MobileUser
from ...services.messages import (
    get_messages_for_person,
    get_message_for_person,
    mark_message_as_read,
    get_unread_count,
)
from ..mobile import mobile_api
from ..mobile.auth import require_mobile_auth


@mobile_api.get("/messages")
@require_mobile_auth
def list_messages(mobile_user: MobileUser):
    """Get messages for the current user"""
    person_id = mobile_user.person_id

    # Debug logging
    print(f"[DEBUG] Fetching messages for person_id={person_id}, mobile_user_id={mobile_user.id}")

    # Parse query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    is_read = request.args.get("is_read")

    # Convert is_read string to boolean
    is_read_filter = None
    if is_read == "true":
        is_read_filter = True
    elif is_read == "false":
        is_read_filter = False

    try:
        recipients, total = get_messages_for_person(
            person_id=person_id,
            is_read=is_read_filter,
            page=page,
            per_page=limit,
        )

        print(f"[DEBUG] Found {total} messages for person_id={person_id}")

        messages = [r.to_dict_for_mobile() for r in recipients]

        return jsonify({
            "success": True,
            "data": messages,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if limit > 0 else 1,
        })

    except Exception as e:
        print(f"[DEBUG] Error fetching messages: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@mobile_api.get("/messages/<int:message_id>")
@require_mobile_auth
def get_message(mobile_user: MobileUser, message_id: int):
    """Get a specific message and mark it as read"""
    person_id = mobile_user.person_id

    try:
        recipient = get_message_for_person(person_id, message_id)

        if not recipient:
            return jsonify({
                "success": False,
                "error": "Message not found"
            }), 404

        return jsonify({
            "success": True,
            "data": recipient.to_dict_for_mobile(),
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@mobile_api.put("/messages/<int:message_id>/read")
@require_mobile_auth
def mark_read(mobile_user: MobileUser, message_id: int):
    """Mark a message as read"""
    person_id = mobile_user.person_id

    try:
        success = mark_message_as_read(person_id, message_id)

        if not success:
            return jsonify({
                "success": False,
                "error": "Message not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Message marked as read"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@mobile_api.get("/messages/unread-count")
@require_mobile_auth
def unread_count(mobile_user: MobileUser):
    """Get count of unread messages"""
    person_id = mobile_user.person_id

    try:
        count = get_unread_count(person_id)

        return jsonify({
            "success": True,
            "count": count,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@mobile_api.delete("/messages/<int:message_id>")
@require_mobile_auth
def delete_message(mobile_user: MobileUser, message_id: int):
    """Delete a message for this user (removes from their inbox)"""
    from ...models import MessageRecipient
    from ...db import db

    person_id = mobile_user.person_id

    try:
        # Find the recipient record for this user and message
        recipient = MessageRecipient.query.filter_by(
            person_id=person_id,
            message_id=message_id
        ).first()

        if not recipient:
            return jsonify({
                "success": False,
                "error": "Message not found"
            }), 404

        # Delete the recipient record (removes message from user's inbox)
        db.session.delete(recipient)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Message deleted"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
