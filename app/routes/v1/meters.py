from __future__ import annotations

from datetime import datetime
from flask import jsonify, request, render_template
from flask_login import login_required

from ...models import Meter, MeterReading, Unit, Wallet, Estate, MeterAlert
from ...utils.pagination import paginate_query, parse_pagination_params
from . import api_v1


@api_v1.route("/meters", methods=["GET"])
@login_required
def meters_page():
    """Render the meters page with meters, unit assignments, balances, filters and stats."""
    meter_type = request.args.get("meter_type") or None
    comm_status = request.args.get("communication_status") or None
    estate_id = request.args.get("estate_id", type=int) or None
    credit_status = (
        request.args.get("credit_status") or None
    )  # 'low'|'disconnected'|'ok'

    # Base SQL query (filters that are simple go here)
    base_query = Meter.get_all(meter_type=meter_type, communication_status=comm_status)
    # Pull all to allow derived filters (estate via unit, credit via wallet) then paginate in Python
    all_meters = base_query.all()

    def meter_wallet_balance_for_type(w: Wallet | None, m: Meter) -> float:
        if not w:
            return 0.0
        if m.meter_type == "electricity":
            return float(w.electricity_balance)
        if m.meter_type == "water":
            return float(w.water_balance)
        if m.meter_type == "solar":
            return float(w.solar_balance)
        return float(w.balance or 0)

    meters_full = []
    for m in all_meters:
        # Find assigned unit (match any of the three fk columns)
        unit = Unit.query.filter(
            (Unit.electricity_meter_id == m.id)
            | (Unit.water_meter_id == m.id)
            | (Unit.solar_meter_id == m.id)
        ).first()
        # Estate filter via unit if requested
        if estate_id and (not unit or unit.estate_id != estate_id):
            continue

        wallet = Wallet.query.filter_by(unit_id=unit.id).first() if unit else None
        bal = meter_wallet_balance_for_type(wallet, m)
        threshold = (
            float(wallet.low_balance_threshold)
            if wallet and wallet.low_balance_threshold is not None
            else 50.0
        )
        derived_credit = (
            "disconnected" if bal <= 0 else ("low" if bal < threshold else "ok")
        )

        # Apply derived credit filter
        if credit_status and derived_credit != credit_status:
            continue

        meters_full.append(
            {
                **m.to_dict(),
                "unit": {
                    "id": unit.id,
                    "estate_id": unit.estate_id,
                    "estate_name": (
                        Estate.query.get(unit.estate_id).name
                        if unit.estate_id
                        else None
                    ),
                    "unit_number": unit.unit_number,
                    "occupancy_status": unit.occupancy_status,
                }
                if unit
                else None,
                "wallet": wallet.to_dict() if wallet else None,
                "credit_status": derived_credit,
            }
        )

    # Manual pagination on filtered list
    page, per_page = parse_pagination_params()
    total = len(meters_full)
    start = (page - 1) * per_page
    end = start + per_page
    meters = meters_full[start:end]
    pages = (total + per_page - 1) // per_page if per_page else 1
    next_page = page + 1 if page < pages else None
    prev_page = page - 1 if page > 1 else None
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "next_page": next_page,
        "prev_page": prev_page,
    }

    # Stats
    total_meters = Meter.count_all()
    total_active = Meter.query.filter(Meter.is_active == True).count()
    # Low credit meters: evaluate via associated wallets
    low_credit_count = 0
    for m in Meter.query.all():
        unit = Unit.query.filter(
            (Unit.electricity_meter_id == m.id)
            | (Unit.water_meter_id == m.id)
            | (Unit.solar_meter_id == m.id)
        ).first()
        if not unit:
            continue
        wallet = Wallet.query.filter_by(unit_id=unit.id).first()
        if not wallet:
            continue
        bal = meter_wallet_balance_for_type(wallet, m)
        threshold = (
            float(wallet.low_balance_threshold)
            if wallet.low_balance_threshold is not None
            else 50.0
        )
        if 0 < bal < threshold:
            low_credit_count += 1
    total_alerts = (
        MeterAlert.query.filter_by(is_resolved=False).count()
        if hasattr(MeterAlert, "is_resolved")
        else MeterAlert.query.count()
    )

    estates = [
        {"id": e.id, "name": e.name}
        for e in Estate.query.order_by(Estate.name.asc()).all()
    ]
    meter_types = [
        {"value": "electricity", "label": "Electricity"},
        {"value": "water", "label": "Water"},
        {"value": "solar", "label": "Solar"},
    ]

    return render_template(
        "meters/meters.html",
        meters=meters,
        estates=estates,
        meter_types=meter_types,
        pagination=meta,
        stats={
            "total": total_meters,
            "active": total_active,
            "low_credit": low_credit_count,
            "alerts": total_alerts,
        },
        current_filters={
            "estate_id": estate_id,
            "meter_type": meter_type,
            "communication_status": comm_status,
            "credit_status": credit_status,
        },
    )


@api_v1.route("/meters/<meter_id>/details", methods=["GET"])
@login_required
def meter_details_page(meter_id: str):
    """Render the meter details page"""
    return render_template("meters/meter-details.html", meter_id=meter_id)


# Removed separate list endpoint; logic consolidated into meters_page


@api_v1.get("/meters/<int:meter_id>")
@login_required
def get_meter(meter_id: int):
    meter = Meter.get_by_id(meter_id)
    if not meter:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": meter.to_dict()})


@api_v1.get("/meters/<int:meter_id>/readings")
@login_required
def meter_readings(meter_id: int):
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    query = MeterReading.list_for_meter(meter_id, start=start_dt, end=end_dt)
    items, meta = paginate_query(query)
    return jsonify({"data": [r.to_dict() for r in items], **meta})
