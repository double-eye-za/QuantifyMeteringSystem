from __future__ import annotations

from flask import jsonify, request, render_template, send_file
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, extract, case, or_, and_, desc, asc
from sqlalchemy.orm import joinedload
import csv
import io
from decimal import Decimal

from . import api_v1
from app.models import (
    MeterReading,
    Transaction,
    Estate,
    Meter,
    Unit,
    Wallet,
    Resident,
    Notification,
    MeterAlert,
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

    # Get estates for filter dropdown
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
        "top_consumers_solar": [],
        "solar_generation_vs_usage": [],
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

    # Apply pagination
    total_count = unit_consumption_query.count()
    paginated_query = unit_consumption_query.offset((unit_page - 1) * per_page).limit(
        per_page
    )

    reports["unit_consumption"] = paginated_query.all()
    reports["unit_consumption_pagination"] = {
        "total": total_count,
        "page": unit_page,
        "per_page": per_page,
        "pages": (total_count + per_page - 1) // per_page,
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
                "pages": (total_count + per_page - 1) // per_page,
                "has_prev": top_page > 1,
                "has_next": top_page * per_page < total_count,
            },
        }

    # Get top consumers for each utility type
    reports["top_consumers_electricity"] = get_top_consumers_by_type("electricity")
    reports["top_consumers_water"] = get_top_consumers_by_type("water")
    reports["top_consumers_solar"] = get_top_consumers_by_type("solar")

    # 4. Solar Generation vs Usage
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
            Transaction.payment_method,
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

    reports["credit_purchases"] = paginated_purchases.all()
    reports["credit_purchases_pagination"] = {
        "total": total_purchases,
        "page": page,
        "per_page": per_page,
        "pages": (total_purchases + per_page - 1) // per_page,
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
        # Create a default revenue summary object
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
    low_balance_alerts = (
        db.session.query(
            Unit.unit_number,
            Estate.name.label("estate_name"),
            Resident.first_name,
            Resident.last_name,
            Resident.email,
            Resident.phone,
            Wallet.balance,
            Wallet.low_balance_threshold,
            case(
                (Wallet.balance <= 0, "cut_off"),
                (Wallet.balance < Wallet.low_balance_threshold, "low_balance"),
                else_="normal",
            ).label("status"),
        )
        .join(Estate, Unit.estate_id == Estate.id)
        .outerjoin(Resident, Unit.resident_id == Resident.id)
        .outerjoin(Wallet, Unit.id == Wallet.unit_id)
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

    reports["estate_utility_summary"] = estate_utility_summary.all()

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

        # Calculate costs (using standard rates)
        electricity_cost = communal_electricity * 2.50  # R2.50/kWh
        water_cost = communal_water * 15.00  # R15.00/kL

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
                        row.solar_kwh,
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
                        row.payment_method,
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

    elif category == "estate":
        if report_type == "estate_summary":
            writer.writerow(
                [
                    "Estate",
                    "Total Units",
                    "Occupied Units",
                    "Total Electricity",
                    "Total Water",
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
                        row.total_solar,
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
    """Export report data as PDF (placeholder - would need reportlab or similar)"""
    return jsonify({"message": "PDF export not yet implemented"}), 501
