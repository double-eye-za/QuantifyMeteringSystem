"""Routes for managing mobile app invitations."""
from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required

from ...models import Estate
from ...services.mobile_invites import (
    list_invites,
    get_invite_by_id,
    delete_invite,
    delete_used_invites,
    get_invite_stats,
    mark_invite_as_used,
)
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.route("/invites", methods=["GET"])
@login_required
@requires_permission("users.view")
def invites_page():
    """Render the invites management page."""
    # Get filter parameters
    is_used = request.args.get("is_used")
    estate_id = request.args.get("estate_id", type=int)
    search = request.args.get("q")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)

    # Convert is_used to boolean
    if is_used == "true":
        is_used = True
    elif is_used == "false":
        is_used = False
    else:
        is_used = None

    # Get invites with pagination
    offset = (page - 1) * per_page
    invites, total = list_invites(
        is_used=is_used,
        estate_id=estate_id,
        search=search,
        limit=per_page,
        offset=offset,
    )

    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page

    # Get estates for filter dropdown
    estates = Estate.query.order_by(Estate.name).all()

    # Get stats
    stats = get_invite_stats()

    return render_template(
        "invites/invites.html",
        invites=invites,
        estates=estates,
        stats=stats,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        },
        filters={
            "is_used": is_used,
            "estate_id": estate_id,
            "search": search,
        },
    )


@api_v1.route("/api/invites", methods=["GET"])
@login_required
@requires_permission("users.view")
def api_list_invites():
    """API endpoint to list invites."""
    is_used = request.args.get("is_used")
    estate_id = request.args.get("estate_id", type=int)
    search = request.args.get("q")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)

    # Convert is_used to boolean
    if is_used == "true":
        is_used = True
    elif is_used == "false":
        is_used = False
    else:
        is_used = None

    offset = (page - 1) * per_page
    invites, total = list_invites(
        is_used=is_used,
        estate_id=estate_id,
        search=search,
        limit=per_page,
        offset=offset,
    )

    return jsonify({
        "data": [invite.to_dict() for invite in invites],
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    })


@api_v1.route("/api/invites/stats", methods=["GET"])
@login_required
@requires_permission("users.view")
def api_invite_stats():
    """API endpoint to get invite statistics."""
    stats = get_invite_stats()
    return jsonify({"data": stats})


@api_v1.route("/api/invites/<int:invite_id>", methods=["DELETE"])
@login_required
@requires_permission("users.delete")
def api_delete_invite(invite_id: int):
    """API endpoint to delete a single invite."""
    success = delete_invite(invite_id)
    if success:
        return jsonify({"message": "Invite deleted successfully"})
    return jsonify({"error": "Invite not found"}), 404


@api_v1.route("/api/invites/used", methods=["DELETE"])
@login_required
@requires_permission("users.delete")
def api_delete_used_invites():
    """API endpoint to delete all used invites."""
    count = delete_used_invites()
    return jsonify({
        "message": f"Deleted {count} used invite(s)",
        "deleted_count": count,
    })
