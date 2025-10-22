from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required

from . import api_v1
from app.models import MeterReading, Transaction, Estate, Meter, Unit
from datetime import datetime, timedelta
from sqlalchemy import func, extract, case, or_
from app.db import db
from ...utils.pagination import parse_pagination_params


@api_v1.route("/reports", methods=["GET"])
@login_required
def reports_page():
    """Render the reports page with real KPI data where available"""
    # Filters (defaults to current month)
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    estate_id = request.args.get("estate_id", type=int)

    # Electricity consumption this month (kWh) from meter_readings.consumption_since_last
    electricity_total_kwh_query = (
        MeterReading.query.with_entities(
            func.coalesce(func.sum(MeterReading.consumption_since_last), 0)
        )
        .filter(MeterReading.reading_date >= month_start)
        .filter(MeterReading.reading_date < next_month)
    )
    if estate_id:
        electricity_total_kwh_query = (
            electricity_total_kwh_query.join(Meter, Meter.id == MeterReading.meter_id)
            .join(Unit, Unit.electricity_meter_id == Meter.id)
            .filter(Unit.estate_id == estate_id)
        )
    electricity_total_kwh_value = electricity_total_kwh_query.scalar() or 0

    # Revenue this month from completed transactions (amount)
    revenue_total_amount = (
        Transaction.query.with_entities(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.status == "completed")
        .filter(Transaction.completed_at != None)
        .filter(Transaction.completed_at >= month_start)
        .filter(Transaction.completed_at < next_month)
    ).scalar() or 0

    # Water usage placeholder (no water model yet) – use electricity_total_kwh to avoid blanks
    water_total_liters = 0

    # Solar generation placeholder (depends on solar readings model)
    solar_total_kwh = 0

    # Build monthly consumption trend for current year (electricity kWh by month)
    year_start = today.replace(month=1, day=1)
    months = list(range(1, 13))
    monthly_kwh_by_month = {m: 0.0 for m in months}

    monthly_query = (
        MeterReading.query.with_entities(
            extract("month", MeterReading.reading_date).label("month"),
            func.coalesce(func.sum(MeterReading.consumption_since_last), 0).label(
                "kwh"
            ),
        )
        .filter(MeterReading.reading_date >= year_start)
        .filter(MeterReading.reading_date < next_month)
    )
    if estate_id:
        monthly_query = (
            monthly_query.join(Meter, Meter.id == MeterReading.meter_id)
            .join(Unit, Unit.electricity_meter_id == Meter.id)
            .filter(Unit.estate_id == estate_id)
        )
    monthly_query = monthly_query.group_by("month").order_by("month")
    for row in monthly_query:  # row.month is 1-12
        m = int(row.month)
        monthly_kwh_by_month[m] = float(row.kwh or 0)

    # Monthly chart (system-wide, by type)
    monthly_query = (
        db.session.query(
            extract("month", MeterReading.reading_date).label("month"),
            Meter.meter_type,
            func.sum(MeterReading.consumption_since_last).label("total"),
        )
        .join(Meter, Meter.id == MeterReading.meter_id)
        .filter(MeterReading.reading_date >= year_start)
        .filter(MeterReading.reading_date < next_month)
        .group_by("month", Meter.meter_type)
        .order_by("month")
    ).all()

    monthly_elec = {m: 0.0 for m in months}
    monthly_water = {m: 0.0 for m in months}
    monthly_solar = {m: 0.0 for m in months}

    for row in monthly_query:
        m = int(row.month)
        total = float(row.total or 0)
        if row.meter_type == "electricity":
            monthly_elec[m] = total
        elif row.meter_type == "water":
            monthly_water[m] = total * 100  # Assume kL to L, adjust as needed
        elif row.meter_type == "solar":
            monthly_solar[m] = total

    has_monthly_data = (
        any(monthly_elec.values())
        or any(monthly_water.values())
        or any(monthly_solar.values())
    )

    monthly_chart = {
        "labels": [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        "electricity_kwh": [monthly_elec[m] for m in months],
        "water_hl": [monthly_water[m] / 10 for m in months],  # Example scaling
        "solar_kwh": [monthly_solar[m] for m in months],
        "no_data": not has_monthly_data,
    }

    # Estate comparison (current month, by estate and type)
    estates = Estate.query.filter_by(is_active=True).all()
    estate_datasets = []
    colors = ["#1A73E8", "#34A853", "#FBBC04", "#EA4335", "#4285F4"]  # Example colors

    for idx, estate in enumerate(estates):
        estate_sums = (
            db.session.query(
                Meter.meter_type,
                func.sum(MeterReading.consumption_since_last).label("total"),
            )
            .join(Meter, Meter.id == MeterReading.meter_id)
            .join(
                Unit,
                or_(
                    Unit.electricity_meter_id == Meter.id,
                    Unit.water_meter_id == Meter.id,
                    Unit.solar_meter_id == Meter.id,
                ),
            )
            .filter(Unit.estate_id == estate.id)
            .filter(MeterReading.reading_date >= month_start)
            .filter(MeterReading.reading_date < next_month)
            .group_by(Meter.meter_type)
            .all()
        )

        elec = next(
            (float(s.total or 0) for s in estate_sums if s.meter_type == "electricity"),
            0,
        )
        water = next(
            (float(s.total or 0) * 100 for s in estate_sums if s.meter_type == "water"),
            0,
        )  # kL to L
        solar = next(
            (float(s.total or 0) for s in estate_sums if s.meter_type == "solar"), 0
        )

        estate_datasets.append(
            {
                "label": estate.name,
                "data": [elec, water, solar],
                "backgroundColor": colors[idx % len(colors)],
            }
        )

    has_estate_data = bool(estate_datasets and any(d["data"] for d in estate_datasets))

    estate_comparison = {
        "labels": ["Electricity (kWh)", "Water (L)", "Solar (kWh)"],
        "datasets": estate_datasets,
        "no_data": not has_estate_data,
    }

    detailed_report = []
    units = (
        Unit.query.join(Estate)
        .filter(Unit.is_active == True, Estate.is_active == True)
        .order_by(Estate.name, Unit.unit_number)
        .all()
    )

    for unit in units:
        unit_sums = (
            db.session.query(
                Meter.meter_type,
                func.sum(MeterReading.consumption_since_last).label("total"),
            )
            .join(MeterReading, MeterReading.meter_id == Meter.id)
            .filter(
                or_(
                    Meter.id == unit.electricity_meter_id,
                    Meter.id == unit.water_meter_id,
                    Meter.id == unit.solar_meter_id,
                )
            )
            .filter(MeterReading.reading_date >= month_start)
            .filter(MeterReading.reading_date < next_month)
            .group_by(Meter.meter_type)
            .all()
        )

        elec_kwh = next(
            (float(s.total or 0) for s in unit_sums if s.meter_type == "electricity"), 0
        )
        water_l = next(
            (float(s.total or 0) * 100 for s in unit_sums if s.meter_type == "water"), 0
        )
        solar_kwh = next(
            (float(s.total or 0) for s in unit_sums if s.meter_type == "solar"), 0
        )

        wallet = unit.wallet
        balance = float(wallet.balance or 0) if wallet else 0

        if not wallet:
            payments = 0
        else:
            payments = (
                db.session.query(func.sum(Transaction.amount))
                .filter(Transaction.wallet_id == wallet.id)
                .filter(Transaction.status == "completed")
                .filter(Transaction.transaction_type == "topup")
                .filter(Transaction.completed_at >= month_start)
                .filter(Transaction.completed_at < next_month)
                .scalar()
                or 0
            )

        # Placeholder cost calc (fetch unit/estate rates in future)
        total_cost = elec_kwh * 2 + water_l * 0.01 + solar_kwh * 1.5

        detailed_report.append(
            {
                "unit_number": unit.unit_number,
                "estate_name": unit.estate.name if unit.estate else "Unassigned",
                "elec_kwh": elec_kwh,
                "water_l": water_l,
                "solar_kwh": solar_kwh,
                "total_cost": total_cost,
                "payments": payments,
                "balance": balance,
            }
        )

    has_detailed_data = bool(
        detailed_report
        and any(
            r["elec_kwh"] or r["water_l"] or r["solar_kwh"] for r in detailed_report
        )
    )

    page, per_page = parse_pagination_params()  # Defaults to 1, 10 if not in args
    total = len(detailed_report) if not has_detailed_data else 0
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = detailed_report[start:end] if not has_detailed_data else []

    detailed_report_dict = {
        "data": paginated_data,
        "no_data": not has_detailed_data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if per_page else 1,
        "next_page": page + 1 if end < total else None,
        "prev_page": page - 1 if start > 0 else None,
        "start_display": (page - 1) * per_page + 1 if total > 0 else 0,
        "end_display": min(page * per_page, total) if not has_detailed_data else 0,
    }

    # Quick Insights
    peak_query = (
        db.session.query(
            extract("hour", MeterReading.reading_date).label("hour"),
            func.sum(MeterReading.consumption_since_last).label("total"),
        )
        .join(Meter, Meter.id == MeterReading.meter_id)
        .filter(Meter.meter_type == "electricity")
        .filter(MeterReading.reading_date >= month_start)
        .filter(MeterReading.reading_date < next_month)
        .group_by("hour")
        .order_by(func.sum(MeterReading.consumption_since_last).desc())
        .first()
    )

    peak_time = (
        f"{int(peak_query.hour) if peak_query else 'N/A'}:00 - {int(peak_query.hour) + 1 if peak_query else 'N/A'}:00"
        if peak_query and (peak_query.total or 0) > 0
        else "No data"
    )

    efficient_unit = (
        db.session.query(
            Unit.unit_number, func.sum(MeterReading.consumption_since_last).label("kwh")
        )
        .join(Meter, Meter.id == Unit.electricity_meter_id)
        .join(MeterReading, MeterReading.meter_id == Meter.id)
        .filter(MeterReading.reading_date >= month_start)
        .filter(MeterReading.reading_date < next_month)
        .group_by(Unit.id, Unit.unit_number)
        .order_by("kwh")
        .first()
    )

    most_efficient = (
        f"{efficient_unit.unit_number} - {float(efficient_unit.kwh or 0):.0f} kWh/month"
        if efficient_unit
        else "No data"
    )

    total_units = db.session.query(func.count(Unit.id.distinct())).scalar() or 1
    subq = (
        db.session.query(func.sum(MeterReading.consumption_since_last).label("total"))
        .join(Meter, Meter.id == MeterReading.meter_id)
        .filter(
            Meter.meter_type == "electricity", MeterReading.reading_date >= month_start
        )
        .group_by(Meter.id)
    ).subquery()

    avg_elec = db.session.query(func.avg(subq.c.total)).scalar() or 0
    avg_elec = float(avg_elec)
    high_query = (
        db.session.query(
            Unit.unit_number, func.sum(MeterReading.consumption_since_last).label("kwh")
        )
        .join(Meter, Meter.id == Unit.electricity_meter_id)
        .join(MeterReading, MeterReading.meter_id == Meter.id)
        .filter(MeterReading.reading_date >= month_start)
        .filter(MeterReading.reading_date < next_month)
        .group_by(Unit.id, Unit.unit_number)
        .having(func.sum(MeterReading.consumption_since_last) > avg_elec * 1.2)
        .order_by(func.sum(MeterReading.consumption_since_last).desc())
        .first()
    )

    high_alert = (
        f"{high_query.unit_number} - {((high_query.kwh / avg_elec - 1) * 100):.0f}% above average"
        if high_query
        else "No alerts"
    )

    # Solar contribution %
    total_elec_solar = electricity_total_kwh_value + solar_total_kwh
    solar_contrib = (
        (solar_total_kwh / total_elec_solar * 100) if total_elec_solar > 0 else 0
    )
    solar_str = f"{solar_contrib:.0f}% of total electricity usage"

    has_insights = bool(
        peak_query or efficient_unit or high_query or solar_total_kwh > 0
    )

    quick_insights = {
        "peak_time": peak_time,
        "most_efficient": most_efficient,
        "high_alert": high_alert,
        "solar_contrib": solar_str,
        "no_data": not has_insights,
    }

    return render_template(
        "reports/reports.html",
        kpis={
            "electricity_total_kwh": float(electricity_total_kwh_value),
            "revenue_total_amount": float(revenue_total_amount),
            "water_total_liters": float(water_total_liters),
            "solar_total_kwh": float(solar_total_kwh),
            "period_label": "This month",
        },
        monthly_chart=monthly_chart,
        estate_comparison=estate_comparison,
        detailed_report=detailed_report_dict,
        estates=estates,
        quick_insights=quick_insights,
    )


@api_v1.get("/reports/estate-consumption")
@login_required
def report_estate_consumption():
    # Placeholder - real implementation would query aggregation views
    estate_id = request.args.get("estate_id")
    return jsonify({"data": {"estate_id": estate_id, "summary": {}}})


@api_v1.get("/reports/reconciliation")
@login_required
def report_reconciliation():
    estate_id = request.args.get("estate_id")
    date = request.args.get("date")
    utility_type = request.args.get("utility_type")
    return jsonify(
        {"data": {"estate_id": estate_id, "date": date, "utility_type": utility_type}}
    )


@api_v1.get("/reports/low-credit")
@login_required
def report_low_credit():
    estate_id = request.args.get("estate_id")
    threshold = request.args.get("threshold", type=float, default=50.0)
    return jsonify({"data": [], "threshold": threshold, "estate_id": estate_id})


@api_v1.get("/reports/revenue")
@login_required
def report_revenue():
    return jsonify({"data": {}})
