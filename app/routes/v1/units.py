from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required

from ...models import Unit, Estate, Resident
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.route("/units", methods=["GET"])
@login_required
def units_page():
    """Render the units page with units, estates, filters and pagination."""
    estate_id = request.args.get("estate_id", type=int)
    occupancy_status = request.args.get("occupancy_status")
    q = request.args.get("q")

    # Normalize empty strings to None so filters are optional
    if not estate_id:
        estate_id = None
    if occupancy_status == "":
        occupancy_status = None
    if q == "":
        q = None

    query = Unit.get_all(
        estate_id=estate_id, occupancy_status=occupancy_status, search=q
    )
    items, meta = paginate_query(query)

    # Preload resident names for nicer display
    units = []
    for u in items:
        ud = u.to_dict()
        if u.resident_id:
            res = Resident.query.get(u.resident_id)
            if res:
                ud["resident"] = {
                    "id": res.id,
                    "first_name": res.first_name,
                    "last_name": res.last_name,
                    "phone": res.phone,
                }
        units.append(ud)
    estates = [
        {"id": e.id, "name": e.name}
        for e in Estate.get_all().order_by(Estate.name.asc()).all()
    ]

    return render_template(
        "units/units.html",
        units=units,
        estates=estates,
        pagination=meta,
        current_filters={
            "estate_id": estate_id,
            "occupancy_status": occupancy_status,
            "q": q,
        },
    )


@api_v1.get("/api/units")
@login_required
def list_units():
    estate_id = request.args.get("estate_id", type=int)
    occupancy_status = request.args.get("occupancy_status")
    q = request.args.get("q")

    if not estate_id:
        estate_id = None
    if occupancy_status == "":
        occupancy_status = None
    if q == "":
        q = None
    query = Unit.get_all(
        estate_id=estate_id, occupancy_status=occupancy_status, search=q
    )
    items, meta = paginate_query(query)
    return jsonify({"data": [u.to_dict() for u in items], **meta})


@api_v1.route("/units/<unit_id>/wallet-statement", methods=["GET"])
@login_required
def wallet_statement_page(unit_id: str):
    """Render the wallet statement page"""
    return render_template("wallets/wallet-statement.html", unit_id=unit_id)


@api_v1.route("/units/<unit_id>/visual", methods=["GET"])
@login_required
def unit_visual_page(unit_id: str):
    """Render the unit visual diagram page"""
    return render_template("units/unit-visual.html", unit_id=unit_id)


@api_v1.route("/units/<unit_id>", methods=["GET"])
@login_required
def unit_details_page(unit_id: str):
    """Render the unit details page"""
    return render_template("units/unit-details.html", unit_id=unit_id)


@api_v1.get("/api/units/<int:unit_id>")
@login_required
def get_unit(unit_id: int):
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": unit.to_dict()})


@api_v1.post("/units")
@login_required
def create_unit():
    payload = request.get_json(force=True) or {}
    unit = Unit.create_from_payload(payload)
    return jsonify({"data": unit.to_dict()}), 201


@api_v1.put("/units/<int:unit_id>")
@login_required
def update_unit(unit_id: int):
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    unit.update_from_payload(payload)
    return jsonify({"data": unit.to_dict()})
