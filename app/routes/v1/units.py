from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Unit, Estate, Resident, Meter, RateTable, SystemSetting
from ...utils.pagination import paginate_query
from ...utils.audit import log_action
from ...utils.decorators import requires_permission
from . import api_v1
from ...utils.rates import calculate_estate_bill


@api_v1.route("/units", methods=["GET"])
@login_required
@requires_permission("units.view")
def units_page():
    """Render the units page with units, estates, filters and pagination."""
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

    # Preload resident names
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
@requires_permission("units.view")
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
@requires_permission("units.view")
def wallet_statement_page(unit_id: str):
    """Render the wallet statement page"""
    from ...models import Unit, Wallet, Estate, Transaction
    from ...db import db
    from sqlalchemy import func

    # Get unit and wallet data
    unit = Unit.query.filter_by(unit_number=unit_id).first()
    if not unit:
        return "Unit not found", 404

    wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    if not wallet:
        return "Wallet not found", 404

    estate = Estate.query.get(unit.estate_id)

    # Get recent transactions for this wallet
    transactions = (
        Transaction.query.filter_by(wallet_id=wallet.id)
        .order_by(Transaction.completed_at.desc())
        .limit(50)
        .all()
    )

    # Get last topup date
    last_topup = (
        Transaction.query.filter_by(
            wallet_id=wallet.id, transaction_type="topup", status="completed"
        )
        .order_by(Transaction.completed_at.desc())
        .first()
    )

    return render_template(
        "wallets/wallet-statement.html",
        unit=unit,
        wallet=wallet,
        estate=estate,
        transactions=transactions,
        last_topup_date=last_topup.completed_at if last_topup else None,
    )


@api_v1.route("/units/<int:unit_id>/visual", methods=["GET"])
@login_required
@requires_permission("units.view")
def unit_visual_page(unit_id: int):
    """Render the unit visual diagram page"""
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return render_template("errors/404.html"), 404

    return render_template("units/unit-visual.html", unit=unit)


@api_v1.route("/units/<int:unit_id>", methods=["GET"])
@login_required
@requires_permission("units.view")
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
@requires_permission("units.view")
def get_unit(unit_id: int):
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": unit.to_dict()})


@api_v1.post("/api/units/overrides")
@login_required
@requires_permission("units.edit")
def apply_unit_overrides():
    """Apply a rate table override to a list of units by id or by estate+unit_numbers list."""
    payload = request.get_json(force=True) or {}
    rate_table_id = payload.get("rate_table_id")
    utility_type = payload.get("utility_type", "electricity")

    if not rate_table_id:
        return jsonify({"error": "rate_table_id is required"}), 400

    rt = RateTable.get_by_id(int(rate_table_id))
    if not rt:
        return jsonify({"error": "Invalid rate_table_id"}), 400

    unit_ids = payload.get("unit_ids") or []
    estate_id = payload.get("estate_id")
    unit_numbers = payload.get("unit_numbers") or []

    updated_unit_ids = []

    def apply_override_to_unit(unit_obj: Unit):
        if utility_type == "electricity":
            unit_obj.electricity_rate_table_id = int(rate_table_id)
        elif utility_type == "water":
            unit_obj.water_rate_table_id = int(rate_table_id)

        unit_obj.update_from_payload({}, current_user.id)
        updated_unit_ids.append(unit_obj.id)

    if unit_ids:
        for uid in unit_ids:
            u = Unit.get_by_id(int(uid))
            if u:
                apply_override_to_unit(u)

    if estate_id and unit_numbers:
        for num in unit_numbers:
            u = Unit.query.filter_by(
                estate_id=int(estate_id), unit_number=str(num)
            ).first()
            if u:
                apply_override_to_unit(u)

    if not updated_unit_ids:
        return jsonify({"error": "No units matched"}), 400

    log_action(
        "unit.rate_override.apply",
        entity_type="unit",
        entity_id=None,
        new_values={
            "rate_table_id": int(rate_table_id),
            "utility_type": utility_type,
            "updated_unit_ids": updated_unit_ids,
        },
    )

    return jsonify(
        {
            "message": f"Rate table override applied to {len(updated_unit_ids)} units",
            "updated_unit_ids": updated_unit_ids,
        }
    )


@api_v1.get("/api/units/overrides")
@login_required
@requires_permission("units.view")
def list_unit_overrides():
    """Get all units with rate table overrides (non-null rate table IDs)"""
    from ...db import db

    # Get all units that have rate table overrides
    units_with_overrides = Unit.query.filter(
        db.or_(
            Unit.electricity_rate_table_id.isnot(None),
            Unit.water_rate_table_id.isnot(None),
        )
    ).all()

    overrides = {}
    for unit in units_with_overrides:
        unit_data = {
            "unit_id": unit.id,
            "unit_number": unit.unit_number,
            "estate_id": unit.estate_id,
            "electricity_rate_table_id": unit.electricity_rate_table_id,
            "water_rate_table_id": unit.water_rate_table_id,
        }
        overrides[str(unit.id)] = unit_data

    return jsonify({"data": overrides})


@api_v1.delete("/api/units/overrides")
@login_required
@requires_permission("units.edit")
def remove_unit_overrides():
    """Remove rate table overrides from units (set to None to inherit from estate)"""
    payload = request.get_json(force=True) or {}
    utility_type = payload.get("utility_type", "electricity")

    unit_ids = payload.get("unit_ids") or []
    estate_id = payload.get("estate_id")
    unit_numbers = payload.get("unit_numbers") or []

    updated_unit_ids = []

    def remove_override_from_unit(unit_obj: Unit):
        if utility_type == "electricity":
            unit_obj.electricity_rate_table_id = None
        elif utility_type == "water":
            unit_obj.water_rate_table_id = None

        unit_obj.update_from_payload({}, current_user.id)
        updated_unit_ids.append(unit_obj.id)

    if unit_ids:
        for uid in unit_ids:
            u = Unit.get_by_id(int(uid))
            if u:
                remove_override_from_unit(u)

    if estate_id and unit_numbers:
        for num in unit_numbers:
            u = Unit.query.filter_by(
                estate_id=int(estate_id), unit_number=str(num)
            ).first()
            if u:
                remove_override_from_unit(u)

    if not updated_unit_ids:
        return jsonify({"error": "No units matched"}), 400

    log_action(
        "unit.rate_override.remove",
        entity_type="unit",
        entity_id=None,
        new_values={
            "utility_type": utility_type,
            "updated_unit_ids": updated_unit_ids,
        },
    )

    return jsonify(
        {
            "message": f"Rate table override removed from {len(updated_unit_ids)} units",
            "updated_unit_ids": updated_unit_ids,
        }
    )


@api_v1.post("/units")
@login_required
@requires_permission("units.create")
def create_unit():
    payload = request.get_json(force=True) or {}
    unit = Unit.create_from_payload(payload, user_id=getattr(current_user, "id", None))
    log_action("unit.create", entity_type="unit", entity_id=unit.id, new_values=payload)
    return jsonify({"data": unit.to_dict()}), 201


@api_v1.put("/units/<int:unit_id>")
@login_required
@requires_permission("units.edit")
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
@requires_permission("units.delete")
def delete_unit(unit_id: int):
    unit = Unit.get_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    unit.delete()
    log_action("unit.delete", entity_type="unit", entity_id=unit_id)
    return jsonify({"message": "Deleted"})
