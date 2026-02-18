from __future__ import annotations

from flask import jsonify, request, render_template, send_file
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, extract, case, or_, and_, desc, asc
from sqlalchemy.orm import joinedload
import csv
import io
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from . import api_v1
from app.models import (
    MeterReading,
    Transaction,
    Estate,
    Meter,
    Unit,
    Wallet,
    Notification,
    MeterAlert,
    Person,
    UnitTenancy,
)
from app.db import db
from ...utils.pagination import parse_pagination_params


@api_v1.route("/reports", methods=["GET"])
@login_required
def reports_page():
    """Main reports page with category navigation"""
    # Get filter parameters
    category = request.args.get("category", "consumption")
    estate_id = request.args.get("estate_id", type=int)
    date_range = request.args.get("date_range", "current_month")
    meter_type = request.args.get("meter_type", "all")

    # Get pagination parameters for different tables
    unit_page = request.args.get("unit_page", 1, type=int)
    top_page = request.args.get("top_page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Calculate date range
    today = datetime.now().date()
    if date_range == "current_month":
        start_date = today.replace(day=1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month - timedelta(days=1)
    elif date_range == "previous_month":
        first_this_month = today.replace(day=1)
        end_date = first_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif date_range == "past_3_months":
        start_date = today - timedelta(days=90)
        end_date = today
    elif date_range == "year_to_date":
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        start_date = today.replace(day=1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month - timedelta(days=1)

    # Get estates
    estates = Estate.query.filter_by(is_active=True).order_by(Estate.name).all()

    # Get report data based on category
    report_data = {}

    if category == "consumption":
        report_data = get_consumption_reports(
            start_date, end_date, estate_id, meter_type, unit_page, top_page, per_page
        )
    elif category == "financial":
        report_data = get_financial_reports(
            start_date, end_date, estate_id, unit_page, per_page
        )
    elif category == "system":
        report_data = get_system_status_reports(
            start_date, end_date, estate_id, unit_page, per_page
        )
    elif category == "estate":
        report_data = get_estate_level_reports(
            start_date, end_date, estate_id, unit_page, per_page
        )

    # Ensure all report data has proper default values
    for key, value in report_data.items():
        if value is None:
            report_data[key] = []

    return render_template(
        "reports/reports.html",
        category=category,
        estates=estates,
        current_estate=estate_id,
        current_date_range=date_range,
        current_meter_type=meter_type,
        unit_page=unit_page,
        top_page=top_page,
        start_date=start_date,
        end_date=end_date,
        datetime=datetime,
        **report_data,
    )


def get_consumption_reports(
    start_date, end_date, estate_id, meter_type, unit_page=1, top_page=1, per_page=10
):
    """Get consumption report data"""
    reports = {
        "unit_consumption": [],
        "bulk_sub_comparison": [],
        "top_consumers_electricity": [],
        "top_consumers_water": [],
        "top_consumers_hot_water": [],
        "top_consumers_solar": [],
        "solar_generation_vs_usage": [],
        "daily_consumption_trend": [],
    }

    # Unit Consumption Summary
    unit_consumption_query = (
        db.session.query(
            Unit.unit_number,
            Estate.name.label("estate_name"),
            func.sum(
                case(
                    (
                        Meter.meter_type == "electricity",
                        MeterReading.consumption_since_last,
                    ),
                    else_=0,
                )
            ).label("electricity_kwh"),
            func.sum(
                case(
                    (Meter.meter_type == "water", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("water_kL"),
            func.sum(
                case(
                    (
                        Meter.meter_type == "hot_water",
                        MeterReading.consumption_since_last,
                    ),
                    else_=0,
                )
            ).label("hot_water_kL"),
            func.sum(
                case(
                    (Meter.meter_type == "solar", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("solar_kwh"),
        )
        .join(Estate, Unit.estate_id == Estate.id)
        .outerjoin(
            Meter,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
            ),
        )
        .outerjoin(
            MeterReading,
            and_(
                MeterReading.meter_id == Meter.id,
                MeterReading.reading_date >= start_date,
                MeterReading.reading_date <= end_date,
            ),
        )
        .filter(Unit.is_active == True)
        .group_by(Unit.id, Unit.unit_number, Estate.name)
    )

    if estate_id:
        unit_consumption_query = unit_consumption_query.filter(
            Unit.estate_id == estate_id
        )

    total_count = unit_consumption_query.count()
    paginated_query = unit_consumption_query.offset((unit_page - 1) * per_page).limit(
        per_page
    )

    reports["unit_consumption"] = paginated_query.all()
    reports["unit_consumption_pagination"] = {
        "total": total_count,
        "page": unit_page,
        "per_page": per_page,
        "pages": (total_count + per_page - 1),
        "has_prev": unit_page > 1,
        "has_next": unit_page * per_page < total_count,
    }

    # Bulk vs Sub-Meter Comparison
    bulk_sub_comparison = []
    estates_to_check = Estate.query.filter_by(is_active=True)
    if estate_id:
        estates_to_check = estates_to_check.filter(Estate.id == estate_id)

    for estate in estates_to_check:
        # Bulk meter readings
        bulk_electricity = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(Meter.id == estate.bulk_electricity_meter_id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        bulk_water = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(Meter.id == estate.bulk_water_meter_id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        # Sub-meter totals
        sub_electricity = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .join(Unit, Unit.electricity_meter_id == Meter.id)
            .filter(Unit.estate_id == estate.id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        sub_water = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .join(Unit, Unit.water_meter_id == Meter.id)
            .filter(Unit.estate_id == estate.id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        communal_electricity = float(bulk_electricity) - float(sub_electricity)
        communal_water = float(bulk_water) - float(sub_water)

        bulk_sub_comparison.append(
            {
                "estate_name": estate.name,
                "bulk_electricity": float(bulk_electricity),
                "sub_electricity": float(sub_electricity),
                "communal_electricity": communal_electricity,
                "bulk_water": float(bulk_water),
                "sub_water": float(sub_water),
                "communal_water": communal_water,
            }
        )

    reports["bulk_sub_comparison"] = bulk_sub_comparison

    # Top Consumers by Utility Type
    def get_top_consumers_by_type(utility_type):
        query = (
            db.session.query(
                Unit.unit_number,
                Estate.name.label("estate_name"),
                Meter.meter_type,
                func.sum(MeterReading.consumption_since_last).label(
                    "total_consumption"
                ),
            )
            .join(Estate, Unit.estate_id == Estate.id)
            .join(
                Meter,
                or_(
                    Unit.electricity_meter_id == Meter.id,
                    Unit.water_meter_id == Meter.id,
                    Unit.hot_water_meter_id == Meter.id,
                    Unit.solar_meter_id == Meter.id,
                ),
            )
            .join(MeterReading, MeterReading.meter_id == Meter.id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .filter(Unit.is_active == True)
            .filter(Meter.meter_type == utility_type)
            .filter(MeterReading.consumption_since_last > 0)
            .group_by(Unit.id, Unit.unit_number, Estate.name, Meter.meter_type)
            .order_by(desc(func.sum(MeterReading.consumption_since_last)))
        )

        if estate_id:
            query = query.filter(Unit.estate_id == estate_id)

        # Pagination
        total_count = query.count()
        paginated_query = query.offset((top_page - 1) * per_page).limit(per_page)

        return {
            "data": paginated_query.all(),
            "pagination": {
                "total": total_count,
                "page": top_page,
                "per_page": per_page,
                "pages": (total_count + per_page - 1),
                "has_prev": top_page > 1,
                "has_next": top_page * per_page < total_count,
            },
        }

    # Get top consumers for each utility type
    reports["top_consumers_electricity"] = get_top_consumers_by_type("electricity")
    reports["top_consumers_water"] = get_top_consumers_by_type("water")
    reports["top_consumers_hot_water"] = get_top_consumers_by_type("hot_water")
    reports["top_consumers_solar"] = get_top_consumers_by_type("solar")

    # Solar Generation vs Usage
    solar_data = (
        db.session.query(
            Estate.name.label("estate_name"),
            func.sum(
                case(
                    (Meter.meter_type == "solar", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("solar_generation"),
            func.sum(
                case(
                    (
                        Meter.meter_type == "electricity",
                        MeterReading.consumption_since_last,
                    ),
                    else_=0,
                )
            ).label("electricity_usage"),
        )
        .join(Unit, Estate.id == Unit.estate_id)
        .outerjoin(
            Meter,
            or_(Unit.electricity_meter_id == Meter.id, Unit.solar_meter_id == Meter.id),
        )
        .outerjoin(
            MeterReading,
            and_(
                MeterReading.meter_id == Meter.id,
                MeterReading.reading_date >= start_date,
                MeterReading.reading_date <= end_date,
            ),
        )
        .filter(Estate.is_active == True)
        .group_by(Estate.id, Estate.name)
    )

    if estate_id:
        solar_data = solar_data.filter(Estate.id == estate_id)

    reports["solar_generation_vs_usage"] = solar_data.all()

    # Daily Consumption Trend - last 30 days aggregated by date
    from datetime import timedelta

    # Calculate date 30 days ago
    thirty_days_ago = datetime.now() - timedelta(days=30)

    daily_trend_query = (
        db.session.query(
            func.date(MeterReading.reading_date).label("date"),
            func.sum(
                case(
                    (Meter.meter_type == "electricity", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("electricity"),
            func.sum(
                case(
                    (Meter.meter_type == "water", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("water"),
            func.sum(
                case(
                    (Meter.meter_type == "hot_water", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("hot_water"),
            func.sum(
                case(
                    (Meter.meter_type == "solar", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("solar"),
        )
        .join(Meter, MeterReading.meter_id == Meter.id)
        .filter(MeterReading.reading_date >= thirty_days_ago)
        .group_by(func.date(MeterReading.reading_date))
        .order_by(func.date(MeterReading.reading_date))
    )

    if estate_id:
        # Join with units to filter by estate
        daily_trend_query = daily_trend_query.join(
            Unit,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
            ),
        ).filter(Unit.estate_id == estate_id)

    # Convert Row objects to dictionaries for JSON serialization
    daily_trend_results = daily_trend_query.all()
    reports["daily_consumption_trend"] = [
        {
            "date": row.date.isoformat() if row.date else None,
            "electricity": float(row.electricity) if row.electricity else 0,
            "water": float(row.water) if row.water else 0,
            "hot_water": float(row.hot_water) if row.hot_water else 0,
            "solar": float(row.solar) if row.solar else 0,
        }
        for row in daily_trend_results
    ]

    return reports


def get_financial_reports(start_date, end_date, estate_id, page=1, per_page=10):
    """Get financial report data"""
    reports = {"credit_purchases": [], "revenue_summary": None}

    # Credit Purchase Report
    credit_purchase_query = (
        db.session.query(
            Transaction.transaction_number,
            Transaction.completed_at,
            Unit.unit_number,
            Estate.name.label("estate_name"),
            Transaction.amount,
            case(
                (Transaction.payment_method.is_(None), "Unknown"),
                else_=Transaction.payment_method,
            ).label("payment_method"),
            Transaction.status,
            Transaction.description,
        )
        .join(Wallet, Transaction.wallet_id == Wallet.id)
        .join(Unit, Wallet.unit_id == Unit.id)
        .join(Estate, Unit.estate_id == Estate.id)
        .filter(Transaction.transaction_type == "topup")
        .filter(Transaction.completed_at >= start_date)
        .filter(Transaction.completed_at <= end_date)
        .order_by(desc(Transaction.completed_at))
    )

    if estate_id:
        credit_purchase_query = credit_purchase_query.filter(
            Unit.estate_id == estate_id
        )

    # Pagination
    total_purchases = credit_purchase_query.count()
    paginated_purchases = credit_purchase_query.offset((page - 1) * per_page).limit(
        per_page
    )

    # Convert to list for template use
    credit_purchases_raw = paginated_purchases.all()
    reports["credit_purchases"] = credit_purchases_raw

    # Also create JSON-serializable version for JavaScript charts
    reports["credit_purchases_json"] = [
        {
            "transaction_number": row.transaction_number,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            "unit_number": row.unit_number,
            "estate_name": row.estate_name,
            "amount": float(row.amount) if row.amount else 0,
            "payment_method": row.payment_method,
            "status": row.status,
            "description": row.description,
        }
        for row in credit_purchases_raw
    ]

    reports["credit_purchases_pagination"] = {
        "total": total_purchases,
        "page": page,
        "per_page": per_page,
        "pages": (total_purchases + per_page - 1),
        "has_prev": page > 1,
        "has_next": page * per_page < total_purchases,
    }

    # Revenue Summary Report
    revenue_summary = (
        db.session.query(
            func.sum(
                case(
                    (Transaction.transaction_type == "topup", Transaction.amount),
                    else_=0,
                )
            ).label("total_revenue"),
            func.count(
                case(
                    (Transaction.transaction_type == "topup", Transaction.id),
                    else_=None,
                )
            ).label("total_transactions"),
            func.sum(
                case(
                    (
                        Transaction.description.ilike("%electricity%"),
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("electricity_revenue"),
            func.sum(
                case(
                    (Transaction.description.ilike("%water%"), Transaction.amount),
                    else_=0,
                )
            ).label("water_revenue"),
            func.sum(
                case(
                    (Transaction.description.ilike("%solar%"), Transaction.amount),
                    else_=0,
                )
            ).label("solar_revenue"),
        )
        .join(Wallet, Transaction.wallet_id == Wallet.id)
        .join(Unit, Wallet.unit_id == Unit.id)
        .filter(Transaction.completed_at >= start_date)
        .filter(Transaction.completed_at <= end_date)
        .filter(Transaction.status == "completed")
    )

    if estate_id:
        revenue_summary = revenue_summary.filter(Unit.estate_id == estate_id)

    revenue_result = revenue_summary.first()
    if revenue_result:
        reports["revenue_summary"] = revenue_result
    else:
        # Create revenue summary object
        from types import SimpleNamespace

        reports["revenue_summary"] = SimpleNamespace(
            total_revenue=0,
            total_transactions=0,
            electricity_revenue=0,
            water_revenue=0,
            solar_revenue=0,
        )

    return reports


def get_system_status_reports(start_date, end_date, estate_id, page=1, per_page=10):
    """Get system and user status report data"""
    reports = {
        "communication_status": [],
        "offline_meters": [],
        "meter_health": [],
        "low_balance_alerts": [],
        "reconnection_history": [],
    }

    # Communication Status
    communication_status = (
        db.session.query(
            Meter.serial_number,
            Meter.meter_type,
            Estate.name.label("estate_name"),
            Unit.unit_number,
            func.max(MeterReading.reading_date).label("last_reading"),
            case(
                (
                    func.max(MeterReading.reading_date)
                    >= datetime.now() - timedelta(hours=24),
                    "online",
                ),
                (
                    func.max(MeterReading.reading_date)
                    >= datetime.now() - timedelta(hours=72),
                    "warning",
                ),
                else_="offline",
            ).label("status"),
        )
        .join(
            Unit,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
            ),
        )
        .join(Estate, Unit.estate_id == Estate.id)
        .outerjoin(MeterReading, MeterReading.meter_id == Meter.id)
        .filter(Meter.is_active == True)
        .group_by(
            Meter.id,
            Meter.serial_number,
            Meter.meter_type,
            Estate.name,
            Unit.unit_number,
        )
    )

    if estate_id:
        communication_status = communication_status.filter(Unit.estate_id == estate_id)

    reports["communication_status"] = communication_status.all()

    # Offline/Unresponsive Meters
    offline_meters = (
        db.session.query(
            Meter.serial_number,
            Meter.meter_type,
            Estate.name.label("estate_name"),
            Unit.unit_number,
            func.max(MeterReading.reading_date).label("last_reading"),
        )
        .join(
            Unit,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
            ),
        )
        .join(Estate, Unit.estate_id == Estate.id)
        .outerjoin(MeterReading, MeterReading.meter_id == Meter.id)
        .filter(Meter.is_active == True)
        .group_by(
            Meter.id,
            Meter.serial_number,
            Meter.meter_type,
            Estate.name,
            Unit.unit_number,
        )
        .having(
            or_(
                func.max(MeterReading.reading_date)
                < datetime.now() - timedelta(hours=72),
                func.max(MeterReading.reading_date).is_(None),
            )
        )
    )

    if estate_id:
        offline_meters = offline_meters.filter(Unit.estate_id == estate_id)

    reports["offline_meters"] = offline_meters.all()

    # Meter Health Report
    meter_health = (
        db.session.query(
            Meter.serial_number,
            Meter.meter_type,
            Estate.name.label("estate_name"),
            Unit.unit_number,
            func.count(MeterAlert.id).label("alert_count"),
            func.max(MeterAlert.created_at).label("last_alert"),
        )
        .join(
            Unit,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
            ),
        )
        .join(Estate, Unit.estate_id == Estate.id)
        .outerjoin(MeterAlert, MeterAlert.meter_id == Meter.id)
        .filter(Meter.is_active == True)
        .group_by(
            Meter.id,
            Meter.serial_number,
            Meter.meter_type,
            Estate.name,
            Unit.unit_number,
        )
    )

    if estate_id:
        meter_health = meter_health.filter(Unit.estate_id == estate_id)

    reports["meter_health"] = meter_health.all()

    # Low Balance & Cut-off Alerts
    # Join through UnitTenancy → Person to get primary tenant info
    low_balance_alerts = (
        db.session.query(
            Unit.unit_number,
            Estate.name.label("estate_name"),
            Person.first_name,
            Person.last_name,
            Person.email,
            Person.phone,
            Wallet.balance,
            Wallet.low_balance_threshold,
            case(
                (Wallet.balance <= 0, "cut_off"),
                (Wallet.balance < Wallet.low_balance_threshold, "low_balance"),
                else_="normal",
            ).label("status"),
        )
        .join(Estate, Unit.estate_id == Estate.id)
        .outerjoin(Wallet, Unit.id == Wallet.unit_id)
        .outerjoin(
            UnitTenancy,
            and_(
                UnitTenancy.unit_id == Unit.id,
                UnitTenancy.is_primary_tenant == True,
                UnitTenancy.status == "active",
                UnitTenancy.move_out_date.is_(None),
            ),
        )
        .outerjoin(Person, Person.id == UnitTenancy.person_id)
        .filter(Unit.is_active == True)
        .filter(Wallet.balance < Wallet.low_balance_threshold)
    )

    if estate_id:
        low_balance_alerts = low_balance_alerts.filter(Unit.estate_id == estate_id)

    reports["low_balance_alerts"] = low_balance_alerts.all()

    # Reconnection/Disconnection History
    reconnection_history = (
        db.session.query(
            Transaction.transaction_number,
            Transaction.completed_at,
            Unit.unit_number,
            Estate.name.label("estate_name"),
            Transaction.transaction_type,
            Transaction.amount,
            Transaction.description,
        )
        .join(Wallet, Transaction.wallet_id == Wallet.id)
        .join(Unit, Wallet.unit_id == Unit.id)
        .join(Estate, Unit.estate_id == Estate.id)
        .filter(Transaction.transaction_type.in_(["reconnection", "disconnection"]))
        .filter(Transaction.completed_at >= start_date)
        .filter(Transaction.completed_at <= end_date)
        .order_by(desc(Transaction.completed_at))
    )

    if estate_id:
        reconnection_history = reconnection_history.filter(Unit.estate_id == estate_id)

    reports["reconnection_history"] = reconnection_history.all()

    return reports


def get_estate_level_reports(start_date, end_date, estate_id, page=1, per_page=10):
    """Get estate-level report data"""
    reports = {
        "estate_utility_summary": [],
        "communal_usage": [],
        "management_snapshot": [],
    }

    # Estate Utility Summary
    estate_utility_summary = (
        db.session.query(
            Estate.name.label("estate_name"),
            func.sum(
                case(
                    (
                        Meter.meter_type == "electricity",
                        MeterReading.consumption_since_last,
                    ),
                    else_=0,
                )
            ).label("total_electricity"),
            func.sum(
                case(
                    (Meter.meter_type == "water", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("total_water"),
            func.sum(
                case(
                    (
                        Meter.meter_type == "hot_water",
                        MeterReading.consumption_since_last,
                    ),
                    else_=0,
                )
            ).label("total_hot_water"),
            func.sum(
                case(
                    (Meter.meter_type == "solar", MeterReading.consumption_since_last),
                    else_=0,
                )
            ).label("total_solar"),
            func.count(Unit.id).label("total_units"),
            func.count(
                case((Unit.occupancy_status == "occupied", Unit.id), else_=None)
            ).label("occupied_units"),
        )
        .join(Unit, Estate.id == Unit.estate_id)
        .outerjoin(
            Meter,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
            ),
        )
        .outerjoin(
            MeterReading,
            and_(
                MeterReading.meter_id == Meter.id,
                MeterReading.reading_date >= start_date,
                MeterReading.reading_date <= end_date,
            ),
        )
        .filter(Estate.is_active == True)
        .group_by(Estate.id, Estate.name)
    )

    if estate_id:
        estate_utility_summary = estate_utility_summary.filter(Estate.id == estate_id)

    estate_utility_summary_raw = estate_utility_summary.all()
    reports["estate_utility_summary"] = estate_utility_summary_raw

    # Also create JSON-serializable version for JavaScript charts
    reports["estate_utility_summary_json"] = [
        {
            "estate_name": row.estate_name,
            "total_electricity": float(row.total_electricity) if row.total_electricity else 0,
            "total_water": float(row.total_water) if row.total_water else 0,
            "total_hot_water": float(row.total_hot_water) if row.total_hot_water else 0,
            "total_solar": float(row.total_solar) if row.total_solar else 0,
            "total_units": row.total_units or 0,
            "occupied_units": row.occupied_units or 0,
        }
        for row in estate_utility_summary_raw
    ]

    # Communal Usage Report
    communal_usage = []
    estates_to_check = Estate.query.filter_by(is_active=True)
    if estate_id:
        estates_to_check = estates_to_check.filter(Estate.id == estate_id)

    for estate in estates_to_check:
        # Get bulk meter readings
        bulk_electricity = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(Meter.id == estate.bulk_electricity_meter_id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        bulk_water = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(Meter.id == estate.bulk_water_meter_id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        # Get sub-meter totals
        sub_electricity = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .join(Unit, Unit.electricity_meter_id == Meter.id)
            .filter(Unit.estate_id == estate.id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        sub_water = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .join(Unit, Unit.water_meter_id == Meter.id)
            .filter(Unit.estate_id == estate.id)
            .filter(MeterReading.reading_date >= start_date)
            .filter(MeterReading.reading_date <= end_date)
            .scalar()
            or 0
        )

        communal_electricity = float(bulk_electricity) - float(sub_electricity)
        communal_water = float(bulk_water) - float(sub_water)

        # Calculate costs using rate tables
        from app.utils.rates import calculate_consumption_charge

        electricity_cost = calculate_consumption_charge(
            consumption=communal_electricity,
            utility_type="electricity"
        )
        water_cost = calculate_consumption_charge(
            consumption=communal_water / 1000.0,  # Convert L to kL
            utility_type="water"
        )
        communal_usage.append(
            {
                "estate_name": estate.name,
                "communal_electricity": communal_electricity,
                "communal_water": communal_water,
                "electricity_cost": electricity_cost,
                "water_cost": water_cost,
                "total_cost": electricity_cost + water_cost,
            }
        )

    reports["communal_usage"] = communal_usage

    # Management Snapshot (real-time data)
    management_snapshot = (
        db.session.query(
            Estate.name.label("estate_name"),
            func.count(Unit.id).label("total_units"),
            func.count(
                case((Unit.occupancy_status == "occupied", Unit.id), else_=None)
            ).label("occupied_units"),
            func.sum(Wallet.balance).label("total_wallet_balance"),
            func.count(
                case(
                    (Wallet.balance < Wallet.low_balance_threshold, Wallet.id),
                    else_=None,
                )
            ).label("low_balance_count"),
            func.count(case((Wallet.balance <= 0, Wallet.id), else_=None)).label(
                "zero_balance_count"
            ),
        )
        .join(Unit, Estate.id == Unit.estate_id)
        .outerjoin(Wallet, Unit.id == Wallet.unit_id)
        .filter(Estate.is_active == True)
        .group_by(Estate.id, Estate.name)
    )

    if estate_id:
        management_snapshot = management_snapshot.filter(Estate.id == estate_id)

    reports["management_snapshot"] = management_snapshot.all()

    return reports


@api_v1.route("/reports/export/<report_type>")
@login_required
def export_report(report_type):
    """Export report data as CSV or PDF"""
    format_type = request.args.get("format", "csv")
    category = request.args.get("category", "consumption")

    # Get the same data as the main reports page
    estate_id = request.args.get("estate_id", type=int)
    date_range = request.args.get("date_range", "current_month")

    # Calculate date range
    today = datetime.now().date()
    if date_range == "current_month":
        start_date = today.replace(day=1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month - timedelta(days=1)
    elif date_range == "previous_month":
        first_this_month = today.replace(day=1)
        end_date = first_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif date_range == "past_3_months":
        start_date = today - timedelta(days=90)
        end_date = today
    elif date_range == "year_to_date":
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        start_date = today.replace(day=1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month - timedelta(days=1)

    if format_type == "csv":
        return export_csv(report_type, category, start_date, end_date, estate_id)
    elif format_type == "pdf":
        return export_pdf(report_type, category, start_date, end_date, estate_id)
    else:
        return jsonify({"error": "Unsupported format"}), 400


def export_csv(report_type, category, start_date, end_date, estate_id):
    """Export report data as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)

    if category == "consumption":
        if report_type == "unit_consumption":
            writer.writerow(
                [
                    "Unit Number",
                    "Estate",
                    "Electricity (kWh)",
                    "Water (kL)",
                    "Hot Water (kL)",
                    "Solar (kWh)",
                ]
            )
            data = get_consumption_reports(start_date, end_date, estate_id, "all")[
                "unit_consumption"
            ]
            for row in data:
                writer.writerow(
                    [
                        row.unit_number,
                        row.estate_name,
                        row.electricity_kwh,
                        row.water_kL,
                        getattr(row, "hot_water_kL", 0),
                        row.solar_kwh,
                    ]
                )

        elif report_type == "bulk_sub_comparison":
            writer.writerow(
                [
                    "Estate",
                    "Bulk Electricity",
                    "Sub Electricity",
                    "Communal Electricity",
                    "Bulk Water",
                    "Sub Water",
                    "Communal Water",
                ]
            )
            data = get_consumption_reports(start_date, end_date, estate_id, "all")[
                "bulk_sub_comparison"
            ]
            for row in data:
                writer.writerow(
                    [
                        row["estate_name"],
                        row["bulk_electricity"],
                        row["sub_electricity"],
                        row["communal_electricity"],
                        row["bulk_water"],
                        row["sub_water"],
                        row["communal_water"],
                    ]
                )

        elif report_type == "solar_generation_vs_usage":
            writer.writerow(
                [
                    "Estate",
                    "Solar Generation (kWh)",
                    "Electricity Usage (kWh)",
                    "Net Generation (kWh)",
                    "Utilization (%)",
                ]
            )
            data = get_consumption_reports(start_date, end_date, estate_id, "all")[
                "solar_generation_vs_usage"
            ]
            for row in data:
                solar_gen = float(row.solar_generation or 0)
                elec_usage = float(row.electricity_usage or 0)
                net_gen = solar_gen - elec_usage
                utilization = (solar_gen / elec_usage * 100) if elec_usage > 0 else 0

                writer.writerow(
                    [
                        row.estate_name,
                        solar_gen,
                        elec_usage,
                        net_gen,
                        f"{utilization:.1f}%",
                    ]
                )

        elif report_type == "top_consumers":
            writer.writerow(
                ["Unit Number", "Estate", "Meter Type", "Total Consumption"]
            )
            data = get_consumption_reports(start_date, end_date, estate_id, "all")[
                "top_consumers"
            ]
            for row in data:
                writer.writerow(
                    [
                        row.unit_number,
                        row.estate_name,
                        row.meter_type,
                        row.total_consumption,
                    ]
                )

    elif category == "financial":
        if report_type == "credit_purchases":
            writer.writerow(
                [
                    "Transaction Number",
                    "Date",
                    "Unit",
                    "Estate",
                    "Amount",
                    "Payment Method",
                    "Status",
                    "Description",
                ]
            )
            data = get_financial_reports(start_date, end_date, estate_id)[
                "credit_purchases"
            ]
            for row in data:
                writer.writerow(
                    [
                        row.transaction_number,
                        row.completed_at.strftime("%Y-%m-%d %H:%M")
                        if row.completed_at
                        else "",
                        row.unit_number,
                        row.estate_name,
                        row.amount,
                        row.payment_method or "Unknown",
                        row.status,
                        row.description,
                    ]
                )

    elif category == "system":
        if report_type == "communication_status":
            writer.writerow(
                [
                    "Serial Number",
                    "Meter Type",
                    "Estate",
                    "Unit",
                    "Last Reading",
                    "Status",
                ]
            )
            data = get_system_status_reports(start_date, end_date, estate_id)[
                "communication_status"
            ]
            for row in data:
                writer.writerow(
                    [
                        row.serial_number,
                        row.meter_type,
                        row.estate_name,
                        row.unit_number,
                        row.last_reading.strftime("%Y-%m-%d %H:%M")
                        if row.last_reading
                        else "Never",
                        row.status,
                    ]
                )

        elif report_type == "meter_health":
            writer.writerow(
                [
                    "Serial Number",
                    "Meter Type",
                    "Estate",
                    "Unit",
                    "Alert Count",
                    "Last Alert",
                ]
            )
            data = get_system_status_reports(start_date, end_date, estate_id)[
                "meter_health"
            ]
            for row in data:
                last_alert_str = (
                    row.last_alert.strftime("%Y-%m-%d") if row.last_alert else "None"
                )
                writer.writerow(
                    [
                        row.serial_number,
                        row.meter_type,
                        row.estate_name,
                        row.unit_number,
                        row.alert_count or 0,
                        last_alert_str,
                    ]
                )

    elif category == "estate":
        if report_type == "estate_summary":
            writer.writerow(
                [
                    "Estate",
                    "Total Units",
                    "Occupied Units",
                    "Total Electricity",
                    "Total Water",
                    "Total Hot Water",
                    "Total Solar",
                ]
            )
            data = get_estate_level_reports(start_date, end_date, estate_id)[
                "estate_utility_summary"
            ]
            for row in data:
                writer.writerow(
                    [
                        row.estate_name,
                        row.total_units,
                        row.occupied_units,
                        row.total_electricity,
                        row.total_water,
                        getattr(row, "total_hot_water", 0),
                        row.total_solar,
                    ]
                )

        elif report_type == "communal_usage":
            writer.writerow(
                [
                    "Estate",
                    "Communal Electricity (kWh)",
                    "Communal Water (kL)",
                    "Electricity Cost",
                    "Water Cost",
                    "Total Cost",
                ]
            )
            data = get_estate_level_reports(start_date, end_date, estate_id)[
                "communal_usage"
            ]
            for row in data:
                writer.writerow(
                    [
                        row["estate_name"],
                        row["communal_electricity"],
                        row["communal_water"],
                        row["electricity_cost"],
                        row["water_cost"],
                        row["total_cost"],
                    ]
                )

        elif report_type == "management_snapshot":
            writer.writerow(
                [
                    "Estate",
                    "Total Units",
                    "Occupied Units",
                    "Occupancy Rate",
                    "Total Wallet Balance",
                    "Low Balance Count",
                    "Zero Balance Count",
                ]
            )
            data = get_estate_level_reports(start_date, end_date, estate_id)[
                "management_snapshot"
            ]
            for row in data:
                occupancy_rate = (
                    ((row.occupied_units or 0) / (row.total_units or 1)) * 100
                    if row.total_units and row.total_units > 0
                    else 0
                )
                writer.writerow(
                    [
                        row.estate_name,
                        row.total_units,
                        row.occupied_units,
                        f"{occupancy_rate:.1f}%",
                        row.total_wallet_balance,
                        row.low_balance_count,
                        row.zero_balance_count,
                    ]
                )

    output.seek(0)
    filename = f"{report_type}_{category}_{start_date}_{end_date}.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )


def export_pdf(report_type, category, start_date, end_date, estate_id):
    """Export report data as PDF"""
    buffer = io.BytesIO()

    # Use landscape orientation for reports with many columns
    landscape_reports = [
        "bulk_sub_comparison",
        "communal_usage",
        "management_snapshot",
        "credit_purchases",
        "solar_generation_vs_usage",
        "low_balance_alerts",
    ]
    if report_type in landscape_reports:
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    else:
        doc = SimpleDocTemplate(buffer, pagesize=A4)

    story = []

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center alignment
    )

    # Add title
    title = f"{report_type.replace('_', ' ').title()} Report"
    story.append(Paragraph(title, title_style))

    # Add date range
    date_text = f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    story.append(Paragraph(date_text, styles["Normal"]))
    story.append(Spacer(1, 20))

    # Get data based on report type
    data = []
    headers = []

    if category == "consumption":
        if report_type == "unit_consumption":
            headers = [
                "Unit Number",
                "Estate",
                "Electricity (kWh)",
                "Water (kL)",
                "Hot Water (kL)",
                "Solar (kWh)",
            ]
            report_data = get_consumption_reports(
                start_date, end_date, estate_id, "all"
            )["unit_consumption"]
            for row in report_data:
                data.append(
                    [
                        str(row.unit_number),
                        str(row.estate_name),
                        f"{row.electricity_kwh:.2f}" if row.electricity_kwh else "0.00",
                        f"{row.water_kL:.2f}" if row.water_kL else "0.00",
                        f"{getattr(row, 'hot_water_kL', 0):.2f}",
                        f"{row.solar_kwh:.2f}" if row.solar_kwh else "0.00",
                    ]
                )

        elif report_type == "bulk_sub_comparison":
            headers = [
                "Estate",
                "Bulk Electricity",
                "Sub Electricity",
                "Communal Electricity",
                "Bulk Water",
                "Sub Water",
                "Communal Water",
            ]
            report_data = get_consumption_reports(
                start_date, end_date, estate_id, "all"
            )["bulk_sub_comparison"]
            for row in report_data:
                data.append(
                    [
                        str(row["estate_name"]),
                        f"{row['bulk_electricity']:.2f}"
                        if row["bulk_electricity"]
                        else "0.00",
                        f"{row['sub_electricity']:.2f}"
                        if row["sub_electricity"]
                        else "0.00",
                        f"{row['communal_electricity']:.2f}"
                        if row["communal_electricity"]
                        else "0.00",
                        f"{row['bulk_water']:.2f}" if row["bulk_water"] else "0.00",
                        f"{row['sub_water']:.2f}" if row["sub_water"] else "0.00",
                        f"{row['communal_water']:.2f}"
                        if row["communal_water"]
                        else "0.00",
                    ]
                )

        elif report_type == "solar_generation_vs_usage":
            headers = [
                "Estate",
                "Solar Generation\n(kWh)",
                "Electricity Usage\n(kWh)",
                "Net Generation\n(kWh)",
                "Utilization\n(%)",
            ]
            report_data = get_consumption_reports(
                start_date, end_date, estate_id, "all"
            )["solar_generation_vs_usage"]
            for row in report_data:
                solar_gen = float(row.solar_generation or 0)
                elec_usage = float(row.electricity_usage or 0)
                net_gen = solar_gen - elec_usage
                utilization = (solar_gen / elec_usage * 100) if elec_usage > 0 else 0

                data.append(
                    [
                        str(row.estate_name),
                        f"{solar_gen:.2f}",
                        f"{elec_usage:.2f}",
                        f"{net_gen:.2f}",
                        f"{utilization:.1f}%",
                    ]
                )

    elif category == "financial":
        if report_type == "credit_purchases":
            headers = [
                "Transaction #",
                "Date",
                "Unit",
                "Estate",
                "Amount",
                "Payment Method",
                "Status",
            ]
            report_data = get_financial_reports(start_date, end_date, estate_id)[
                "credit_purchases"
            ]
            for row in report_data:
                data.append(
                    [
                        str(row.transaction_number),
                        row.completed_at.strftime("%Y-%m-%d")
                        if row.completed_at
                        else "",
                        str(row.unit_number),
                        str(row.estate_name),
                        f"R{row.amount:.2f}" if row.amount else "R0.00",
                        str(row.payment_method),
                        str(row.status),
                    ]
                )

    elif category == "system":
        if report_type == "communication_status":
            headers = [
                "Serial Number",
                "Meter Type",
                "Estate",
                "Unit",
                "Last Reading",
                "Status",
            ]
            report_data = get_system_status_reports(start_date, end_date, estate_id)[
                "communication_status"
            ]
            for row in report_data:
                data.append(
                    [
                        str(row.serial_number),
                        str(row.meter_type),
                        str(row.estate_name),
                        str(row.unit_number),
                        row.last_reading.strftime("%Y-%m-%d %H:%M")
                        if row.last_reading
                        else "Never",
                        str(row.status),
                    ]
                )

        elif report_type == "offline_meters":
            headers = [
                "Serial Number",
                "Meter Type",
                "Estate",
                "Unit",
                "Last Reading",
                "Days Offline",
            ]
            report_data = get_system_status_reports(start_date, end_date, estate_id)[
                "offline_meters"
            ]
            for row in report_data:
                data.append(
                    [
                        str(row.serial_number),
                        str(row.meter_type),
                        str(row.estate_name),
                        str(row.unit_number),
                        row.last_reading.strftime("%Y-%m-%d %H:%M")
                        if row.last_reading
                        else "Never",
                        str(row.days_offline) if row.days_offline else "0",
                    ]
                )

        elif report_type == "meter_health":
            headers = [
                "Serial Number",
                "Meter Type",
                "Estate",
                "Unit",
                "Alert Count",
                "Last Alert",
            ]
            report_data = get_system_status_reports(start_date, end_date, estate_id)[
                "meter_health"
            ]
            for row in report_data:
                last_alert_str = (
                    row.last_alert.strftime("%Y-%m-%d") if row.last_alert else "None"
                )
                data.append(
                    [
                        str(row.serial_number),
                        str(row.meter_type),
                        str(row.estate_name),
                        str(row.unit_number),
                        str(row.alert_count or 0),
                        last_alert_str,
                    ]
                )

        elif report_type == "low_balance_alerts":
            headers = [
                "Unit Number",
                "Estate",
                "Resident",
                "Email",
                "Phone",
                "Current Balance",
                "Threshold",
                "Status",
            ]
            report_data = get_system_status_reports(start_date, end_date, estate_id)[
                "low_balance_alerts"
            ]
            for row in report_data:
                resident_name = (
                    f"{row.first_name} {row.last_name}"
                    if row.first_name
                    else "Vacant"
                )
                data.append(
                    [
                        str(row.unit_number),
                        str(row.estate_name),
                        resident_name,
                        str(row.email or "N/A"),
                        str(row.phone or "N/A"),
                        f"R{row.balance:.2f}" if row.balance else "R0.00",
                        f"R{row.low_balance_threshold:.2f}"
                        if row.low_balance_threshold
                        else "R0.00",
                        str(row.status).replace("_", " ").title(),
                    ]
                )

        elif report_type == "reconnection_history":
            headers = [
                "Transaction #",
                "Date",
                "Unit Number",
                "Estate",
                "Type",
                "Amount",
                "Description",
            ]
            report_data = get_system_status_reports(start_date, end_date, estate_id)[
                "reconnection_history"
            ]
            for row in report_data:
                data.append(
                    [
                        str(row.transaction_number),
                        row.completed_at.strftime("%Y-%m-%d %H:%M")
                        if row.completed_at
                        else "N/A",
                        str(row.unit_number),
                        str(row.estate_name),
                        str(row.transaction_type).title(),
                        f"R{row.amount:.2f}" if row.amount else "R0.00",
                        str(row.description or "N/A"),
                    ]
                )

    elif category == "estate":
        if report_type == "estate_summary":
            headers = [
                "Estate",
                "Total Units",
                "Occupied Units",
                "Total Electricity",
                "Total Water",
                "Total Hot Water",
                "Total Solar",
            ]
            report_data = get_estate_level_reports(start_date, end_date, estate_id)[
                "estate_utility_summary"
            ]
            for row in report_data:
                data.append(
                    [
                        str(row.estate_name),
                        str(row.total_units),
                        str(row.occupied_units),
                        f"{row.total_electricity:.2f}"
                        if row.total_electricity
                        else "0.00",
                        f"{row.total_water:.2f}" if row.total_water else "0.00",
                        f"{row.total_hot_water:.2f}" if row.total_hot_water else "0.00",
                        f"{row.total_solar:.2f}" if row.total_solar else "0.00",
                    ]
                )

        elif report_type == "communal_usage":
            headers = [
                "Estate",
                "Communal\nElectricity\n(kWh)",
                "Communal\nWater\n(kL)",
                "Electricity\nCost",
                "Water\nCost",
                "Total\nCost",
            ]
            report_data = get_estate_level_reports(start_date, end_date, estate_id)[
                "communal_usage"
            ]
            for row in report_data:
                data.append(
                    [
                        str(row["estate_name"]),
                        f"{row['communal_electricity']:.2f}"
                        if row["communal_electricity"]
                        else "0.00",
                        f"{row['communal_water']:.2f}"
                        if row["communal_water"]
                        else "0.00",
                        f"R{row['electricity_cost']:.2f}"
                        if row["electricity_cost"]
                        else "R0.00",
                        f"R{row['water_cost']:.2f}" if row["water_cost"] else "R0.00",
                        f"R{row['total_cost']:.2f}" if row["total_cost"] else "R0.00",
                    ]
                )

        elif report_type == "management_snapshot":
            headers = [
                "Estate",
                "Total\nUnits",
                "Occupied\nUnits",
                "Occupancy\nRate",
                "Total Wallet\nBalance",
                "Low Balance\nCount",
                "Zero Balance\nCount",
            ]
            report_data = get_estate_level_reports(start_date, end_date, estate_id)[
                "management_snapshot"
            ]
            for row in report_data:
                occupancy_rate = (
                    ((row.occupied_units or 0) / (row.total_units or 1)) * 100
                    if row.total_units and row.total_units > 0
                    else 0
                )
                data.append(
                    [
                        str(row.estate_name),
                        str(row.total_units),
                        str(row.occupied_units),
                        f"{occupancy_rate:.1f}%",
                        f"R{row.total_wallet_balance:.2f}"
                        if row.total_wallet_balance
                        else "R0.00",
                        str(row.low_balance_count),
                        str(row.zero_balance_count),
                    ]
                )

    # Create table
    if headers and data:
        table_data = [headers] + data

        # Adjust column widths for landscape reports
        if report_type in landscape_reports:
            # Use full width for landscape reports
            num_cols = len(headers)
            # Calculate width to use most of the landscape page (11.69 inches - margins)
            available_width = 10.5

            # For specific reports, use custom column widths
            if report_type == "solar_generation_vs_usage":
                # Use wider columns for better readability
                col_widths = [
                    2.0 * inch,
                    2.0 * inch,
                    2.0 * inch,
                    2.0 * inch,
                    2.0 * inch,
                ]
            elif report_type == "communal_usage":
                # Communal usage has 6 columns
                col_widths = [
                    2.0 * inch,  # Estate (wider for longer names)
                    1.7 * inch,  # Communal Electricity
                    1.7 * inch,  # Communal Water
                    1.4 * inch,  # Electricity Cost
                    1.4 * inch,  # Water Cost
                    1.3 * inch,  # Total Cost
                ]
            elif report_type == "management_snapshot":
                # Management snapshot has 7 columns - optimize for landscape
                col_widths = [
                    2.0 * inch,  # Estate
                    1.2 * inch,  # Total Units
                    1.2 * inch,  # Occupied Units
                    1.2 * inch,  # Occupancy Rate
                    1.8 * inch,  # Total Wallet Balance
                    1.2 * inch,  # Low Balance Count
                    1.2 * inch,  # Zero Balance Count
                ]
            elif report_type == "credit_purchases":
                # Credit purchases has 7 columns - use more of the landscape width
                col_widths = [
                    1.5 * inch,  # Transaction #
                    1.4 * inch,  # Date
                    1.0 * inch,  # Unit
                    2.0 * inch,  # Estate
                    1.3 * inch,  # Amount
                    1.5 * inch,  # Payment Method
                    1.3 * inch,  # Status
                ]
            else:
                col_width = available_width / num_cols
                col_widths = [col_width * inch for _ in range(num_cols)]

            table = Table(table_data, colWidths=col_widths)
        else:
            table = Table(table_data)

        # Style the table
        if report_type in landscape_reports:
            # Larger fonts and better spacing for landscape
            if report_type == "solar_generation_vs_usage":
                # Special styling for multi-line headers
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            (
                                "FONTSIZE",
                                (0, 0),
                                (-1, 0),
                                12,
                            ),  # Slightly smaller for multi-line
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, 0),
                                20,
                            ),  # More padding for multi-line
                            ("TOPPADDING", (0, 0), (-1, 0), 15),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("FONTSIZE", (0, 1), (-1, -1), 12),  # Larger data font
                            ("TOPPADDING", (0, 1), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                            (
                                "ROWBACKGROUNDS",
                                (0, 1),
                                (-1, -1),
                                [colors.white, colors.lightgrey],
                            ),
                        ]
                    )
                )
        elif report_type == "communal_usage":
            # Special styling for multi-line headers
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),  # Smaller for multi-line
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, 0),
                            25,
                        ),  # More padding for multi-line
                        ("TOPPADDING", (0, 0), (-1, 0), 15),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("FONTSIZE", (0, 1), (-1, -1), 12),  # Larger data font
                        ("TOPPADDING", (0, 1), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )
        elif report_type == "management_snapshot":
            # Special styling for multi-line headers
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),  # Smaller for multi-line
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, 0),
                            25,
                        ),  # More padding for multi-line
                        ("TOPPADDING", (0, 0), (-1, 0), 15),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("FONTSIZE", (0, 1), (-1, -1), 12),  # Larger data font
                        ("TOPPADDING", (0, 1), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )
        else:
            # Standard landscape styling
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 14),  # Larger header font
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 15),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("FONTSIZE", (0, 1), (-1, -1), 12),  # Larger data font
                        ("TOPPADDING", (0, 1), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )
        # Standard styling for portrait
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )

        story.append(table)

        # Add spacing after table for landscape reports
        if report_type in landscape_reports:
            story.append(Spacer(1, 20))
    else:
        story.append(Paragraph("No data available for this report.", styles["Normal"]))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    filename = f"{report_type}_{category}_{start_date}_{end_date}.pdf"

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
