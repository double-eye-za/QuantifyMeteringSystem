from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user

from ...models import Unit, Estate, Resident, Meter, RateTable, SystemSetting
from ...utils.pagination import paginate_query
from ...utils.audit import log_action
from ...utils.decorators import requires_permission
from . import api_v1
from ...utils.rates import calculate_estate_bill

from ...services.units import (
    list_units as svc_list_units,
    get_unit_by_id as svc_get_unit_by_id,
    create_unit as svc_create_unit,
    update_unit as svc_update_unit,
    delete_unit as svc_delete_unit,
)
from ...services.meters import list_available_by_type as svc_list_available_meters
from ...services.residents import (
    list_residents_for_dropdown as svc_list_residents_for_dropdown,
)
from ...services.rate_tables import get_rate_table_by_id as svc_get_rate_table_by_id


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

    query = svc_list_units(
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
        for e in Estate.query.order_by(Estate.name.asc()).all()
    ]

    assigned_ids = set()
    for u in Unit.query.with_entities(
        Unit.electricity_meter_id,
        Unit.water_meter_id,
        Unit.hot_water_meter_id,
        Unit.solar_meter_id,
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

    electricity_meters = [
        serialize_meter(m) for m in svc_list_available_meters("electricity")
    ]
    water_meters = [serialize_meter(m) for m in svc_list_available_meters("water")]
    hot_water_meters = [
        serialize_meter(m) for m in svc_list_available_meters("hot_water")
    ]
    solar_meters = [serialize_meter(m) for m in svc_list_available_meters("solar")]

    residents = [
        {"id": r.id, "name": f"{r.first_name} {r.last_name}"}
        for r in svc_list_residents_for_dropdown()
    ]

    return render_template(
        "units/units.html",
        units=units,
        estates=estates,
        electricity_meters=electricity_meters,
        water_meters=water_meters,
        hot_water_meters=hot_water_meters,
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
    query = svc_list_units(
        estate_id=estate_id, occupancy_status=occupancy_status, search=q
    )
    items, meta = paginate_query(query)
    return jsonify({"data": [u.to_dict() for u in items], **meta})


@api_v1.route("/units/<int:unit_id>/wallet-statement", methods=["GET"])
@login_required
@requires_permission("units.view")
def wallet_statement_page(unit_id: int):
    """Render the wallet statement page"""
    from ...models import Unit, Wallet, Estate, Transaction
    from ...db import db
    from sqlalchemy import func

    # Get unit and wallet data
    unit = svc_get_unit_by_id(unit_id)
    if not unit:
        return render_template("errors/404.html"), 404

    wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    if not wallet:
        return "Wallet not found", 404

    estate = Estate.query.get(unit.estate_id)

    # Transactions
    txn_query = Transaction.query.filter_by(wallet_id=wallet.id).order_by(
        Transaction.completed_at.desc()
    )
    txn_items, txn_meta = paginate_query(txn_query)

    # Get last topup date
    last_topup = (
        Transaction.query.filter_by(
            wallet_id=wallet.id, transaction_type="topup", status="completed"
        )
        .order_by(Transaction.completed_at.desc())
        .first()
    )
    last_topup_date = last_topup.completed_at if last_topup else None

    # Calculate month-to-date usage
    from datetime import datetime, timedelta

    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    month_transactions = (
        Transaction.query.filter_by(wallet_id=wallet.id)
        .filter(
            Transaction.completed_at >= month_start, Transaction.completed_at <= now
        )
        .all()
    )

    # Calculate usage statistics (in physical units via meter readings)
    # Sum meter readings for the current month
    from ...models.meter_reading import MeterReading
    from ...db import db
    from sqlalchemy import func

    def sum_month_usage_for_meter(meter_id: int):
        if not meter_id:
            return 0.0
        total = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .filter_by(meter_id=meter_id)
            .filter(
                MeterReading.reading_date >= month_start,
                MeterReading.reading_date <= now,
            )
            .scalar()
        ) or 0.0
        return float(total)

    electricity_kwh = sum_month_usage_for_meter(unit.electricity_meter_id)
    water_kl = sum_month_usage_for_meter(unit.water_meter_id)
    hot_water_kwh = sum_month_usage_for_meter(unit.hot_water_meter_id)
    solar_kwh = sum_month_usage_for_meter(unit.solar_meter_id)

    # Daily averages per utility (units/day)
    days_in_period = now.day if now.day > 0 else 1
    electricity_kwh_daily = electricity_kwh / days_in_period
    water_kl_daily = water_kl / days_in_period
    hot_water_kwh_daily = hot_water_kwh / days_in_period
    solar_kwh_daily = solar_kwh / days_in_period

    # For backward compatibility with template pieces that referenced totals
    electricity_total = electricity_kwh
    water_total = water_kl
    hot_water_total = hot_water_kwh
    total_usage = electricity_kwh + water_kl + hot_water_kwh
    daily_average = electricity_kwh_daily + water_kl_daily + hot_water_kwh_daily

    # Calculate days until depletion based on previous currency-based estimate is no longer meaningful; set to 0
    days_left = 0
    projected_usage = 0
    projected_balance = float(wallet.balance)

    # Get meter readings for consumption display
    from ...models.meter_reading import MeterReading

    meter_readings = {}
    if unit.electricity_meter_id:
        latest = (
            MeterReading.query.filter_by(meter_id=unit.electricity_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest:
            meter_readings["electricity"] = latest

    if unit.water_meter_id:
        latest = (
            MeterReading.query.filter_by(meter_id=unit.water_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest:
            meter_readings["water"] = latest

    if unit.hot_water_meter_id:
        latest = (
            MeterReading.query.filter_by(meter_id=unit.hot_water_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest:
            meter_readings["hot_water"] = latest

    if unit.solar_meter_id:
        latest = (
            MeterReading.query.filter_by(meter_id=unit.solar_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest:
            meter_readings["solar"] = latest

    return render_template(
        "wallets/wallet-statement.html",
        unit=unit,
        wallet=wallet,
        estate=estate,
        transactions=txn_items,
        transactions_pagination=txn_meta,
        last_topup_date=last_topup_date,
        electricity_total=electricity_total,
        water_total=water_total,
        hot_water_total=hot_water_total,
        total_usage=total_usage,
        daily_average=daily_average,
        days_left=days_left,
        projected_balance=projected_balance,
        projected_usage=projected_usage,
        # New unit-based fields
        electricity_kwh=electricity_kwh,
        water_kl=water_kl,
        hot_water_kwh=hot_water_kwh,
        solar_kwh=solar_kwh,
        electricity_kwh_daily=electricity_kwh_daily,
        water_kl_daily=water_kl_daily,
        hot_water_kwh_daily=hot_water_kwh_daily,
        solar_kwh_daily=solar_kwh_daily,
        meter_readings=meter_readings,
        current_date=now,
    )


@api_v1.route("/units/<int:unit_id>/visual", methods=["GET"])
@login_required
@requires_permission("units.view")
def unit_visual_page(unit_id: int):
    """Render the unit visual diagram page"""
    unit = svc_get_unit_by_id(unit_id)
    if not unit:
        return render_template("errors/404.html"), 404

    elec_serial = water_serial = solar_serial = hot_water_serial = None
    if unit.electricity_meter_id:
        m = Meter.query.get(unit.electricity_meter_id)
        elec_serial = getattr(m, "serial_number", None) if m else None
    if unit.water_meter_id:
        m = Meter.query.get(unit.water_meter_id)
        water_serial = getattr(m, "serial_number", None) if m else None
    if unit.solar_meter_id:
        m = Meter.query.get(unit.solar_meter_id)
        solar_serial = getattr(m, "serial_number", None) if m else None
    if unit.hot_water_meter_id:
        m = Meter.query.get(unit.hot_water_meter_id)
        hot_water_serial = getattr(m, "serial_number", None) if m else None

    # Rate tables - use unit override if available, else estate default
    estate = Estate.query.get(unit.estate_id) if unit.estate_id else None
    elec_rate_table_id = unit.electricity_rate_table_id or (
        estate.electricity_rate_table_id if estate else None
    )
    water_rate_table_id = unit.water_rate_table_id or (
        estate.water_rate_table_id if estate else None
    )

    elec_rate_name = water_rate_name = ""
    if elec_rate_table_id:
        rt = RateTable.query.get(elec_rate_table_id)
        elec_rate_name = rt.name if rt else "Standard Residential"
    else:
        elec_rate_name = "Standard Residential"

    if water_rate_table_id:
        rt = RateTable.query.get(water_rate_table_id)
        water_rate_name = rt.name if rt else "Standard Residential Water"
    else:
        water_rate_name = "Standard Residential Water"

    # Wallet
    wallet = getattr(unit, "wallet", None)

    # Resident data
    resident = None
    if unit.resident_id:
        resident = Resident.query.get(unit.resident_id)

    # Today's usage from transactions
    from datetime import datetime, timedelta
    from ...models.transaction import Transaction
    from ...db import db
    from sqlalchemy import func

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now()

    today_usage = {"electricity": 0.0, "solar": 0.0, "water": 0.0, "hot_water": 0.0}
    if wallet:
        today_transactions = (
            Transaction.query.filter_by(wallet_id=wallet.id)
            .filter(
                Transaction.completed_at >= today_start,
                Transaction.completed_at <= today_end,
            )
            .all()
        )

        for txn in today_transactions:
            if txn.transaction_type == "consumption_electricity":
                # Use consumption_kwh if available, otherwise estimate from amount
                today_usage["electricity"] += float(
                    txn.consumption_kwh or txn.amount or 0
                )
            elif txn.transaction_type == "consumption_solar":
                today_usage["solar"] += float(txn.consumption_kwh or txn.amount or 0)
            elif txn.transaction_type == "consumption_water":
                # Convert amount or use consumption if available (in kL)
                today_usage["water"] += float(txn.consumption_kwh or txn.amount or 0)
            elif txn.transaction_type == "consumption_hot_water":
                today_usage["hot_water"] += float(
                    txn.consumption_kwh or txn.amount or 0
                )

    # Meter details
    from ...models.meter_reading import MeterReading

    def get_meter_details(meter_id, meter_type):
        if not meter_id:
            return None

        meter = Meter.query.get(meter_id)
        if not meter:
            return None

        # Latest reading
        latest_reading = (
            MeterReading.query.filter_by(meter_id=meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )

        # Total usage/generation (sum of all consumption_since_last)
        total_usage = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .filter_by(meter_id=meter_id)
            .scalar()
        ) or 0.0

        # Last reading date
        last_reading_date = latest_reading.reading_date if latest_reading else None
        last_reading_ago = None
        if last_reading_date:
            delta = datetime.now() - last_reading_date
            if delta.days > 0:
                last_reading_ago = (
                    f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
                )
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                last_reading_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            else:
                minutes = delta.seconds // 60
                last_reading_ago = (
                    f"{minutes} min{'s' if minutes > 1 else ''} ago"
                    if minutes > 0
                    else "Just now"
                )

        return {
            "serial_number": meter.serial_number,
            "type": f"{meter.model or 'Unknown'} {meter.meter_type.title()}"
            if meter.model
            else meter.meter_type.title(),
            "total_usage": float(total_usage),
            "last_reading_date": last_reading_date,
            "last_reading_ago": last_reading_ago or "No readings",
            "communication_status": meter.communication_status or "unknown",
        }

    # Get meter details
    elec_meter_details = get_meter_details(unit.electricity_meter_id, "electricity")
    water_meter_details = get_meter_details(unit.water_meter_id, "water")
    solar_meter_details = get_meter_details(unit.solar_meter_id, "solar")
    hot_water_meter_details = get_meter_details(unit.hot_water_meter_id, "hot_water")

    # calculate free remaining for solar (based on current month usage)
    if solar_meter_details and estate:
        free_allocation = float(estate.solar_free_allocation_kwh or 0)
        total_generated = solar_meter_details["total_usage"]
        solar_meter_details["total_generated"] = total_generated

        # Calculate current month's solar generation
        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if unit.solar_meter_id:
            month_solar = (
                db.session.query(func.sum(MeterReading.consumption_since_last))
                .filter_by(meter_id=unit.solar_meter_id)
                .filter(MeterReading.reading_date >= month_start)
                .scalar()
            ) or 0.0
            # Free remaining is allocation minus what's been used this month
            solar_meter_details["free_remaining"] = max(
                0, free_allocation - float(month_solar)
            )
        else:
            solar_meter_details["free_remaining"] = free_allocation

    # Supply status for electricity (based on wallet balance)
    if elec_meter_details and wallet:
        if float(wallet.balance) > 0:
            elec_meter_details["supply_status"] = "Connected"
        else:
            elec_meter_details["supply_status"] = "Disconnected"

    return render_template(
        "units/unit-visual.html",
        unit=unit,
        elec_serial=elec_serial,
        water_serial=water_serial,
        solar_serial=solar_serial,
        hot_water_serial=hot_water_serial,
        elec_rate_name=elec_rate_name,
        water_rate_name=water_rate_name,
        wallet=wallet,
        resident=resident,
        today_usage=today_usage,
        elec_meter_details=elec_meter_details,
        water_meter_details=water_meter_details,
        solar_meter_details=solar_meter_details,
        hot_water_meter_details=hot_water_meter_details,
    )


@api_v1.get("/units/<int:unit_id>/wallet-statement.pdf")
@login_required
@requires_permission("units.view")
def wallet_statement_pdf(unit_id: int):
    """Generate a PDF wallet statement for the unit using ReportLab."""
    from flask import send_file
    import io
    from datetime import datetime
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    # Compute current month unit totals
    unit = svc_get_unit_by_id(unit_id)
    if not unit:
        return render_template("errors/404.html"), 404

    from ...models import Wallet, Transaction

    wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    if not wallet:
        return "Wallet not found", 404

    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    # Sum usage from meter readings
    from ...models.meter_reading import MeterReading
    from ...db import db
    from sqlalchemy import func

    def sum_month_usage_for_meter(meter_id: int) -> float:
        if not meter_id:
            return 0.0
        total = (
            db.session.query(func.sum(MeterReading.consumption_since_last))
            .filter_by(meter_id=meter_id)
            .filter(
                MeterReading.reading_date >= month_start,
                MeterReading.reading_date <= now,
            )
            .scalar()
        ) or 0.0
        return float(total)

    electricity_kwh = sum_month_usage_for_meter(unit.electricity_meter_id)
    water_kl = sum_month_usage_for_meter(unit.water_meter_id)
    hot_water_kwh = sum_month_usage_for_meter(unit.hot_water_meter_id)
    solar_kwh = sum_month_usage_for_meter(unit.solar_meter_id)

    # Gather this month's transactions
    month_txns = (
        Transaction.query.filter_by(wallet_id=wallet.id)
        .filter(
            Transaction.completed_at >= month_start, Transaction.completed_at <= now
        )
        .order_by(Transaction.completed_at.asc())
        .all()
    )

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "StatementTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=18,
        alignment=1,
    )
    story = []

    # Title and header
    statement_title = f"Wallet Statement - Unit {unit.unit_number}"
    story.append(Paragraph(statement_title, title_style))
    date_text = (
        f"Period: {month_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}"
    )
    story.append(Paragraph(date_text, styles["Normal"]))
    story.append(
        Paragraph(f"Current Balance: R {float(wallet.balance):.2f}", styles["Normal"])
    )
    story.append(Spacer(1, 12))

    # Utility summary table
    summary_headers = [
        "Utility",
        "Total",
        "Unit",
    ]
    summary_rows = [
        ["Electricity", f"{electricity_kwh:.2f}", "kWh"],
        ["Water", f"{water_kl:.2f}", "kL"],
        ["Hot Water", f"{hot_water_kwh:.2f}", "kWh"],
        ["Solar", f"{solar_kwh:.2f}", "kWh"],
    ]
    summary_table = Table([summary_headers] + summary_rows)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 18))

    # Transactions table (limited columns)
    txn_headers = ["Date", "Type", "Description", "Debit", "Credit"]
    txn_rows = []
    for t in month_txns:
        date_str = t.completed_at.strftime("%Y-%m-%d %H:%M") if t.completed_at else ""
        is_topup = t.transaction_type == "topup"
        debit = f"R {float(t.amount):.2f}" if not is_topup else ""
        credit = f"R {float(t.amount):.2f}" if is_topup else ""
        txn_rows.append(
            [
                date_str,
                (t.transaction_type or "").replace("_", " ").title(),
                t.description or (t.reference or ""),
                debit,
                credit,
            ]
        )

    if txn_rows:
        txn_table = Table([txn_headers] + txn_rows)
        txn_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(Paragraph("Transactions (Current Month)", styles["Heading3"]))
        story.append(Spacer(1, 6))
        story.append(txn_table)
    else:
        story.append(Paragraph("No transactions for this month.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)

    filename = f"wallet_statement_unit_{unit.unit_number}_{now.strftime('%Y_%m')}.pdf"
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@api_v1.route("/units/<int:unit_id>", methods=["GET"])
@login_required
@requires_permission("units.view")
def unit_details_page(unit_id: int):
    """Render the unit details page with dynamic unit and resident info"""
    unit = svc_get_unit_by_id(unit_id)
    if not unit:
        return render_template("errors/404.html"), 404

    estate = None
    if getattr(unit, "estate_id", None):
        estate = Estate.query.get(unit.estate_id)

    resident = None
    if getattr(unit, "resident_id", None):
        resident = Resident.query.get(unit.resident_id)

    # Get wallet for the unit
    wallet = None
    if hasattr(unit, "id"):
        from ...models.wallet import Wallet

        wallet = Wallet.query.filter_by(unit_id=unit.id).first()

    # Get recent transactions for this unit's wallet
    recent_transactions = []
    if wallet:
        from ...models.transaction import Transaction

        recent_transactions = (
            Transaction.query.filter_by(wallet_id=wallet.id)
            .order_by(Transaction.completed_at.desc())
            .limit(10)
            .all()
        )

    # Get latest meter readings for all 4 meters
    meter_readings = {}
    from ...models.meter_reading import MeterReading

    if unit.electricity_meter_id:
        latest_electricity = (
            MeterReading.query.filter_by(meter_id=unit.electricity_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest_electricity:
            meter_readings["electricity"] = latest_electricity

    if unit.water_meter_id:
        latest_water = (
            MeterReading.query.filter_by(meter_id=unit.water_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest_water:
            meter_readings["water"] = latest_water

    if unit.hot_water_meter_id:
        latest_hot_water = (
            MeterReading.query.filter_by(meter_id=unit.hot_water_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest_hot_water:
            meter_readings["hot_water"] = latest_hot_water

    if unit.solar_meter_id:
        latest_solar = (
            MeterReading.query.filter_by(meter_id=unit.solar_meter_id)
            .order_by(MeterReading.reading_date.desc())
            .first()
        )
        if latest_solar:
            meter_readings["solar"] = latest_solar

    return render_template(
        "units/unit-details.html",
        unit=unit,
        estate=estate,
        resident=resident,
        wallet=wallet,
        recent_transactions=recent_transactions,
        meter_readings=meter_readings,
    )


@api_v1.get("/api/units/<int:unit_id>")
@login_required
@requires_permission("units.view")
def get_unit(unit_id: int):
    unit = svc_get_unit_by_id(unit_id)
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

    rt = svc_get_rate_table_by_id(int(rate_table_id))
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

        svc_update_unit(unit_obj, {}, getattr(current_user, "id", None))
        updated_unit_ids.append(unit_obj.id)

    if unit_ids:
        for uid in unit_ids:
            u = svc_get_unit_by_id(int(uid))
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

        svc_update_unit(unit_obj, {}, getattr(current_user, "id", None))
        updated_unit_ids.append(unit_obj.id)

    if unit_ids:
        for uid in unit_ids:
            u = svc_get_unit_by_id(int(uid))
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
    unit = svc_create_unit(payload, user_id=getattr(current_user, "id", None))
    log_action("unit.create", entity_type="unit", entity_id=unit.id, new_values=payload)
    return jsonify({"data": unit.to_dict()}), 201


@api_v1.put("/units/<int:unit_id>")
@login_required
@requires_permission("units.edit")
def update_unit(unit_id: int):
    unit = svc_get_unit_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    before = unit.to_dict()
    svc_update_unit(unit, payload, user_id=getattr(current_user, "id", None))
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
    unit = svc_get_unit_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Not Found", "code": 404}), 404
    svc_delete_unit(unit)
    log_action("unit.delete", entity_type="unit", entity_id=unit_id)
    return jsonify({"message": "Deleted"})
