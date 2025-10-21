from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Resident, Unit, Estate
from ...utils.audit import log_action
from ...utils.pagination import paginate_query, parse_pagination_params
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.route("/residents", methods=["GET"])
@login_required
@requires_permission("residents.view")
def residents_page():
    search = request.args.get("q") or None
    is_active = request.args.get("is_active")
    unit_id = request.args.get("unit_id", type=int)

    if is_active == "true":
        is_active_val = True
    elif is_active == "false":
        is_active_val = False
    else:
        is_active_val = None

    if not unit_id:
        unit_id = None

    query = Resident.get_all(search=search, is_active=is_active_val, unit_id=unit_id)
    items, meta = paginate_query(query)

    residents = []
    for r in items:
        rd = r.to_dict()
        unit = Unit.query.filter_by(resident_id=r.id).first()
        if unit:
            estate = Estate.query.get(unit.estate_id)
            rd["unit"] = {
                "id": unit.id,
                "unit_number": unit.unit_number,
                "estate_name": estate.name if estate else None,
            }
        else:
            rd["unit"] = None
        residents.append(rd)

    units = []
    for unit in (
        Unit.query.join(Estate, Unit.estate_id == Estate.id)
        .order_by(Estate.name.asc(), Unit.unit_number.asc())
        .all()
    ):
        estate = Estate.query.get(unit.estate_id)
        units.append(
            {
                "id": unit.id,
                "unit_number": unit.unit_number,
                "estate_name": estate.name if estate else "Unknown",
            }
        )

    return render_template(
        "residents/residents.html",
        residents=residents,
        units=units,
        pagination=meta,
        current_filters={"q": search, "is_active": is_active, "unit_id": unit_id},
    )


@api_v1.get("/api/residents")
@login_required
@requires_permission("residents.view")
def list_residents():
    search = request.args.get("q") or None
    items, meta = paginate_query(Resident.get_all(search=search))
    return jsonify({"data": [r.to_dict() for r in items], **meta})


@api_v1.post("/residents")
@login_required
@requires_permission("residents.create")
def create_resident():
    payload = request.get_json(force=True) or {}
    required = ["first_name", "last_name", "email", "phone"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    r = Resident.create_from_payload(payload, user_id=getattr(current_user, "id", None))
    log_action(
        "resident.create", entity_type="resident", entity_id=r.id, new_values=payload
    )
    return jsonify({"data": r.to_dict()}), 201


@api_v1.put("/residents/<int:resident_id>")
@login_required
@requires_permission("residents.edit")
def update_resident(resident_id: int):
    r = Resident.get_by_id(resident_id)
    if not r:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    before = r.to_dict()
    r.update_from_payload(payload, user_id=getattr(current_user, "id", None))
    log_action(
        "resident.update",
        entity_type="resident",
        entity_id=resident_id,
        old_values=before,
        new_values=payload,
    )
    return jsonify({"data": r.to_dict()})


@api_v1.delete("/residents/<int:resident_id>")
@login_required
@requires_permission("residents.delete")
def delete_resident(resident_id: int):
    r = Resident.get_by_id(resident_id)
    if not r:
        return jsonify({"error": "Not Found", "code": 404}), 404
    ok, err = r.delete()
    if not ok:
        return jsonify({"error": "Conflict", **err}), err.get("code", 409)
    log_action("resident.delete", entity_type="resident", entity_id=resident_id)
    return jsonify({"message": "Deleted"})
