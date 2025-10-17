from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import RateTable, Estate, RateTableTier, TimeOfUseRate
from ...utils.pagination import paginate_query
from ...utils.rates import calculate_estate_bill
from ...utils.audit import log_action
from . import api_v1


@api_v1.route("/rate-tables", methods=["GET"])
@login_required
def rate_tables_page():
    """Render the rate tables page with available rate tables and estate assignments"""

    electricity_rate_tables = [
        rt.to_dict() for rt in RateTable.list_filtered(utility_type="electricity").all()
    ]
    water_rate_tables = [
        rt.to_dict() for rt in RateTable.list_filtered(utility_type="water").all()
    ]
    # All rate tables (any utility)
    raw_rate_tables = RateTable.list_filtered().all()
    all_rate_tables = [r.to_dict() for r in raw_rate_tables]

    rate_table_id_to_tiers = {}
    rate_table_id_to_tou = {}
    for rt in raw_rate_tables:
        tiers = (
            RateTableTier.query.filter_by(rate_table_id=rt.id)
            .order_by(RateTableTier.tier_number.asc())
            .all()
        )
        rate_table_id_to_tiers[rt.id] = [
            {
                "tier_number": t.tier_number,
                "from": float(t.from_kwh or 0),
                "to": float(t.to_kwh) if t.to_kwh is not None else None,
                "rate": float(t.rate_per_kwh or 0),
                "description": t.description,
            }
            for t in tiers
        ]
        tou_periods = (
            TimeOfUseRate.query.filter_by(rate_table_id=rt.id)
            .order_by(TimeOfUseRate.start_time.asc())
            .all()
        )
        rate_table_id_to_tou[rt.id] = [
            {
                "period_name": p.period_name,
                "start_time": p.start_time.strftime("%H:%M"),
                "end_time": p.end_time.strftime("%H:%M"),
                "weekdays": bool(p.weekdays),
                "weekends": bool(p.weekends),
                "rate": float(p.rate_per_kwh or 0),
            }
            for p in tou_periods
        ]

    estates = [e.to_dict() for e in Estate.get_all().order_by(Estate.name.asc()).all()]

    return render_template(
        "rate-tables/rate-table.html",
        rate_tables=all_rate_tables,
        rate_table_tiers=rate_table_id_to_tiers,
        time_of_use_rates=rate_table_id_to_tou,
        estates=estates,
        electricity_rate_tables=electricity_rate_tables,
        water_rate_tables=water_rate_tables,
    )


@api_v1.route("/rate-tables/builder", methods=["GET"])
@login_required
def rate_table_builder_page():
    """Render the rate table builder page"""
    return render_template("rate-tables/rate-table-builder.html")


@api_v1.route("/rate-tables/<int:rate_table_id>/edit", methods=["GET"])
@login_required
def rate_table_edit_page(rate_table_id: int):
    """Render the edit page for a specific rate table"""
    rt = RateTable.get_by_id(rate_table_id)
    if not rt:
        return render_template("errors/404.html"), 404
    # Provide initial dict; page JS will fetch full details (tiers/TOU)
    return render_template(
        "rate-tables/edit-rate-table.html",
        rate_table=rt.to_dict(),
    )


@api_v1.get("/api/rate-tables")
@login_required
def list_rate_tables():
    utility_type = request.args.get("utility_type")
    is_active = request.args.get("is_active")
    is_active_bool = None
    if is_active is not None:
        is_active_bool = is_active.lower() in ("1", "true", "yes")
    query = RateTable.list_filtered(utility_type=utility_type, is_active=is_active_bool)
    items, meta = paginate_query(query)
    return jsonify({"data": [r.to_dict() for r in items], **meta})


@api_v1.get("/api/rate-tables/<int:rate_table_id>")
@login_required
def get_rate_table(rate_table_id: int):
    rt = RateTable.get_by_id(rate_table_id)
    if not rt:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": rt.to_dict()})


@api_v1.get("/api/rate-tables/<int:rate_table_id>/details")
@login_required
def get_rate_table_details(rate_table_id: int):
    rt = RateTable.get_by_id(rate_table_id)
    if not rt:
        return jsonify({"error": "Not Found", "code": 404}), 404
    tiers = (
        RateTableTier.query.filter_by(rate_table_id=rt.id)
        .order_by(RateTableTier.tier_number.asc())
        .all()
    )
    tou = (
        TimeOfUseRate.query.filter_by(rate_table_id=rt.id)
        .order_by(TimeOfUseRate.start_time.asc())
        .all()
    )
    return jsonify(
        {
            "data": {
                **rt.to_dict(),
                "tiers": [
                    {
                        "tier_number": t.tier_number,
                        "from": float(t.from_kwh or 0),
                        "to": float(t.to_kwh) if t.to_kwh is not None else None,
                        "rate": float(t.rate_per_kwh or 0),
                        "description": t.description,
                    }
                    for t in tiers
                ],
                "time_of_use": [
                    {
                        "period_name": p.period_name,
                        "start_time": p.start_time.strftime("%H:%M"),
                        "end_time": p.end_time.strftime("%H:%M"),
                        "weekdays": bool(p.weekdays),
                        "weekends": bool(p.weekends),
                        "rate": float(p.rate_per_kwh or 0),
                    }
                    for p in tou
                ],
            }
        }
    )


@api_v1.post("/api/rate-tables")
@login_required
def create_rate_table():
    payload = request.get_json(force=True) or {}
    required = ["name", "utility_type", "rate_structure", "effective_from"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Normalize rate_structure to JSON string for storage
    import json

    try:
        structure = payload.get("rate_structure")
        if isinstance(structure, str):
            json.loads(structure)  # validate
            rate_structure_str = structure
        else:
            rate_structure_str = json.dumps(structure or {})
    except Exception as e:
        return jsonify({"error": f"Invalid rate_structure: {e}"}), 400

    from ...db import db

    rt = RateTable(
        name=payload["name"],
        utility_type=payload["utility_type"],
        rate_structure=rate_structure_str,
        is_default=bool(payload.get("is_default", False)),
        effective_from=payload["effective_from"],
        effective_to=payload.get("effective_to"),
        category=payload.get("category"),
        description=payload.get("description"),
        is_active=bool(payload.get("is_active", True)),
        created_by=getattr(current_user, "id", None),
    )
    db.session.add(rt)
    db.session.commit()

    log_action(
        "rate_table.create",
        entity_type="rate_table",
        entity_id=rt.id,
        new_values=rt.to_dict(),
    )
    return jsonify({"data": rt.to_dict()}), 201


@api_v1.post("/api/rate-tables/preview")
@login_required
def rate_preview():
    payload = request.get_json(force=True) or {}
    # Inputs: estate fields and two rate table structures by id (optional) or inline
    electricity_kwh = float(payload.get("electricity_kwh") or 0)
    water_kl = float(payload.get("water_kl") or 0)
    service_fee = float(payload.get("service_fee") or 0)

    electricity_rate_table_id = payload.get("electricity_rate_table_id")
    water_rate_table_id = payload.get("water_rate_table_id")
    electricity_structure = payload.get("electricity_structure")
    water_structure = payload.get("water_structure")
    electricity_markup = payload.get("electricity_markup_percentage")
    water_markup = payload.get("water_markup_percentage")

    # Helper: build a computable structure (with 'tiers') from DB tiers if available
    def structure_from_db(rt_id: int):
        tiers = (
            RateTableTier.query.filter_by(rate_table_id=rt_id)
            .order_by(RateTableTier.tier_number.asc())
            .all()
        )
        if tiers:
            return {
                "tiers": [
                    {
                        "from": float(t.from_kwh or 0),
                        "to": float(t.to_kwh) if t.to_kwh is not None else None,
                        "rate": float(t.rate_per_kwh or 0),
                    }
                    for t in tiers
                ]
            }
        # fallback to stored JSON if already in consumable format
        rt = RateTable.get_by_id(int(rt_id))
        if not rt:
            return {}
        rs = rt.to_dict().get("rate_structure") or {}
        if isinstance(rs, dict) and ("tiers" in rs or "flat_rate" in rs):
            return rs
        return {}

    # Resolve structures from DB if ids given
    if electricity_rate_table_id and not electricity_structure:
        electricity_structure = structure_from_db(int(electricity_rate_table_id))
    if water_rate_table_id and not water_structure:
        water_structure = structure_from_db(int(water_rate_table_id))

    breakdown = calculate_estate_bill(
        electricity_kwh=electricity_kwh,
        water_kl=water_kl,
        electricity_structure=electricity_structure,
        water_structure=water_structure,
        electricity_markup_percent=electricity_markup,
        water_markup_percent=water_markup,
        service_fee=service_fee,
    )
    return jsonify({"data": breakdown})


@api_v1.put("/api/rate-tables/<int:rate_table_id>")
@login_required
def update_rate_table(rate_table_id: int):
    try:
        rt = RateTable.get_by_id(rate_table_id)
        if not rt:
            return jsonify({"error": "Not Found"}), 404

        payload = request.get_json(force=True) or {}
        print(f"Updating rate table {rate_table_id} with payload:", payload)

        before = rt.to_dict()
        for f in [
            "name",
            "utility_type",
            "rate_structure",
            "is_default",
            "effective_from",
            "effective_to",
            "category",
            "description",
            "is_active",
        ]:
            if f in payload:
                if f == "rate_structure" and isinstance(payload[f], dict):
                    # Convert dict to JSON string for database storage
                    import json

                    setattr(rt, f, json.dumps(payload[f]))
                else:
                    setattr(rt, f, payload[f])

        from ...db import db

        rt.updated_by = getattr(current_user, "id", None)
        db.session.commit()

        log_action(
            "rate_table.update",
            entity_type="rate_table",
            entity_id=rt.id,
            old_values=before,
            new_values=payload,
        )
        return jsonify({"data": rt.to_dict()})
    except Exception as e:
        print(f"Error updating rate table {rate_table_id}:", str(e))
        return jsonify({"error": str(e)}), 500


@api_v1.delete("/api/rate-tables/<int:rate_table_id>")
@login_required
def delete_rate_table(rate_table_id: int):
    rt = RateTable.get_by_id(rate_table_id)
    if not rt:
        return jsonify({"error": "Not Found"}), 404
    # Block delete if linked to estates
    in_use = (
        Estate.query.filter(
            (Estate.electricity_rate_table_id == rate_table_id)
            | (Estate.water_rate_table_id == rate_table_id)
        ).count()
        > 0
    )
    if in_use:
        return jsonify({"error": "Cannot delete rate table assigned to estates"}), 409
    from ...db import db

    before = rt.to_dict()
    db.session.delete(rt)
    db.session.commit()
    log_action(
        "rate_table.delete",
        entity_type="rate_table",
        entity_id=rate_table_id,
        old_values=before,
    )
    return jsonify({"message": "Deleted"})
