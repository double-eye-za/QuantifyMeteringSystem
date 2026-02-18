"""
Ticket routes for the website staff interface.

Staff members can:
- View all tickets
- View ticket details
- Reply to tickets
- Update ticket status, priority, and assignment
- Manage ticket categories
"""
from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from ...models import Ticket, TicketMessage, TicketCategory, Person, User, Unit, Estate
from ...services.tickets import (
    list_tickets as svc_list_tickets,
    get_ticket_by_id,
    get_ticket_by_number,
    update_ticket as svc_update_ticket,
    add_message as svc_add_message,
    close_ticket as svc_close_ticket,
    reopen_ticket as svc_reopen_ticket,
    list_categories as svc_list_categories,
    get_category_by_id,
    create_category as svc_create_category,
    update_category as svc_update_category,
    delete_category as svc_delete_category,
    get_ticket_stats,
)
from ...utils.audit import log_action
from ...utils.pagination import paginate_query
from ...utils.decorators import requires_permission
from . import api_v1


# ==================== Page Routes ====================

@api_v1.route("/tickets", methods=["GET"])
@login_required
@requires_permission("tickets.view")
def tickets_page():
    """Render the tickets management page"""
    search = request.args.get("q") or None
    status = request.args.get("status") or None
    priority = request.args.get("priority") or None
    category_id = request.args.get("category_id", type=int)
    assigned_to_user_id = request.args.get("assigned_to", type=int)
    include_closed = request.args.get("include_closed") == "true"

    # Get tickets with filters
    query = svc_list_tickets(
        search=search,
        status=status,
        priority=priority,
        category_id=category_id,
        assigned_to_user_id=assigned_to_user_id,
        include_closed=include_closed,
    )
    items, meta = paginate_query(query)

    # Build tickets data
    tickets = []
    for ticket in items:
        ticket_data = ticket.to_dict()
        tickets.append(ticket_data)

    # Get categories for filter dropdown
    categories = svc_list_categories()

    # Get users for assignment dropdown
    users = User.query.filter_by(is_active=True).order_by(User.first_name.asc()).all()

    # Get stats for dashboard
    stats = get_ticket_stats()

    return render_template(
        "tickets/tickets.html",
        tickets=tickets,
        categories=[c.to_dict() for c in categories],
        users=[{
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
        } for u in users],
        stats=stats,
        pagination=meta,
        current_filters={
            "q": search,
            "status": status,
            "priority": priority,
            "category_id": category_id,
            "assigned_to": assigned_to_user_id,
            "include_closed": include_closed,
        },
    )


@api_v1.route("/tickets/<int:ticket_id>", methods=["GET"])
@login_required
@requires_permission("tickets.view")
def ticket_detail_page(ticket_id: int):
    """Render the ticket detail page"""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return render_template("errors/404.html"), 404

    # Get categories for edit dropdown
    categories = svc_list_categories()

    # Get users for assignment dropdown
    users = User.query.filter_by(is_active=True).order_by(User.first_name.asc()).all()

    # Get unit info if associated
    unit_info = None
    if ticket.unit_id:
        unit = Unit.query.get(ticket.unit_id)
        if unit:
            estate = Estate.query.get(unit.estate_id)
            unit_info = {
                "id": unit.id,
                "unit_number": unit.unit_number,
                "estate_name": estate.name if estate else "Unknown",
            }

    return render_template(
        "tickets/ticket-detail.html",
        ticket=ticket.to_dict_detailed(),
        categories=[c.to_dict() for c in categories],
        users=[{
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
        } for u in users],
        unit_info=unit_info,
    )


@api_v1.route("/tickets/categories", methods=["GET"])
@login_required
@requires_permission("tickets.view")
def ticket_categories_page():
    """Render the ticket categories management page"""
    include_inactive = request.args.get("include_inactive") == "true"
    categories = svc_list_categories(include_inactive=include_inactive)

    return render_template(
        "tickets/categories.html",
        categories=[c.to_dict() for c in categories],
        include_inactive=include_inactive,
    )


# ==================== API Routes ====================

@api_v1.get("/api/tickets")
@login_required
@requires_permission("tickets.view")
def list_tickets():
    """API endpoint to list tickets"""
    search = request.args.get("q") or None
    status = request.args.get("status") or None
    priority = request.args.get("priority") or None
    category_id = request.args.get("category_id", type=int)
    assigned_to_user_id = request.args.get("assigned_to", type=int)
    include_closed = request.args.get("include_closed") == "true"

    query = svc_list_tickets(
        search=search,
        status=status,
        priority=priority,
        category_id=category_id,
        assigned_to_user_id=assigned_to_user_id,
        include_closed=include_closed,
    )
    items, meta = paginate_query(query)

    tickets = [ticket.to_dict() for ticket in items]
    return jsonify({"data": tickets, **meta})


@api_v1.get("/api/tickets/<int:ticket_id>")
@login_required
@requires_permission("tickets.view")
def get_ticket(ticket_id: int):
    """API endpoint to get a single ticket with messages"""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify({"data": ticket.to_dict_detailed()})


@api_v1.put("/api/tickets/<int:ticket_id>")
@login_required
@requires_permission("tickets.edit")
def update_ticket(ticket_id: int):
    """API endpoint to update a ticket (status, priority, assignment, etc.)"""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    payload = request.get_json(force=True) or {}
    before = ticket.to_dict()

    try:
        ticket, changes = svc_update_ticket(
            ticket, payload, user_id=getattr(current_user, "id", None)
        )
        log_action(
            "ticket.update",
            entity_type="ticket",
            entity_id=ticket_id,
            old_values=before,
            new_values=payload,
        )
        return jsonify({
            "success": True,
            "data": ticket.to_dict(),
            "changes": changes,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.post("/api/tickets/<int:ticket_id>/messages")
@login_required
@requires_permission("tickets.edit")
def add_ticket_message(ticket_id: int):
    """API endpoint to add a message/reply to a ticket"""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    payload = request.get_json(force=True) or {}

    if not payload.get("message"):
        return jsonify({"error": "Message is required"}), 400

    try:
        message = svc_add_message(
            ticket=ticket,
            message=payload["message"],
            sender_type="staff",
            sender_id=current_user.id,
            is_internal=payload.get("is_internal", False),
        )

        log_action(
            "ticket.reply",
            entity_type="ticket",
            entity_id=ticket_id,
            new_values={"message": payload["message"][:100]},
        )

        return jsonify({
            "success": True,
            "data": message.to_dict(),
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.post("/api/tickets/<int:ticket_id>/close")
@login_required
@requires_permission("tickets.edit")
def close_ticket(ticket_id: int):
    """API endpoint to close a ticket"""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    try:
        ticket = svc_close_ticket(ticket, user_id=current_user.id)
        log_action(
            "ticket.close",
            entity_type="ticket",
            entity_id=ticket_id,
        )
        return jsonify({
            "success": True,
            "data": ticket.to_dict(),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.post("/api/tickets/<int:ticket_id>/reopen")
@login_required
@requires_permission("tickets.edit")
def reopen_ticket(ticket_id: int):
    """API endpoint to reopen a closed ticket"""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    try:
        ticket = svc_reopen_ticket(ticket)
        log_action(
            "ticket.reopen",
            entity_type="ticket",
            entity_id=ticket_id,
        )
        return jsonify({
            "success": True,
            "data": ticket.to_dict(),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.get("/api/tickets/stats")
@login_required
@requires_permission("tickets.view")
def tickets_stats():
    """API endpoint to get ticket statistics"""
    stats = get_ticket_stats()
    return jsonify({"data": stats})


# ==================== Category API Routes ====================

@api_v1.get("/api/tickets/categories")
@login_required
@requires_permission("tickets.view")
def list_ticket_categories():
    """API endpoint to list ticket categories"""
    include_inactive = request.args.get("include_inactive") == "true"
    categories = svc_list_categories(include_inactive=include_inactive)
    return jsonify({"data": [c.to_dict() for c in categories]})


@api_v1.get("/api/tickets/categories/<int:category_id>")
@login_required
@requires_permission("tickets.view")
def get_ticket_category(category_id: int):
    """API endpoint to get a single category"""
    category = get_category_by_id(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404
    return jsonify({"data": category.to_dict()})


@api_v1.post("/api/tickets/categories")
@login_required
@requires_permission("tickets.edit")
def create_ticket_category():
    """API endpoint to create a new category"""
    payload = request.get_json(force=True) or {}

    if not payload.get("name"):
        return jsonify({"error": "Category name is required"}), 400

    try:
        category = svc_create_category(
            name=payload["name"],
            description=payload.get("description"),
            icon=payload.get("icon"),
            color=payload.get("color"),
            display_order=payload.get("display_order", 0),
            user_id=current_user.id,
        )

        log_action(
            "ticket_category.create",
            entity_type="ticket_category",
            entity_id=category.id,
            new_values=payload,
        )

        return jsonify({
            "success": True,
            "data": category.to_dict(),
        }), 201

    except IntegrityError:
        return jsonify({"error": "A category with this name already exists"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.put("/api/tickets/categories/<int:category_id>")
@login_required
@requires_permission("tickets.edit")
def update_ticket_category(category_id: int):
    """API endpoint to update a category"""
    category = get_category_by_id(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    payload = request.get_json(force=True) or {}
    before = category.to_dict()

    try:
        category = svc_update_category(category, payload)
        log_action(
            "ticket_category.update",
            entity_type="ticket_category",
            entity_id=category_id,
            old_values=before,
            new_values=payload,
        )
        return jsonify({
            "success": True,
            "data": category.to_dict(),
        })

    except IntegrityError:
        return jsonify({"error": "A category with this name already exists"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1.delete("/api/tickets/categories/<int:category_id>")
@login_required
@requires_permission("tickets.edit")
def delete_ticket_category(category_id: int):
    """API endpoint to delete a category"""
    category = get_category_by_id(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    try:
        success, error = svc_delete_category(category)
        if not success:
            return jsonify({"error": error}), 409

        log_action(
            "ticket_category.delete",
            entity_type="ticket_category",
            entity_id=category_id,
        )

        return jsonify({
            "success": True,
            "message": "Category deleted successfully",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
