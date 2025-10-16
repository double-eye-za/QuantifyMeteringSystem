from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Estate
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.route("/estates", methods=["GET"])
@login_required
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
def get_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": estate.to_dict()})


@api_v1.post("/estates")
@login_required
def create_estate():
    payload = request.get_json(force=True) or {}
    estate = Estate.create_from_payload(
        payload, user_id=getattr(current_user, "id", None)
    )
    return jsonify({"data": estate.to_dict()}), 201


@api_v1.put("/estates/<int:estate_id>")
@login_required
def update_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    estate.update_from_payload(payload, user_id=getattr(current_user, "id", None))
    return jsonify({"data": estate.to_dict()})


@api_v1.delete("/estates/<int:estate_id>")
@login_required
def delete_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    estate.delete()
    return jsonify({"message": "Deleted"}), 200
