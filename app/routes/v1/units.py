from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from ...models import Unit
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.get("/units")
@login_required
def list_units():
    estate_id = request.args.get("estate_id", type=int)
    occupancy_status = request.args.get("occupancy_status")
    q = request.args.get("q")
    query = Unit.get_all(
        estate_id=estate_id, occupancy_status=occupancy_status, search=q
    )
    items, meta = paginate_query(query)
    return jsonify({"data": [u.to_dict() for u in items], **meta})


@api_v1.get("/units/<int:unit_id>")
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
