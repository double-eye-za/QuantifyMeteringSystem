from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from ...models import Estate
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.get("/estates")
@login_required
def list_estates():
    q = request.args.get("q")
    is_active = request.args.get("is_active")
    is_active_bool = None
    if is_active is not None:
        is_active_bool = is_active.lower() in ("1", "true", "yes")

    query = Estate.get_all(search=q, is_active=is_active_bool)
    items, meta = paginate_query(query)
    return jsonify({"data": [e.to_dict() for e in items], **meta})


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
    estate = Estate.create_from_payload(payload)
    return jsonify({"data": estate.to_dict()}), 201


@api_v1.put("/estates/<int:estate_id>")
@login_required
def update_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    estate.update_from_payload(payload)
    return jsonify({"data": estate.to_dict()})


@api_v1.delete("/estates/<int:estate_id>")
@login_required
def delete_estate(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return jsonify({"error": "Not Found", "code": 404}), 404
    estate.delete()
    return jsonify({"message": "Deleted"}), 200
