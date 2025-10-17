from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Unit, Estate, Resident, Meter, RateTable, SystemSetting
from ...utils.pagination import paginate_query
from ...utils.audit import log_action
from . import api_v1
from ...utils.rates import calculate_estate_bill


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

    assigned_ids = set()
    for u in Unit.query.with_entities(
        Unit.electricity_meter_id, Unit.water_meter_id, Unit.solar_meter_id
    ).all():
        for mid in u:
            if mid:
                assigned_ids.add(mid)

    def serialize_meter(m):
        return {
            "id": m.id,
            "serial_number": m.serial_number,
            "disabled": m.id in assigned_ids,
        }

    electricity_meters = [serialize_meter(m) for m in Meter.get_electricity_meters()]
    water_meters = [serialize_meter(m) for m in Meter.get_water_meters()]
    solar_meters = [serialize_meter(m) for m in Meter.get_solar_meters()]

    residents = [
        {"id": r.id, "name": f"{r.first_name} {r.last_name}"}
        for r in Resident.get_all_for_dropdown()
    ]

    return render_template(
        "units/units.html",
        units=units,
        estates=estates,
        electricity_meters=electricity_meters,
        water_meters=water_meters,
        solar_meters=solar_meters,
        residents=residents,
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


@api_v1.route("/units/<int:unit_id>", methods=["GET"])
@login_required
def unit_details_page(unit_id: int):
    """Render the unit details page with dynamic unit and resident info"""
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return render_template("errors/404.html"), 404

    estate = None
    if getattr(unit, "estate_id", None):
        estate = Estate.get_by_id(unit.estate_id)

    resident = None
    if getattr(unit, "resident_id", None):
        resident = Resident.get_by_id(unit.resident_id)

    return render_template(
        "units/unit-details.html",
        unit=unit,
        estate=estate,
        resident=resident,
    )


@api_v1.get("/api/units/<int:unit_id>")
@login_required
def get_unit(unit_id: int):
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": unit.to_dict()})


@api_v1.post("/api/units/overrides")
@login_required
def apply_unit_overrides():
    """Apply a rate table override to a list of units by id or by estate+unit_numbers list."""
    payload = request.get_json(force=True) or {}
    rate_table_id = payload.get("rate_table_id")
    if not rate_table_id:
        return jsonify({"error": "rate_table_id is required"}), 400
    rt = RateTable.get_by_id(int(rate_table_id))
    if not rt:
        return jsonify({"error": "Invalid rate_table_id"}), 400

    unit_ids = payload.get("unit_ids") or []
    estate_id = payload.get("estate_id")
    unit_numbers = payload.get("unit_numbers") or []

    import json

    setting_key = "unit_rate_overrides"
    setting: SystemSetting = SystemSetting.query.filter_by(
        setting_key=setting_key
    ).first()
    overrides = {}
    if setting and setting.setting_value:
        try:
            overrides = json.loads(setting.setting_value) or {}
        except Exception:
            overrides = {}

    def apply_override_to_unit(unit_obj: Unit):
        uid = str(unit_obj.id)
        entry = overrides.get(uid) or {}

        if getattr(unit_obj, "electricity_meter_id", None):
            entry["electricity_rate_table_id"] = int(rate_table_id)
        if getattr(unit_obj, "water_meter_id", None):
            entry["water_rate_table_id"] = int(rate_table_id)
        overrides[uid] = entry

    updated_unit_ids = []
    if unit_ids:
        for uid in unit_ids:
            u = Unit.get_by_id(int(uid))
            if u:
                apply_override_to_unit(u)
                updated_unit_ids.append(u.id)

    if estate_id and unit_numbers:
        for num in unit_numbers:
            u = Unit.query.filter_by(
                estate_id=int(estate_id), unit_number=str(num)
            ).first()
            if u:
                apply_override_to_unit(u)
                updated_unit_ids.append(u.id)

    if not updated_unit_ids:
        return jsonify({"error": "No units matched"}), 400

    # Persist overrides
    overrides_str = json.dumps(overrides)
    if not setting:
        setting = SystemSetting(
            setting_key=setting_key,
            setting_type="json",
            setting_value=overrides_str,
            updated_by=getattr(current_user, "id", None),
        )
        from ...db import db

        db.session.add(setting)
        db.session.commit()
    else:
        from ...db import db

        setting.setting_value = overrides_str
        setting.updated_by = getattr(current_user, "id", None)
        db.session.commit()

    for uid in updated_unit_ids:
        log_action(
            "unit.rate_override.apply",
            entity_type="unit",
            entity_id=uid,
            new_values={"rate_table_id": rate_table_id},
        )

    return jsonify({"data": {"updated": updated_unit_ids}})


@api_v1.get("/api/units/overrides")
@login_required
def list_unit_overrides():
    import json

    setting_key = "unit_rate_overrides"
    setting: SystemSetting = SystemSetting.query.filter_by(
        setting_key=setting_key
    ).first()
    overrides = {}
    if setting and setting.setting_value:
        try:
            overrides = json.loads(setting.setting_value) or {}
        except Exception:
            overrides = {}
    return jsonify({"data": overrides})


@api_v1.post("/units")
@login_required
def create_unit():
    payload = request.get_json(force=True) or {}
    unit = Unit.create_from_payload(payload, user_id=getattr(current_user, "id", None))
    log_action("unit.create", entity_type="unit", entity_id=unit.id, new_values=payload)
    return jsonify({"data": unit.to_dict()}), 201


@api_v1.put("/units/<int:unit_id>")
@login_required
def update_unit(unit_id: int):
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    before = unit.to_dict()
    unit.update_from_payload(payload, user_id=getattr(current_user, "id", None))
    log_action(
        "unit.update",
        entity_type="unit",
        entity_id=unit_id,
        old_values=before,
        new_values=payload,
    )
    return jsonify({"data": unit.to_dict()})


@api_v1.delete("/units/<int:unit_id>")
@login_required
def delete_unit(unit_id: int):
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    unit.delete()
    log_action("unit.delete", entity_type="unit", entity_id=unit_id)
    return jsonify({"message": "Deleted"})
