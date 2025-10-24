from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Estate, Resident, Unit, Meter, RateTable
from ...utils.audit import log_action
from ...utils.pagination import paginate_query
from ...utils.decorators import requires_permission
from . import api_v1

from sqlalchemy import union, func


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

    from ...db import db

    elec_counts = dict(
        db.session.query(
            Unit.estate_id, func.count(Unit.electricity_meter_id.distinct())
        )
        .filter(Unit.electricity_meter_id.isnot(None))
        .group_by(Unit.estate_id)
        .all()
    )

    water_counts = dict(
        db.session.query(Unit.estate_id, func.count(Unit.water_meter_id.distinct()))
        .filter(Unit.water_meter_id.isnot(None))
        .group_by(Unit.estate_id)
        .all()
    )

    solar_counts = dict(
        db.session.query(Unit.estate_id, func.count(Unit.solar_meter_id.distinct()))
        .filter(Unit.solar_meter_id.isnot(None))
        .group_by(Unit.estate_id)
        .all()
    )

    meter_configs = {}
    for e in estates:
        eid = e["id"]
        has_bulk_e = e["bulk_electricity_meter_id"] is not None
        has_bulk_w = e["bulk_water_meter_id"] is not None
        meter_configs[eid] = {
            "elec": f"{elec_counts.get(eid, 0)} unit{' + 1 bulk' if has_bulk_e else ''}",
            "water": f"{water_counts.get(eid, 0)} unit{' + 1 bulk' if has_bulk_w else ''}",
            "solar": f"{solar_counts.get(eid, 0)} unit",
        }

    # Rate tables for dropdowns
    electricity_rate_tables = [
        rt.to_dict() for rt in RateTable.list_filtered(utility_type="electricity").all()
    ]
    water_rate_tables = [
        rt.to_dict() for rt in RateTable.list_filtered(utility_type="water").all()
    ]

    # Fetch bulk meter data for overview
    bulk_meters_data = []
    for estate in estates:
        estate_id = estate["id"]
        estate_name = estate["name"]

        # Get bulk electricity meter
        if estate["bulk_electricity_meter_id"]:
            bulk_elec_meter = Meter.get_by_id(estate["bulk_electricity_meter_id"])
            if bulk_elec_meter:
                bulk_meters_data.append(
                    {
                        "estate_id": estate_id,
                        "estate_name": estate_name,
                        "meter_id": bulk_elec_meter.id,
                        "meter_type": "Electricity",
                        "meter_type_icon": "fas fa-bolt",
                        "meter_type_color": "text-yellow-500",
                        "serial_number": bulk_elec_meter.serial_number,
                        "current_reading": bulk_elec_meter.last_reading,
                        "reading_unit": "kWh",
                        "status": bulk_elec_meter.communication_status,
                        "last_update": bulk_elec_meter.last_reading_date,
                        "last_communication": bulk_elec_meter.last_communication,
                    }
                )

        # Get bulk water meter
        if estate["bulk_water_meter_id"]:
            bulk_water_meter = Meter.get_by_id(estate["bulk_water_meter_id"])
            if bulk_water_meter:
                bulk_meters_data.append(
                    {
                        "estate_id": estate_id,
                        "estate_name": estate_name,
                        "meter_id": bulk_water_meter.id,
                        "meter_type": "Water",
                        "meter_type_icon": "fas fa-tint",
                        "meter_type_color": "text-blue-500",
                        "serial_number": bulk_water_meter.serial_number,
                        "current_reading": bulk_water_meter.last_reading,
                        "reading_unit": "kL",
                        "status": bulk_water_meter.communication_status,
                        "last_update": bulk_water_meter.last_reading_date,
                        "last_communication": bulk_water_meter.last_communication,
                    }
                )

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
        meter_configs=meter_configs,
        bulk_meters_data=bulk_meters_data,
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


@api_v1.route("/estates/<int:estate_id>/details", methods=["GET"])
@login_required
@requires_permission("estates.view")
def estate_details_page(estate_id: int):
    estate = Estate.get_by_id(estate_id)
    if not estate:
        return render_template("errors/404.html"), 404

    units_query = Unit.get_all(estate_id=estate_id)
    units, pagination = paginate_query(units_query)

    # Enrich units with resident, wallet balance
    enriched_units = []
    for u in units:
        resident = Resident.get_by_id(u.resident_id) if u.resident_id else None
        wallet = u.wallet
        balance = float(wallet.balance or 0) if wallet else 0
        enriched_units.append(
            {
                "unit": u.to_dict(),
                "resident": resident.to_dict() if resident else None,
                "wallet_balance": balance,
            }
        )

    # Stats
    total_units = estate.total_units or 0

    from ...db import db

    elec = db.session.query(Unit.electricity_meter_id).filter(
        Unit.estate_id == estate_id, Unit.electricity_meter_id.isnot(None)
    )

    water = db.session.query(Unit.water_meter_id).filter(
        Unit.estate_id == estate_id, Unit.water_meter_id.isnot(None)
    )

    solar = db.session.query(Unit.solar_meter_id).filter(
        Unit.estate_id == estate_id, Unit.solar_meter_id.isnot(None)
    )

    all_meter_ids = union(elec, water, solar).subquery()

    total_meters = (
        db.session.query(func.count()).select_from(all_meter_ids).scalar() or 0
    )

    elec_unit_count = (
        db.session.query(func.count(Unit.electricity_meter_id.distinct()))
        .filter(Unit.estate_id == estate_id, Unit.electricity_meter_id.isnot(None))
        .scalar()
        or 0
    )

    water_unit_count = (
        db.session.query(func.count(Unit.water_meter_id.distinct()))
        .filter(Unit.estate_id == estate_id, Unit.water_meter_id.isnot(None))
        .scalar()
        or 0
    )

    solar_unit_count = (
        db.session.query(func.count(Unit.solar_meter_id.distinct()))
        .filter(Unit.estate_id == estate_id, Unit.solar_meter_id.isnot(None))
        .scalar()
        or 0
    )

    has_bulk_elec = estate.bulk_electricity_meter_id is not None
    has_bulk_water = estate.bulk_water_meter_id is not None

    meter_config = {
        "elec": f"{elec_unit_count} unit{' + 1 bulk' if has_bulk_elec else ''}",
        "water": f"{water_unit_count} unit{' + 1 bulk' if has_bulk_water else ''}",
        "solar": f"{solar_unit_count} unit",
    }

    bulk_elec_meter = (
        Meter.get_by_id(estate.bulk_electricity_meter_id)
        if estate.bulk_electricity_meter_id
        else None
    )
    bulk_water_meter = (
        Meter.get_by_id(estate.bulk_water_meter_id)
        if estate.bulk_water_meter_id
        else None
    )
    elec_rate_table = (
        RateTable.get_by_id(estate.electricity_rate_table_id)
        if estate.electricity_rate_table_id
        else None
    )
    water_rate_table = (
        RateTable.get_by_id(estate.water_rate_table_id)
        if estate.water_rate_table_id
        else None
    )

    return render_template(
        "estates/estate_details.html",
        estate=estate.to_dict(),
        units=enriched_units,
        pagination=pagination,
        stats={"total_units": total_units, "total_meters": total_meters},
        bulk_elec_meter=bulk_elec_meter.to_dict() if bulk_elec_meter else None,
        bulk_water_meter=bulk_water_meter.to_dict() if bulk_water_meter else None,
        elec_rate_table=elec_rate_table.to_dict() if elec_rate_table else None,
        water_rate_table=water_rate_table.to_dict() if water_rate_table else None,
        meter_config=meter_config,
    )
