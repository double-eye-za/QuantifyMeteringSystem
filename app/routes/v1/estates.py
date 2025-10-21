from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Estate
from ...utils.audit import log_action
from ...utils.pagination import paginate_query
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.route("/estates", methods=["GET"])
@login_required
@requires_permission("estates.view")
def estates_page():
    """Render the estates page with paginated estates and summary counts"""
    q = request.args.get("q")
    is_active = request.args.get("is_active")
    is_active_bool = None
    if is_active is not None:
        is_active_bool = is_active.lower() in ("1", "true", "yes")

    query = Estate.get_all(search=q, is_active=is_active_bool)
    items, meta = paginate_query(query)

    # Summary counts via model statics
    total_estates = Estate.count_all()
    from ...models import (
        Unit,
        Meter,
        RateTable,
    )  # local import to avoid circulars at module import

    total_units = Unit.count_all()
    total_meters = Meter.count_all()
    active_dc450s = Meter.count_active_dc450s()

    estates = [e.to_dict() for e in items]
    # Rate tables for dropdowns
    electricity_rate_tables = [
        rt.to_dict() for rt in RateTable.list_filtered(utility_type="electricity").all()
    ]
    water_rate_tables = [
        rt.to_dict() for rt in RateTable.list_filtered(utility_type="water").all()
    ]
    return render_template(
        "estates/estates.html",
        estates=estates,
        pagination=meta,
        totals={
            "estates": total_estates,
            "units": total_units,
            "meters": total_meters,
            "dc450s": active_dc450s,
        },
        electricity_rate_tables=electricity_rate_tables,
        water_rate_tables=water_rate_tables,
    )


@api_v1.get("/estates/<int:estate_id>")
@login_required
@requires_permission("estates.view")
def get_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": estate.to_dict()})


@api_v1.patch("/api/estates/<int:estate_id>/rate-assignment")
@login_required
@requires_permission("estates.edit")
def update_estate_rate_assignment(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404

    payload = request.get_json(force=True) or {}
    before = estate.to_dict()

    updatable = (
        "electricity_rate_table_id",
        "water_rate_table_id",
        "electricity_markup_percentage",
        "water_markup_percentage",
        "solar_free_allocation_kwh",
    )
    for f in updatable:
        if f in payload:
            setattr(estate, f, payload[f])

    from ...db import db

    estate.updated_by = getattr(current_user, "id", None)
    db.session.commit()

    log_action(
        "estate.rate_assignment.update",
        entity_type="estate",
        entity_id=estate.id,
        old_values=before,
        new_values=payload,
    )
    return jsonify({"data": estate.to_dict()})


@api_v1.post("/estates")
@login_required
@requires_permission("estates.create")
def create_estate():
    payload = request.get_json(force=True) or {}
    estate = Estate.create_from_payload(
        payload, user_id=getattr(current_user, "id", None)
    )
    log_action(
        "estate.create", entity_type="estate", entity_id=estate.id, new_values=payload
    )
    return jsonify({"data": estate.to_dict()}), 201


@api_v1.put("/estates/<int:estate_id>")
@login_required
@requires_permission("estates.edit")
def update_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    before = estate.to_dict()
    estate.update_from_payload(payload, user_id=getattr(current_user, "id", None))
    log_action(
        "estate.update",
        entity_type="estate",
        entity_id=estate_id,
        old_values=before,
        new_values=payload,
    )
    return jsonify({"data": estate.to_dict()})


@api_v1.delete("/estates/<int:estate_id>")
@login_required
@requires_permission("estates.delete")
def delete_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    estate.delete()
    log_action("estate.delete", entity_type="estate", entity_id=estate_id)
    return jsonify({"message": "Deleted"}), 200
