from __future__ import annotations

from flask import (
    jsonify,
    request,
    current_app,
    session,
    render_template,
    redirect,
    url_for,
)
from flask_login import login_user, logout_user, login_required, current_user

from ...models import User, MobileUser
from ...db import db
from ...utils.audit import log_action
from ...services.mobile_users import authenticate_mobile_user
from ...utils.password_generator import validate_phone_number
from . import api_v1
from datetime import datetime, timedelta
from sqlalchemy import func, case
from sqlalchemy.sql import extract
from ...models import Transaction, MeterReading, Meter, Unit, Estate
from ...utils.decorators import get_user_estate_filter, get_allowed_estates
import re


def _is_phone_credential(credential: str) -> bool:
    """Detect if a login credential looks like a phone number rather than an email/username.

    Returns True for South African phone formats:
    - +27xxxxxxxxx
    - 0xxxxxxxxx
    - Digits with spaces/dashes
    """
    cleaned = re.sub(r'[\s\-\(\)]', '', credential)
    return bool(
        re.match(r'^\+\d{10,15}$', cleaned) or  # E.164 international
        re.match(r'^0\d{9}$', cleaned)            # SA local format
    )


def _is_portal_user() -> bool:
    """Check if the current authenticated user is a portal (mobile) user."""
    if not current_user.is_authenticated:
        return False
    return str(current_user.get_id()).startswith('mobile:')


@api_v1.route("/login", methods=["GET"])
def login_page():
    """Render the login page"""
    if current_user.is_authenticated:
        if _is_portal_user():
            return redirect(url_for("portal.portal_dashboard"))
        return redirect(url_for("api_v1.dashboard"))
    return render_template("auth/login.html")


@api_v1.route("/", methods=["GET"])
@login_required
def index():
    """Main entry point - redirect to appropriate dashboard."""
    if _is_portal_user():
        return redirect(url_for("portal.portal_dashboard"))
    return redirect(url_for("api_v1.dashboard"))


@api_v1.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    from ...models import (
        Estate,
        Unit,
        Meter,
        Wallet,
        Transaction,
        MeterReading,
        MeterAlert,
    )
    from datetime import datetime, timedelta, date
    from sqlalchemy import func, case
    from ...db import db

    # Get filter parameters — estate-scoped users are locked to their estate
    user_estate = get_user_estate_filter()
    if user_estate:
        estate_id = str(user_estate)
    else:
        estate_id = request.args.get("estate", "all")
    period = request.args.get("period", "current-month")


    # Calculate date range based on period
    today = date.today()
    current_month = datetime.now().strftime("%B %Y")

    if period == "previous-month":
        # Previous month
        month_start = (datetime.now().replace(day=1) - timedelta(days=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_month = month_start.strftime("%B %Y")
    elif period == "past-3-months":
        # Past 3 months
        month_start = (datetime.now().replace(day=1) - timedelta(days=90)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_month = f"Past 3 Months ({month_start.strftime('%b')} - {datetime.now().strftime('%b %Y')})"
    else:
        # Current month (default)
        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_month = (month_start + timedelta(days=32)).replace(day=1)

    # Build estate filter
    estate_filter = []
    if estate_id != "all":
        estate_filter = [Estate.id == int(estate_id)]

    # Summary Metrics

    # Total Electricity Consumption (kWh) - current month
    electricity_query = (
        db.session.query(func.sum(MeterReading.consumption_since_last))
        .join(Meter, Meter.id == MeterReading.meter_id)
        .join(Unit, Unit.electricity_meter_id == Meter.id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Meter.meter_type == "electricity",
            MeterReading.reading_date >= month_start,
            MeterReading.reading_date < next_month,
        )
    )
    if estate_filter:
        electricity_query = electricity_query.filter(*estate_filter)
    total_electricity_kwh = electricity_query.scalar() or 0.0

    # Total Water Consumption (L) - current month
    water_query = (
        db.session.query(func.sum(MeterReading.consumption_since_last))
        .join(Meter, Meter.id == MeterReading.meter_id)
        .join(Unit, Unit.water_meter_id == Meter.id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Meter.meter_type == "water",
            MeterReading.reading_date >= month_start,
            MeterReading.reading_date < next_month,
        )
    )
    if estate_filter:
        water_query = water_query.filter(*estate_filter)
    total_water_liters = water_query.scalar() or 0.0

    # Total Hot Water Consumption (L) - current month
    hot_water_query = (
        db.session.query(func.sum(MeterReading.consumption_since_last))
        .join(Meter, Meter.id == MeterReading.meter_id)
        .join(Unit, Unit.hot_water_meter_id == Meter.id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Meter.meter_type == "hot_water",
            MeterReading.reading_date >= month_start,
            MeterReading.reading_date < next_month,
        )
    )
    if estate_filter:
        hot_water_query = hot_water_query.filter(*estate_filter)
    total_hot_water_liters = hot_water_query.scalar() or 0.0

    # Solar Contribution (kWh) - current month
    solar_query = (
        db.session.query(func.sum(MeterReading.consumption_since_last))
        .join(Meter, Meter.id == MeterReading.meter_id)
        .join(Unit, Unit.solar_meter_id == Meter.id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Meter.meter_type == "solar",
            MeterReading.reading_date >= month_start,
            MeterReading.reading_date < next_month,
        )
    )
    if estate_filter:
        solar_query = solar_query.filter(*estate_filter)
    solar_contribution_kwh = solar_query.scalar() or 0.0

    # Revenue Collected (R) - current month
    revenue_query = (
        db.session.query(func.sum(Transaction.amount))
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Transaction.transaction_type == "topup",
            Transaction.status == "completed",
            Transaction.completed_at >= month_start,
            Transaction.completed_at < next_month,
        )
    )
    if estate_filter:
        revenue_query = revenue_query.filter(*estate_filter)
    revenue_collected = revenue_query.scalar() or 0.0

    # Active Units - units with meters reporting within last 24 hours
    active_query = (
        db.session.query(func.count(func.distinct(Unit.id)))
        .join(
            Meter,
            Meter.id.in_(
                [
                    Unit.electricity_meter_id,
                    Unit.water_meter_id,
                    Unit.hot_water_meter_id,
                    Unit.solar_meter_id,
                ]
            ),
        )
        .join(MeterReading, MeterReading.meter_id == Meter.id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(MeterReading.reading_date >= datetime.now() - timedelta(hours=24))
    )
    if estate_filter:
        active_query = active_query.filter(*estate_filter)
    active_units = active_query.scalar() or 0

    # Offline / Faulty Meters
    offline_query = (
        db.session.query(func.count(Meter.id))
        .join(
            Unit,
            Unit.id.in_(
                [
                    Unit.electricity_meter_id,
                    Unit.water_meter_id,
                    Unit.hot_water_meter_id,
                    Unit.solar_meter_id,
                ]
            ),
        )
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(Meter.communication_status == "offline")
    )
    if estate_filter:
        offline_query = offline_query.filter(*estate_filter)
    offline_meters = offline_query.scalar() or 0

    # Total Disconnections / Re-connections - units with zero balance
    disconnected_query = (
        db.session.query(func.count(Wallet.id))
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(Wallet.balance <= 0)
    )
    if estate_filter:
        disconnected_query = disconnected_query.filter(*estate_filter)
    disconnected_units = disconnected_query.scalar() or 0

    # Communal Area Usage (kWh / L) - bulk meter consumption
    communal_elec_query = (
        db.session.query(func.sum(MeterReading.consumption_since_last))
        .join(Meter, Meter.id == MeterReading.meter_id)
        .join(Estate, Estate.bulk_electricity_meter_id == Meter.id)
        .filter(
            Meter.meter_type == "bulk_electricity",
            MeterReading.reading_date >= month_start,
            MeterReading.reading_date < next_month,
        )
    )
    if estate_filter:
        communal_elec_query = communal_elec_query.filter(*estate_filter)
    communal_electricity = communal_elec_query.scalar() or 0.0

    communal_water_query = (
        db.session.query(func.sum(MeterReading.consumption_since_last))
        .join(Meter, Meter.id == MeterReading.meter_id)
        .join(Estate, Estate.bulk_water_meter_id == Meter.id)
        .filter(
            Meter.meter_type == "bulk_water",
            MeterReading.reading_date >= month_start,
            MeterReading.reading_date < next_month,
        )
    )
    if estate_filter:
        communal_water_query = communal_water_query.filter(*estate_filter)
    communal_water = communal_water_query.scalar() or 0.0

    #  Alerts & Notifications

    # Offline Meters Alert
    offline_meters_alert = (
        db.session.query(Meter)
        .filter(Meter.communication_status == "offline")
        .limit(5)
        .all()
    )

    # Low Credit Alerts
    low_credit_alerts = (
        db.session.query(Wallet, Unit, Estate)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(Wallet.balance < Wallet.low_balance_threshold, Wallet.balance > 0)
        .limit(5)
        .all()
    )

    # Tamper or Fault Warnings (using MeterAlert)
    tamper_alerts = (
        db.session.query(MeterAlert)
        .filter(
            MeterAlert.alert_type.in_(["tamper", "fault", "communication_loss"]),
            MeterAlert.is_resolved == False,
        )
        .limit(5)
        .all()
    )

    # Failed Wallet Top-Ups
    failed_topups = (
        db.session.query(Transaction)
        .filter(
            Transaction.transaction_type == "topup",
            Transaction.status == "failed",
            Transaction.initiated_at >= datetime.now() - timedelta(days=1),
        )
        .limit(5)
        .all()
    )

    # 3. Estate Overview Widgets

    # Estate Selector data — scoped users only see their estate
    estates = [e.to_dict() for e in get_allowed_estates()]

    # Live Status Summary
    live_status = {
        "online": db.session.query(func.count(Meter.id))
        .filter(Meter.communication_status == "online")
        .scalar()
        or 0,
        "low_signal": db.session.query(func.count(Meter.id))
        .filter(Meter.communication_status == "low_signal")
        .scalar()
        or 0,
        "offline": offline_meters,
    }

    # Bulk Meter Feed Status
    bulk_meter_status = (
        db.session.query(
            Estate.name,
            Estate.bulk_electricity_meter_id,
            Estate.bulk_water_meter_id,
            func.max(MeterReading.reading_date).label("last_elec_reading"),
            func.max(MeterReading.reading_date).label("last_water_reading"),
        )
        .outerjoin(
            MeterReading,
            MeterReading.meter_id.in_(
                [Estate.bulk_electricity_meter_id, Estate.bulk_water_meter_id]
            ),
        )
        .group_by(
            Estate.name, Estate.bulk_electricity_meter_id, Estate.bulk_water_meter_id
        )
        .all()
    )

    # Solar Offset Gauge - percentage of total electricity supplied via solar
    total_electricity_all = float(total_electricity_kwh) + float(solar_contribution_kwh)
    solar_offset_percentage = (
        (float(solar_contribution_kwh) / total_electricity_all * 100)
        if total_electricity_all > 0
        else 0
    )

    # Communal Usage Gauge - percentage of bulk usage not allocated to individual units
    total_bulk_usage = float(communal_electricity) + float(communal_water)
    total_sub_usage = float(total_electricity_kwh) + float(total_water_liters)
    communal_usage_percentage = (
        (total_bulk_usage / (total_bulk_usage + total_sub_usage) * 100)
        if (total_bulk_usage + total_sub_usage) > 0
        else 0
    )

    # 4. Financial Snapshot

    # Total Top-Ups (Today / This Month)
    todays_topups = (
        db.session.query(func.sum(Transaction.amount))
        .filter(
            Transaction.transaction_type == "topup",
            Transaction.status == "completed",
            func.date(Transaction.completed_at) == today,
        )
        .scalar()
        or 0.0
    )

    # Revenue per Utility - based on consumption transactions
    revenue_per_utility_query = (
        db.session.query(
            case(
                (
                    Transaction.transaction_type == "consumption_electricity",
                    "Electricity",
                ),
                (Transaction.transaction_type == "consumption_water", "Water"),
                (Transaction.transaction_type == "consumption_hot_water", "Hot Water"),
                (Transaction.transaction_type == "consumption_solar", "Solar"),
                else_="Other",
            ).label("utility"),
            func.sum(Transaction.amount).label("revenue"),
        )
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Transaction.transaction_type.in_(
                [
                    "consumption_electricity",
                    "consumption_water",
                    "consumption_hot_water",
                    "consumption_solar",
                ]
            ),
            Transaction.status == "completed",
            Transaction.completed_at >= month_start,
            Transaction.completed_at < next_month,
        )
    )
    if estate_filter:
        revenue_per_utility_query = revenue_per_utility_query.filter(*estate_filter)
    revenue_per_utility = revenue_per_utility_query.group_by("utility").all()

    # Top Paying Units
    top_paying_query = (
        db.session.query(
            Unit.unit_number,
            Estate.name.label("estate_name"),
            func.sum(Transaction.amount).label("total_spent"),
        )
        .join(Wallet, Wallet.unit_id == Unit.id)
        .join(Estate, Estate.id == Unit.estate_id)
        .join(Transaction, Transaction.wallet_id == Wallet.id)
        .filter(
            Transaction.transaction_type == "topup",
            Transaction.status == "completed",
            Transaction.completed_at >= month_start,
            Transaction.completed_at < next_month,
        )
    )
    if estate_filter:
        top_paying_query = top_paying_query.filter(*estate_filter)
    top_paying_units = (
        top_paying_query.group_by(Unit.unit_number, Estate.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )

    # Communal Area Cost Estimate - based on tariff rates
    from app.utils.rates import calculate_consumption_charge

    electricity_cost = calculate_consumption_charge(
        consumption=float(communal_electricity),
        utility_type="electricity"
    )
    water_cost = calculate_consumption_charge(
        consumption=float(communal_water) / 1000.0,  # Convert L to kL
        utility_type="water"
    )
    communal_cost_estimate = electricity_cost + water_cost

    # Calculate KPIs for new dashboard spec
    cold_water_kL = float(total_water_liters) / 1000.0  # Convert L to kL
    hot_water_kL = float(total_hot_water_liters) / 1000.0  # Convert L to kL

    # Calculate solar contribution percentage
    total_electricity_all = float(total_electricity_kwh) + float(solar_contribution_kwh)
    solar_contribution_percent = (
        (float(solar_contribution_kwh) / total_electricity_all * 100)
        if total_electricity_all > 0
        else 0
    )

    # Revenue by utility type breakdown - based on consumption transactions

    revenue_by_utility_query = (
        db.session.query(
            case(
                (
                    Transaction.transaction_type == "consumption_electricity",
                    "Electricity",
                ),
                (Transaction.transaction_type == "consumption_water", "Water"),
                (Transaction.transaction_type == "consumption_solar", "Solar"),
                else_="Other",
            ).label("utility"),
            func.sum(Transaction.amount).label("revenue"),
        )
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Transaction.transaction_type.in_(
                ["consumption_electricity", "consumption_water", "consumption_solar"]
            ),
            Transaction.status == "completed",
            Transaction.completed_at >= month_start,
            Transaction.completed_at < next_month,
        )
    )
    if estate_filter:
        revenue_by_utility_query = revenue_by_utility_query.filter(*estate_filter)
    revenue_by_utility = revenue_by_utility_query.group_by("utility").all()

    # Format for template
    # Normalize to include all
    revenue_map = {u: 0.0 for u in ["Electricity", "Water", "Hot Water", "Solar"]}
    for item in revenue_by_utility:
        revenue_map[item.utility] = float(item.revenue)
    revenue_by_utility = [
        {"utility": key, "revenue": revenue_map[key]}
        for key in ["Electricity", "Water", "Hot Water", "Solar"]
    ]

    # Estate Usage Data for comparison chart
    estate_usage_query = (
        db.session.query(
            Estate.name,
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_electricity",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("electricity"),
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_water",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("water"),
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_hot_water",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("hot_water"),
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_solar",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("solar"),
        )
        .join(Unit, Estate.id == Unit.estate_id)
        .join(Wallet, Wallet.unit_id == Unit.id)
        .join(Transaction, Transaction.wallet_id == Wallet.id)
        .filter(
            Transaction.transaction_type.in_(
                [
                    "consumption_electricity",
                    "consumption_water",
                    "consumption_hot_water",
                    "consumption_solar",
                ]
            ),
            Transaction.status == "completed",
            Transaction.completed_at >= month_start,
            Transaction.completed_at < next_month,
        )
    )
    if estate_filter:
        estate_usage_query = estate_usage_query.filter(*estate_filter)
    estate_usage_data = estate_usage_query.group_by(Estate.name).all()

    # Format estate usage data
    estate_usage_data = [
        {
            "name": item.name,
            "electricity": float(item.electricity),
            "water": float(item.water),
            "hot_water": float(item.hot_water),
            "solar": float(item.solar),
        }
        for item in estate_usage_data
    ]

    # Daily Consumption for trend chart
    daily_consumption_query = (
        db.session.query(
            func.date(Transaction.completed_at).label("date"),
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_electricity",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("electricity"),
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_water",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("water"),
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_hot_water",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("hot_water"),
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "consumption_solar",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ).label("solar"),
        )
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Transaction.transaction_type.in_(
                [
                    "consumption_electricity",
                    "consumption_water",
                    "consumption_hot_water",
                    "consumption_solar",
                ]
            ),
            Transaction.status == "completed",
            Transaction.completed_at >= month_start,
            Transaction.completed_at < next_month,
        )
    )
    if estate_filter:
        daily_consumption_query = daily_consumption_query.filter(*estate_filter)
    daily_consumption_data = (
        daily_consumption_query.group_by("date").order_by("date").all()
    )

    # Format daily consumption data
    daily_consumption_data = [
        {
            "date": item.date.strftime("%b %d") if item.date else "",
            "electricity": float(item.electricity),
            "water": float(item.water),
            "hot_water": float(item.hot_water),
            "solar": float(item.solar),
        }
        for item in daily_consumption_data
    ]

    # Average spend per resident (now using tenants)
    from app.models import UnitTenancy
    resident_count = (
        db.session.query(func.count(func.distinct(UnitTenancy.person_id)))
        .filter(UnitTenancy.status == 'active')
        .scalar()
        or 1
    )
    avg_spend_per_resident = (
        float(revenue_collected) / resident_count if resident_count > 0 else 0.0
    )

    # Alerts format
    alerts = []
    for alert in tamper_alerts[:5]:
        alerts.append(
            {
                "alert_type": "system",
                "title": f"{alert.alert_type.replace('_', ' ').title()} Alert",
                "timestamp": alert.created_at
                if hasattr(alert, "created_at")
                else datetime.now(),
                "severity": alert.severity if hasattr(alert, "severity") else "warning",
                "estate_name": None,
                "unit_number": None,
            }
        )

    return render_template(
        "dashboard/index.html",
        # KPI Cards
        kpis={
            "electricity_used_kwh": float(total_electricity_kwh),
            "cold_water_kL": cold_water_kL,
            "hot_water_kL": hot_water_kL,
            "solar_kwh": float(solar_contribution_kwh),
            "solar_contribution_percent": solar_contribution_percent,
            "total_revenue": float(revenue_collected),
        },
        alerts=alerts,
        revenue_by_utility=revenue_by_utility,
        avg_spend_per_resident=avg_spend_per_resident,
        estate_usage_data=estate_usage_data,
        daily_consumption_data=daily_consumption_data,
        estate_filter=estate_id,
        estate_locked=bool(user_estate),
        period=period,
        estates=estates,
        current_month=current_month,
    )


@api_v1.post("/auth/login")
def login():
    payload = request.get_json(force=True) or {}
    # Accept 'credential', 'email', or 'username' — all treated as the identity field
    credential = payload.get("credential") or payload.get("username") or payload.get("email")
    password = payload.get("password")
    if not credential or not password:
        return jsonify({"error": "Invalid credentials", "code": 401}), 401

    # --- Detect credential type and authenticate accordingly ---
    if _is_phone_credential(credential):
        # Phone number → authenticate as portal/mobile user
        success, result = authenticate_mobile_user(credential, password)
        if not success:
            error_msg = result.get("message", "Invalid credentials") if isinstance(result, dict) else "Invalid credentials"
            return jsonify({"error": error_msg, "code": 401}), 401

        mobile_user = result
        logged_in = login_user(mobile_user, force=True)
        if not logged_in:
            return jsonify({"error": "Invalid credentials", "code": 401}), 401

        if current_app.config.get("TESTING"):
            session["_user_id"] = mobile_user.get_id()
            session["_fresh"] = True

        log_action(
            "user.login",
            entity_type="mobile_user",
            entity_id=mobile_user.id,
            new_values={
                "phone_number": mobile_user.phone_number,
                "login_method": "password",
                "user_type": "portal",
            },
        )

        # Determine redirect URL
        if mobile_user.password_must_change:
            redirect_url = url_for("portal.portal_change_password")
        else:
            redirect_url = url_for("portal.portal_dashboard")

        if request.headers.get("Content-Type") == "application/json":
            return jsonify({
                "message": "Logged in",
                "data": {"user_id": mobile_user.id, "user_type": "portal"},
                "redirect": redirect_url,
            })
        else:
            return redirect(redirect_url)

    else:
        # Email/username → authenticate as admin user (existing flow)
        user = User.query.filter(
            (User.username == credential) | (User.email == credential)
        ).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials", "code": 401}), 401

        logged_in = login_user(user, force=True)
        if not logged_in:
            return jsonify({"error": "Invalid credentials", "code": 401}), 401

        if current_app.config.get("TESTING"):
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

        log_action(
            "user.login",
            entity_type="user",
            entity_id=user.id,
            new_values={
                "username": user.username,
                "email": user.email,
                "login_method": "password",
                "user_type": "admin",
            },
        )

        redirect_url = url_for("api_v1.dashboard")

        if request.headers.get("Content-Type") == "application/json":
            return jsonify({
                "message": "Logged in",
                "data": {"user_id": user.id, "user_type": "admin"},
                "redirect": redirect_url,
            })
        else:
            return redirect(redirect_url)


@api_v1.route("/auth/logout", methods=["POST", "GET"])
@login_required
def logout():
    user_id = current_user.id
    username = getattr(current_user, 'username', None) or getattr(current_user, 'phone_number', 'unknown')
    email = getattr(current_user, 'email', None) or ''
    is_portal = _is_portal_user()
    entity_type = "mobile_user" if is_portal else "user"

    logout_user()

    log_action(
        "user.logout",
        entity_type=entity_type,
        entity_id=user_id,
        new_values={"username": username, "email": email},
    )

    # Check if this is a web request or API request
    if request.headers.get("Content-Type") == "application/json":
        return jsonify({"message": "Logged out"})
    else:
        return redirect(url_for("api_v1.login_page"))


@api_v1.post("/auth/change-password")
@login_required
def change_password():
    payload = request.get_json(force=True) or {}
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    if not current_password or not new_password:
        return jsonify({"error": "Missing password fields", "code": 400}), 400

    if not current_user.check_password(current_password):
        return jsonify({"error": "Current password incorrect", "code": 400}), 400

    current_user.set_password(new_password)
    db.session.commit()

    log_action(
        "user.password_change",
        entity_type="user",
        entity_id=current_user.id,
        new_values={"username": current_user.username, "email": current_user.email},
    )

    return jsonify({"message": "Password changed"})
