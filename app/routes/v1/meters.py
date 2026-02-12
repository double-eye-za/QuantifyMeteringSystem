from __future__ import annotations

from datetime import datetime
import io
from flask import jsonify, request, render_template, Response
from sqlalchemy.exc import IntegrityError
from flask_login import login_required, current_user
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from ...models import Meter, MeterReading, Unit, Wallet, Estate, MeterAlert, Transaction
from ...utils.pagination import paginate_query, parse_pagination_params
from ...utils.audit import log_action
from ...utils.decorators import requires_permission
from . import api_v1

from ...services.meters import (
    list_meters as svc_list_meters,
    list_meters_paginated as svc_list_meters_paginated,
    get_meter_by_id as svc_get_meter_by_id,
    create_meter as svc_create_meter,
    list_available_by_type as svc_list_available_by_type,
    list_for_meter_readings as svc_list_for_meter_readings,
)
from ...services.units import find_unit_by_meter_id as svc_find_unit_by_meter_id
from ...services.device_types import list_device_types as svc_list_device_types
from ...services.communication_types import list_communication_types as svc_list_communication_types


@api_v1.route("/meters", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meters_page():
    """Render the meters page with meters, unit assignments, balances, filters and stats."""
    search = request.args.get("search", "").strip() or None
    meter_type = request.args.get("meter_type") or None
    comm_status = request.args.get("communication_status") or None
    estate_id = request.args.get("estate_id", type=int) or None
    credit_status = request.args.get("credit_status") or None

    # Get pagination params
    page, per_page = parse_pagination_params()

    # Use efficient server-side pagination
    meters, meta = svc_list_meters_paginated(
        search=search,
        meter_type=meter_type,
        communication_status=comm_status,
        estate_id=estate_id,
        credit_status=credit_status,
        page=page,
        per_page=per_page,
    )

    # Stats - use efficient queries
    total_meters = Meter.query.count()
    total_active = Meter.query.filter(Meter.is_active == True).count()

    # Low credit count - use efficient subquery
    from sqlalchemy import or_, and_, case
    from ...db import db

    low_credit_subquery = (
        db.session.query(Meter.id)
        .outerjoin(
            Unit,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
            ),
        )
        .outerjoin(Wallet, Wallet.unit_id == Unit.id)
        .filter(
            and_(
                Wallet.id.isnot(None),
                case(
                    (Meter.meter_type == "electricity", Wallet.electricity_balance),
                    (Meter.meter_type == "water", Wallet.water_balance),
                    (Meter.meter_type == "solar", Wallet.solar_balance),
                    (Meter.meter_type == "hot_water", Wallet.hot_water_balance),
                    else_=Wallet.balance,
                ) > 0,
                case(
                    (Meter.meter_type == "electricity", Wallet.electricity_balance),
                    (Meter.meter_type == "water", Wallet.water_balance),
                    (Meter.meter_type == "solar", Wallet.solar_balance),
                    (Meter.meter_type == "hot_water", Wallet.hot_water_balance),
                    else_=Wallet.balance,
                ) < case(
                    (Wallet.low_balance_threshold.isnot(None), Wallet.low_balance_threshold),
                    else_=50.0,
                ),
            )
        )
        .count()
    )
    low_credit_count = low_credit_subquery

    total_alerts = (
        MeterAlert.query.filter_by(is_resolved=False).count()
        if hasattr(MeterAlert, "is_resolved")
        else MeterAlert.query.count()
    )

    estates = [
        {"id": e.id, "name": e.name}
        for e in Estate.query.order_by(Estate.name.asc()).all()
    ]

    # Count meters per estate for header display (within the current result set)
    # Also count unassigned meters
    estate_meter_counts = {}
    unassigned_count = 0
    for m in meters:
        if m.get("unit") and m["unit"].get("estate_id"):
            eid = m["unit"]["estate_id"]
            estate_meter_counts[eid] = estate_meter_counts.get(eid, 0) + 1
        elif m.get("assigned_estate") and m["assigned_estate"].get("id"):
            eid = m["assigned_estate"]["id"]
            estate_meter_counts[eid] = estate_meter_counts.get(eid, 0) + 1
        else:
            unassigned_count += 1
    estate_meter_counts["unassigned"] = unassigned_count

    # Units availability - join with Estate to get estate name
    units_info = []
    units_with_estates = (
        Unit.query
        .join(Estate, Unit.estate_id == Estate.id)
        .order_by(Estate.name.asc(), Unit.unit_number.asc())
        .all()
    )
    for u in units_with_estates:
        units_info.append(
            {
                "id": u.id,
                "unit_number": u.unit_number,
                "estate_id": u.estate_id,
                "estate_name": u.estate.name if u.estate else "",
                "has_electricity": bool(u.electricity_meter_id),
                "has_water": bool(u.water_meter_id),
                "has_solar": bool(u.solar_meter_id),
                "has_hot_water": bool(u.hot_water_meter_id),
            }
        )

    meter_types = [
        {"value": "electricity", "label": "Electricity"},
        {"value": "bulk_electricity", "label": "Bulk Electricity"},
        {"value": "water", "label": "Water"},
        {"value": "hot_water", "label": "Hot Water"},
        {"value": "solar", "label": "Solar"},
    ]

    # Get device types and communication types for dropdowns
    device_types = svc_list_device_types(active_only=True)
    communication_types = svc_list_communication_types(active_only=True)

    return render_template(
        "meters/meters.html",
        meters=meters,
        estates=estates,
        estate_meter_counts=estate_meter_counts,
        units=units_info,
        meter_types=meter_types,
        device_types=device_types,
        communication_types=communication_types,
        pagination=meta,
        stats={
            "total": total_meters,
            "active": total_active,
            "low_credit": low_credit_count,
            "alerts": total_alerts,
        },
        current_filters={
            "search": search,
            "estate_id": estate_id,
            "meter_type": meter_type,
            "communication_status": comm_status,
            "credit_status": credit_status,
        },
    )


@api_v1.route("/api/meters", methods=["GET"])
@login_required
@requires_permission("meters.view")
def list_meters_api():
    """JSON API endpoint for meters list with filters, search, and pagination."""
    search = request.args.get("search", "").strip() or None
    meter_type = request.args.get("meter_type") or None
    comm_status = request.args.get("communication_status") or None
    estate_id = request.args.get("estate_id", type=int) or None
    credit_status = request.args.get("credit_status") or None

    # Get pagination params
    page, per_page = parse_pagination_params()

    # Use efficient server-side pagination
    meters, meta = svc_list_meters_paginated(
        search=search,
        meter_type=meter_type,
        communication_status=comm_status,
        estate_id=estate_id,
        credit_status=credit_status,
        page=page,
        per_page=per_page,
    )

    return jsonify({
        "data": meters,
        "page": meta["page"],
        "per_page": meta["per_page"],
        "total": meta["total"],
        "total_pages": meta["pages"],
    })


@api_v1.route("/api/meters/units-availability", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_units_availability():
    """Get fresh unit availability data for meter assignment dropdowns."""
    units_with_estates = (
        Unit.query
        .join(Estate, Unit.estate_id == Estate.id)
        .order_by(Estate.name.asc(), Unit.unit_number.asc())
        .all()
    )
    units_info = []
    for u in units_with_estates:
        units_info.append({
            "id": u.id,
            "unit_number": u.unit_number,
            "estate_id": u.estate_id,
            "estate_name": u.estate.name if u.estate else "",
            "has_electricity": bool(u.electricity_meter_id),
            "has_water": bool(u.water_meter_id),
            "has_solar": bool(u.solar_meter_id),
            "has_hot_water": bool(u.hot_water_meter_id),
        })
    return jsonify({"units": units_info})


@api_v1.route("/meters/<meter_id>/details", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meter_details_page(meter_id: str):
    """Render the meter details page with enriched data for the selected meter."""
    from datetime import datetime, timedelta

    # Try to find by device_eui first, then by serial_number, then by numeric ID
    meter = Meter.query.filter_by(device_eui=meter_id).first()
    if meter is None:
        meter = Meter.query.filter_by(serial_number=meter_id).first()
    if meter is None and meter_id.isdigit():
        meter = svc_get_meter_by_id(int(meter_id))
    if meter is None:
        return render_template(
            "meters/meter-details.html",
            meter=None,
            error="Meter not found",
            meter_id=meter_id,
        )

    # Assigned unit
    unit = Unit.query.filter(
        (Unit.electricity_meter_id == meter.id)
        | (Unit.water_meter_id == meter.id)
        | (Unit.solar_meter_id == meter.id)
        | (Unit.hot_water_meter_id == meter.id)
    ).first()
    estate = Estate.query.get(unit.estate_id) if unit else None
    # Use backward compatibility: unit.resident returns primary_tenant
    resident = unit.resident if unit else None
    wallet = Wallet.query.filter_by(unit_id=unit.id).first() if unit else None

    def typed_balance(w: Wallet | None, m: Meter) -> float:
        if not w:
            return 0.0
        if m.meter_type == "electricity":
            return float(w.electricity_balance)
        if m.meter_type == "water":
            return float(w.water_balance)
        if m.meter_type == "solar":
            return float(w.solar_balance)
        if m.meter_type == "hot_water":
            return float(w.hot_water_balance)
        return float(w.balance or 0)

    balance_value = typed_balance(wallet, meter)
    low_threshold = (
        float(wallet.low_balance_threshold)
        if wallet and wallet.low_balance_threshold is not None
        else 50.0
    )
    credit_status = (
        "disconnected"
        if balance_value <= 0
        else ("low" if balance_value < low_threshold else "ok")
    )

    # Recent readings (latest 20)
    readings_query = svc_list_for_meter_readings(meter.id)
    readings_items, _ = paginate_query(readings_query)
    recent_readings = [r.to_dict() for r in readings_items]

    # Convert UTC timestamps to SAST (UTC+2) for display
    for reading in recent_readings:
        if reading.get("reading_date"):
            # Parse ISO timestamp and add 2 hours for SAST
            utc_time = datetime.fromisoformat(reading["reading_date"].replace('Z', '+00:00'))
            sast_time = utc_time + timedelta(hours=2)
            reading["reading_date"] = sast_time.strftime("%Y-%m-%d %H:%M:%S")

    # Determine device communication status
    # Consider device online if it communicated within last 30 minutes
    device_status = "offline"
    if meter.last_communication:
        time_since_last_comm = datetime.utcnow() - meter.last_communication
        if time_since_last_comm.total_seconds() < 1800:  # 30 minutes
            device_status = "online"

    meter_dict = meter.to_dict()
    return render_template(
        "meters/meter-details.html",
        meter_id=meter.device_eui or meter.serial_number,
        meter=meter_dict,
        unit=unit,  # Pass the full unit object, not a dictionary
        estate=estate,
        resident=resident,
        wallet=wallet,  # Pass the full wallet object, not a dictionary
        balance_value=balance_value,
        credit_status=credit_status,
        device_status=device_status,
        recent_readings=recent_readings,
    )


@api_v1.get("/meters/<int:meter_id>")
@login_required
@requires_permission("meters.view")
def get_meter(meter_id: int):
    meter = svc_get_meter_by_id(meter_id)
    if not meter:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": meter.to_dict()})


def _assign_meter_to_unit(meter: Meter, unit_id: int | None):
    """Assign the meter to the given unit based on meter_type; handles unassigning from previous unit."""
    # Unassign from any current unit first
    current_unit = Unit.query.filter(
        (Unit.electricity_meter_id == meter.id)
        | (Unit.water_meter_id == meter.id)
        | (Unit.solar_meter_id == meter.id)
        | (Unit.hot_water_meter_id == meter.id)
    ).first()
    if current_unit:
        if current_unit.electricity_meter_id == meter.id:
            current_unit.electricity_meter_id = None
        if current_unit.water_meter_id == meter.id:
            current_unit.water_meter_id = None
        if current_unit.solar_meter_id == meter.id:
            current_unit.solar_meter_id = None
        if current_unit.hot_water_meter_id == meter.id:
            current_unit.hot_water_meter_id = None
    if unit_id:
        target = Unit.query.get(unit_id)
        if target:
            if meter.meter_type == "electricity":
                if target.electricity_meter_id:
                    raise ValueError("Target unit already has an electricity meter")
                target.electricity_meter_id = meter.id
            elif meter.meter_type == "water":
                if target.water_meter_id:
                    raise ValueError("Target unit already has a water meter")
                target.water_meter_id = meter.id
            elif meter.meter_type == "solar":
                if target.solar_meter_id:
                    raise ValueError("Target unit already has a solar meter")
                target.solar_meter_id = meter.id
            elif meter.meter_type == "hot_water":
                if target.hot_water_meter_id:
                    raise ValueError("Target unit already has a hot water meter")
                target.hot_water_meter_id = meter.id
    from ...db import db

    db.session.commit()


def _assign_bulk_meter_to_estate(meter: Meter, estate_id: int | None):
    """Assign a bulk meter to an estate by updating the estate's bulk meter field.
    Clears previous estate linkage if moving.
    """
    if meter.meter_type not in ("bulk_electricity", "bulk_water"):
        return
    from ...db import db

    # Clear any existing estate referencing this meter
    prev = None
    if meter.meter_type == "bulk_electricity":
        prev = Estate.query.filter_by(bulk_electricity_meter_id=meter.id).first()
    elif meter.meter_type == "bulk_water":
        prev = Estate.query.filter_by(bulk_water_meter_id=meter.id).first()
    if prev:
        if meter.meter_type == "bulk_electricity":
            prev.bulk_electricity_meter_id = None
        else:
            prev.bulk_water_meter_id = None

    if estate_id:
        target = Estate.query.get(estate_id)
        if target:
            if meter.meter_type == "bulk_electricity":
                target.bulk_electricity_meter_id = meter.id
            else:
                target.bulk_water_meter_id = meter.id

    db.session.commit()


@api_v1.post("/meters")
@login_required
@requires_permission("meters.create")
def create_meter():
    payload = request.get_json(force=True) or {}
    required = ["serial_number", "meter_type"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    # Validate device_eui length (LoRaWAN EUI-64 = 16 hex characters)
    device_eui = payload.get("device_eui", "").strip()
    if device_eui:
        # Clean and validate device_eui
        device_eui = device_eui.lower().replace(":", "").replace("-", "")
        if len(device_eui) != 16 or not all(c in "0123456789abcdef" for c in device_eui):
            return jsonify({"message": "Device EUI must be exactly 16 hexadecimal characters"}), 400
        payload["device_eui"] = device_eui

    status = (payload.get("status") or "").lower()
    if status in ("active", "inactive"):
        payload["is_active"] = status == "active"
    try:
        meter = svc_create_meter(payload)
    except IntegrityError:
        return jsonify({"message": "Serial number already exists"}), 409
    except Exception as e:
        return jsonify({"message": str(e)}), 400

    unit_id = payload.get("unit_id")
    try:
        if unit_id:
            _assign_meter_to_unit(meter, int(unit_id))
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    # Bulk meter estate assignment (if provided)
    try:
        estate_id_val = payload.get("estate_id")
        if estate_id_val:
            _assign_bulk_meter_to_estate(meter, int(estate_id_val))
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    log_action(
        "meter.create", entity_type="meter", entity_id=meter.id, new_values=payload
    )
    return jsonify(
        {"message": "Meter created successfully", "data": meter.to_dict()}
    ), 201


@api_v1.put("/meters/<int:meter_id>")
@login_required
@requires_permission("meters.edit")
def update_meter(meter_id: int):
    meter = svc_get_meter_by_id(meter_id)
    if not meter:
        return jsonify({"message": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}
    before = meter.to_dict()
    # Status mapping
    status = (payload.get("status") or "").lower()
    if status in ("active", "inactive"):
        payload["is_active"] = status == "active"

    # Validate device_eui if provided
    device_eui = payload.get("device_eui", "").strip() if payload.get("device_eui") else ""
    if device_eui:
        device_eui = device_eui.lower().replace(":", "").replace("-", "")
        if len(device_eui) != 16 or not all(c in "0123456789abcdef" for c in device_eui):
            return jsonify({"message": "Device EUI must be exactly 16 hexadecimal characters"}), 400
        payload["device_eui"] = device_eui
    elif "device_eui" in payload:
        # Allow clearing device_eui by setting to empty string or null
        payload["device_eui"] = None

    for f in ("serial_number", "meter_type", "installation_date", "is_active", "device_eui"):
        if f in payload:
            setattr(meter, f, payload[f])
    from ...db import db

    try:
        db.session.commit()
    except IntegrityError:
        return jsonify({"message": "Serial number or Device EUI already exists"}), 409
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    # Handle assignment changes
    try:
        if "unit_id" in payload:
            _assign_meter_to_unit(
                meter, int(payload["unit_id"]) if payload["unit_id"] else None
            )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    # Handle bulk meter estate assignment change
    try:
        if "estate_id" in payload and payload["estate_id"] is not None:
            _assign_bulk_meter_to_estate(
                meter, int(payload["estate_id"]) if payload["estate_id"] else None
            )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    log_action(
        "meter.update",
        entity_type="meter",
        entity_id=meter_id,
        old_values=before,
        new_values=payload,
    )
    return jsonify({"message": "Meter updated successfully", "data": meter.to_dict()})


@api_v1.delete("/meters/<int:meter_id>")
@login_required
@requires_permission("meters.delete")
def delete_meter(meter_id: int):
    meter = svc_get_meter_by_id(meter_id)
    if not meter:
        return jsonify({"error": "Not Found", "code": 404}), 404
    # Unassign from any unit
    _assign_meter_to_unit(meter, None)
    from ...db import db

    before = meter.to_dict()
    db.session.delete(meter)
    db.session.commit()
    log_action(
        "meter.delete", entity_type="meter", entity_id=meter_id, old_values=before
    )
    return jsonify({"message": "Deleted"})


@api_v1.get("/meters/available")
@login_required
@requires_permission("meters.view")
def available_meters():
    meter_type = request.args.get("meter_type")
    if not meter_type:
        return jsonify({"error": "meter_type is required"}), 400
    items = svc_list_available_by_type(meter_type)
    return jsonify(
        {
            "data": [
                {
                    "id": m.id,
                    "serial_number": m.serial_number,
                    "meter_type": m.meter_type,
                }
                for m in items
            ]
        }
    )


@api_v1.get("/meters/<int:meter_id>/readings")
@login_required
@requires_permission("meters.view")
def meter_readings(meter_id: int):
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    query = svc_list_for_meter_readings(meter_id, start=start_dt, end=end_dt)
    items, meta = paginate_query(query)
    return jsonify({"data": [r.to_dict() for r in items], **meta})


@api_v1.route("/meters/export", methods=["GET"])
@login_required
@requires_permission("meters.view")
def export_meters_pdf():
    """Export meters data to PDF"""
    try:
        meter_type = request.args.get("meter_type") or None
        comm_status = request.args.get("communication_status") or None
        estate_id = request.args.get("estate_id", type=int) or None
        credit_status = request.args.get("credit_status") or None

        query = Meter.query
        if meter_type:
            query = query.filter(Meter.meter_type == meter_type)
        if comm_status:
            query = query.filter(Meter.communication_status == comm_status)
        if estate_id:
            query = query.join(Unit).filter(Unit.estate_id == estate_id)
        if credit_status:
            if credit_status == "low":
                query = query.join(Unit).join(Wallet).filter(Wallet.balance < 50)
            elif credit_status == "sufficient":
                query = query.join(Unit).join(Wallet).filter(Wallet.balance >= 50)

        meters = query.all()

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
        )
        title = Paragraph("Meters Report", title_style)
        story.append(title)

        # Report info
        info_style = ParagraphStyle(
            "Info", parent=styles["Normal"], fontSize=10, spaceAfter=20, alignment=1
        )
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        info_text = f"Generated on {report_date}<br/>Total Meters: {len(meters)}"
        info = Paragraph(info_text, info_style)
        story.append(info)
        story.append(Spacer(1, 20))

        # Create table data
        table_data = [
            [
                "Serial Number",
                "Type",
                "Status",
                "Unit/Location",
                "Estate",
                "Credit Balance",
                "Last Reading",
            ]
        ]

        for meter in meters:
            # Get unit and estate info
            unit = svc_find_unit_by_meter_id(meter.id)
            estate_name = ""
            unit_location = ""

            if unit:
                estate = Estate.query.get(unit.estate_id)
                estate_name = estate.name if estate else ""
                unit_location = (
                    f"{unit.unit_number}" if unit.unit_number else f"Unit {unit.id}"
                )

            # Get wallet balance
            wallet = Wallet.query.filter_by(unit_id=unit.id).first() if unit else None
            if wallet:
                if meter.meter_type == "electricity":
                    balance = f"R {wallet.electricity_balance:.2f}"
                elif meter.meter_type == "water":
                    balance = f"R {wallet.water_balance:.2f}"
                elif meter.meter_type == "solar":
                    balance = f"R {wallet.solar_balance:.2f}"
                else:
                    balance = f"R {wallet.balance:.2f}"
            else:
                balance = "N/A"

            # Get last reading
            readings_query = svc_list_for_meter_readings(meter.id)
            last_reading = readings_query.first()
            last_reading_text = (
                last_reading.reading_date.strftime("%Y-%m-%d")
                if last_reading
                else "No readings"
            )

            status = "Active" if meter.is_active else "Inactive"

            table_data.append(
                [
                    meter.serial_number,
                    meter.meter_type.replace("_", " ").title(),
                    status,
                    unit_location,
                    estate_name,
                    balance,
                    last_reading_text,
                ]
            )

        # Create table
        available_width = doc.width
        col_weights = [1.6, 1.2, 1.0, 1.6, 1.6, 1.4, 1.2]
        total_weight = sum(col_weights)
        col_widths = [available_width * (w / total_weight) for w in col_weights]
        table = Table(table_data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        story.append(table)

        # Build PDF
        doc.build(story)

        # Log the export action
        log_action(
            "meter.export",
            entity_type="meter",
            entity_id=None,
            new_values={"export_type": "pdf", "total_records": len(meters)},
        )

        response = Response(buffer.getvalue(), mimetype="application/pdf")
        response.headers["Content-Disposition"] = (
            f"attachment; filename=meters_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        return response

    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@api_v1.route("/meters", methods=["POST"])
@login_required
@requires_permission("meters.create")
def register_meter():
    """
    Register a new meter (LoRaWAN or 4G cellular devices)

    Expected JSON payload:
    {
        "device_eui": "24e124136f215917",  # Required: DevEUI from ChirpStack or IMEI for 4G
        "meter_type": "water",             # Required: electricity, water, solar, etc.
        "serial_number": "METER-001",      # Optional: auto-filled from device_eui if empty
        "lorawan_device_type": "fengbo_4g",
        "communication_type": "cellular",
        "manufacturer": "Fengbo",
        "model": "Ultrasonic 4G",
        "is_prepaid": true,
        "is_active": true
    }
    """
    try:
        data = request.get_json()

        # Validate required fields - device_eui is the primary identifier
        if not data.get("device_eui"):
            return jsonify({"error": "device_eui is required (DevEUI from ChirpStack or IMEI for 4G devices)"}), 400
        if not data.get("meter_type"):
            return jsonify({"error": "meter_type is required"}), 400

        # Auto-fill serial_number from device_eui if not provided
        if not data.get("serial_number"):
            data["serial_number"] = data["device_eui"]

        # Create the meter
        meter = svc_create_meter(data)

        # Log the action
        log_action(
            "meter.create",
            entity_type="meter",
            entity_id=meter.id,
            new_values={
                "serial_number": meter.serial_number,
                "meter_type": meter.meter_type,
                "device_eui": meter.device_eui,
            },
        )

        return jsonify({
            "message": "Meter registered successfully",
            "meter": meter.to_dict()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        if "unique constraint" in str(e).lower():
            return jsonify({"error": "Meter with this serial number or device EUI already exists"}), 409
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to register meter: {str(e)}"}), 500


@api_v1.route("/meters/<meter_id>/realtime-stats", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meter_realtime_stats(meter_id: str):
    """Get real-time statistics for a specific meter."""
    from sqlalchemy import func
    from datetime import date
    from ...db import db

    # Get meter
    meter = Meter.query.filter_by(device_eui=meter_id).first()
    if not meter:
        return jsonify({"error": "Meter not found"}), 404

    # Get latest reading
    latest_reading = MeterReading.query.filter_by(meter_id=meter.id)\
        .order_by(MeterReading.reading_date.desc())\
        .first()

    # Determine device capabilities based on device type
    capabilities = {
        "measures_power": False,
        "measures_voltage": False,
        "measures_flow": False,
        "measures_temperature": True if meter.lorawan_device_type == "milesight_em300" else False,
        "unit": "kWh" if meter.meter_type in ["electricity", "solar"] else "m³"
    }

    # Calculate today's consumption
    today = date.today()
    today_readings = MeterReading.query.filter(
        MeterReading.meter_id == meter.id,
        func.date(MeterReading.reading_date) == today
    ).all()

    today_consumption = 0.0
    if len(today_readings) >= 2:
        values = [r.reading_value for r in today_readings if r.reading_value is not None]
        if values:
            today_consumption = max(values) - min(values)

    # Check for unit assignment and calculate cost
    unit = svc_find_unit_by_meter_id(meter.id)
    cost = None
    cost_message = None

    if not unit:
        cost_message = "Meter not assigned to unit"
    else:
        # Calculate cost using rate tables
        from app.utils.rates import calculate_consumption_charge

        try:
            # Determine utility type based on meter type
            utility_type = meter.meter_type
            if utility_type == "hot_water":
                utility_type = "water"  # Use water rates for hot water
            elif utility_type not in ("electricity", "water"):
                utility_type = "electricity"  # Default to electricity for solar/bulk

            # Calculate cost for today's consumption
            if today_consumption > 0:
                cost = calculate_consumption_charge(
                    consumption=today_consumption,
                    utility_type=utility_type
                )
            else:
                cost = 0
                cost_message = "No consumption today"
        except Exception as e:
            cost_message = f"Cost calculation error: {str(e)}"

    # Build response
    response = {
        "meter_id": meter.device_eui,
        "meter_type": meter.meter_type,
        "device_type": meter.lorawan_device_type,
        "capabilities": capabilities,
        "latest_reading": {
            "timestamp": latest_reading.reading_date.isoformat() if latest_reading else None,
            "value": float(latest_reading.reading_value) if latest_reading and latest_reading.reading_value else 0.0,
            "pulse_count": latest_reading.pulse_count if latest_reading else None,
            "temperature": float(latest_reading.temperature) if latest_reading and latest_reading.temperature else None,
            "humidity": float(latest_reading.humidity) if latest_reading and latest_reading.humidity else None,
            "battery_level": latest_reading.battery_level if latest_reading else None,
            "rssi": latest_reading.rssi if latest_reading else None,
            "snr": float(latest_reading.snr) if latest_reading and latest_reading.snr else None
        } if latest_reading else None,
        "today": {
            "consumption": round(today_consumption, 2),
            "cost": cost,
            "unit": capabilities["unit"],
            "cost_message": cost_message
        },
        "communication": {
            "last_communication": meter.last_communication.isoformat() if meter.last_communication else None,
            "status": "online" if meter.communication_status == "online" else "offline"
        }
    }

    return jsonify(response), 200


@api_v1.route("/meters/<meter_id>/chart-data", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meter_chart_data(meter_id: str):
    """Get chart data for a specific meter."""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from ...db import db

    # Get meter
    meter = Meter.query.filter_by(device_eui=meter_id).first()
    if not meter:
        return jsonify({"error": "Meter not found"}), 404

    # Get period parameter
    period = request.args.get("period", "day")

    # Determine time range and grouping
    now = datetime.now()
    if period == "hour":
        start_time = now - timedelta(hours=24)
        interval = "hour"
    elif period == "week":
        start_time = now - timedelta(days=7)
        interval = "day"
    elif period == "month":
        start_time = now - timedelta(days=30)
        interval = "day"
    else:  # day
        start_time = now - timedelta(days=1)
        interval = "hour"

    # Get readings for the period
    readings = MeterReading.query.filter(
        MeterReading.meter_id == meter.id,
        MeterReading.reading_date >= start_time
    ).order_by(MeterReading.reading_date).all()

    # Group by interval and calculate consumption
    labels = []
    data = []

    if interval == "hour":
        # Group by hour
        hourly_data = {}
        for reading in readings:
            hour_key = reading.reading_date.strftime("%H:00")
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
            if reading.reading_value is not None:
                hourly_data[hour_key].append(float(reading.reading_value))

        # Generate 24-hour labels
        for i in range(24):
            hour_label = f"{i:02d}:00"
            labels.append(hour_label)

            if hour_label in hourly_data and len(hourly_data[hour_label]) >= 2:
                consumption = max(hourly_data[hour_label]) - min(hourly_data[hour_label])
                data.append(round(consumption, 2))
            else:
                data.append(0.0)

    elif interval == "day":
        # Group by day
        daily_data = {}
        for reading in readings:
            day_key = reading.reading_date.strftime("%Y-%m-%d")
            if day_key not in daily_data:
                daily_data[day_key] = []
            if reading.reading_value is not None:
                daily_data[day_key].append(float(reading.reading_value))

        # Generate labels based on period
        num_days = 7 if period == "week" else 30
        for i in range(num_days):
            day = now - timedelta(days=num_days - i - 1)
            day_key = day.strftime("%Y-%m-%d")
            day_label = day.strftime("%b %d")
            labels.append(day_label)

            if day_key in daily_data and len(daily_data[day_key]) >= 2:
                consumption = max(daily_data[day_key]) - min(daily_data[day_key])
                data.append(round(consumption, 2))
            else:
                data.append(0.0)

    unit = "kWh" if meter.meter_type in ["electricity", "solar"] else "m³"

    response = {
        "labels": labels,
        "data": data,
        "period": period,
        "unit": unit,
        "meter_type": meter.meter_type
    }

    return jsonify(response), 200


@api_v1.route("/meters/<meter_id>/relay", methods=["POST"])
@login_required
@requires_permission("meters.edit")
def meter_relay_control(meter_id: str):
    """
    Send a relay control command to a meter (disconnect/reconnect power).

    Supports:
    - Eastron SDM320C: Write Single Coil via UC100 bridge (fPort 5)
    - IVY EM114039-02: Write Multiple Registers to register 167 (fPort 10)

    The device type is determined from the meter's lorawan_device_type field.

    Expected JSON payload:
    {
        "action": "off"  // "off" to disconnect, "on" to reconnect
    }

    Returns:
        - 200: Command queued successfully
        - 400: Invalid action or missing device_eui
        - 404: Meter not found
        - 500: ChirpStack API error
    """
    from ...services import chirpstack_service

    # Find meter by device_eui, serial_number, or id
    meter = Meter.query.filter_by(device_eui=meter_id).first()
    if meter is None:
        meter = Meter.query.filter_by(serial_number=meter_id).first()
    if meter is None and meter_id.isdigit():
        meter = svc_get_meter_by_id(int(meter_id))

    if meter is None:
        return jsonify({"error": "Meter not found"}), 404

    if not meter.device_eui:
        return jsonify({"error": "Meter does not have a device EUI configured"}), 400

    # Get action from request
    data = request.get_json() or {}
    action = data.get("action", "").lower()

    if action not in ("on", "off"):
        return jsonify({"error": "Invalid action. Must be 'on' or 'off'"}), 400

    # Determine device type from meter's lorawan_device_type field
    device_type = getattr(meter, "lorawan_device_type", None) or "eastron_sdm"

    # Send the relay command via ChirpStack (device-type-aware)
    success, message = chirpstack_service.send_relay_command(
        meter.device_eui, action, device_type=device_type
    )

    if success:
        # Log the action
        log_action(
            f"meter.relay_{action}",
            entity_type="meter",
            entity_id=meter.id,
            new_values={
                "device_eui": meter.device_eui,
                "action": action,
                "device_type": device_type,
            },
        )

        return jsonify({
            "success": True,
            "message": f"Relay {action.upper()} command queued successfully",
            "device_eui": meter.device_eui,
            "action": action,
            "device_type": device_type,
            "note": "Command will be delivered on next device uplink (Class A)"
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": message,
        }), 500


@api_v1.route("/meters/prepaid/zero-balance-report", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_zero_balance_report():
    """
    Get a report of all electricity meters with zero or negative balance.
    These are meters that would be disconnected by the scheduled task.

    This is a DRY RUN - no actual disconnects are performed.

    Returns:
        JSON list of meters with zero/negative electricity balance
    """
    from ...db import db

    try:
        # Find all units with electricity meters that have zero or negative balance
        zero_balance_units = (
            db.session.query(Unit, Wallet, Meter)
            .join(Wallet, Unit.id == Wallet.unit_id)
            .join(Meter, Unit.electricity_meter_id == Meter.id)
            .filter(
                Wallet.electricity_balance <= 0,  # Zero or negative balance
                Meter.device_eui.isnot(None),     # Has LoRaWAN device
                Meter.is_active == True,          # Meter is active
                Unit.is_active == True,           # Unit is active
            )
            .all()
        )

        report = []
        for unit, wallet, meter in zero_balance_units:
            # Get estate name
            estate = Estate.query.get(unit.estate_id)

            report.append({
                'unit_id': unit.id,
                'unit_number': unit.unit_number,
                'estate_id': unit.estate_id,
                'estate_name': estate.estate_name if estate else None,
                'meter_id': meter.id,
                'meter_serial': meter.serial_number,
                'device_eui': meter.device_eui,
                'electricity_balance': float(wallet.electricity_balance),
                'total_balance': float(wallet.balance),
                'can_disconnect': True,  # Has device_eui, so can be controlled
            })

        return jsonify({
            'success': True,
            'total_meters': len(report),
            'note': 'This is a report only - no disconnects performed',
            'meters': report,
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@api_v1.route("/meters/prepaid/test-disconnect-check", methods=["POST"])
@login_required
@requires_permission("meters.edit")
def test_disconnect_check():
    """
    Manually trigger the zero balance disconnect check task (for testing).

    This triggers the same task that runs at 6 AM daily.
    NOTE: The actual disconnect is COMMENTED OUT in the task for safety.

    Returns:
        Task result with list of meters that would be disconnected
    """
    from ...tasks.prepaid_disconnect_tasks import disconnect_zero_balance_meters

    try:
        # Run the task synchronously for immediate feedback
        result = disconnect_zero_balance_meters.apply().get(timeout=60)

        return jsonify({
            'success': True,
            'message': 'Disconnect check completed (dry run mode)',
            'result': result,
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@api_v1.route("/meters/<meter_id>/readings-paginated", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meter_readings_paginated(meter_id: str):
    """
    Get readings for a specific meter with date filtering and pagination.

    Query parameters:
        - start_date: ISO date string (default: today)
        - end_date: ISO date string (default: today)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)

    Returns:
        JSON with readings data and pagination metadata
    """
    from datetime import datetime, date, timedelta
    from ...db import db

    # Find meter by device_eui, serial_number, or id
    meter = Meter.query.filter_by(device_eui=meter_id).first()
    if meter is None:
        meter = Meter.query.filter_by(serial_number=meter_id).first()
    if meter is None and meter_id.isdigit():
        meter = svc_get_meter_by_id(int(meter_id))

    if meter is None:
        return jsonify({"error": "Meter not found"}), 404

    # Parse date filters (default to today)
    today = date.today()
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str).date()
        else:
            start_date = today

        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str).date()
        else:
            end_date = today
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DD)"}), 400

    # Ensure end_date includes the full day
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # Cap at 100

    # Consumption filter
    min_consumption = request.args.get("min_consumption", type=float)

    # Query readings for this meter within date range
    query = MeterReading.query.filter(
        MeterReading.meter_id == meter.id,
        MeterReading.reading_date >= start_datetime,
        MeterReading.reading_date <= end_datetime
    )

    # Apply consumption filter if specified
    if min_consumption is not None:
        query = query.filter(MeterReading.consumption_since_last >= min_consumption)

    query = query.order_by(MeterReading.reading_date.desc())

    # Get total count
    total = query.count()

    # Apply pagination
    readings = query.offset((page - 1) * per_page).limit(per_page).all()

    # Convert to SAST for display
    readings_data = []
    for r in readings:
        r_dict = r.to_dict()
        # Convert UTC to SAST (UTC+2)
        if r.reading_date:
            sast_time = r.reading_date + timedelta(hours=2)
            r_dict["reading_date_sast"] = sast_time.strftime("%Y-%m-%d %H:%M:%S")
        readings_data.append(r_dict)

    return jsonify({
        "data": readings_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0
        },
        "filters": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "meter_id": meter.id,
            "meter_serial": meter.serial_number
        }
    }), 200


@api_v1.route("/meters/<meter_id>/transactions", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meter_transactions(meter_id: str):
    """
    Get transactions for a specific meter with date filtering and pagination.

    Query parameters:
        - start_date: ISO date string (default: today)
        - end_date: ISO date string (default: today)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)

    Returns:
        JSON with transactions data and pagination metadata
    """
    from datetime import datetime, date, timedelta
    from ...db import db

    # Find meter by device_eui, serial_number, or id
    meter = Meter.query.filter_by(device_eui=meter_id).first()
    if meter is None:
        meter = Meter.query.filter_by(serial_number=meter_id).first()
    if meter is None and meter_id.isdigit():
        meter = svc_get_meter_by_id(int(meter_id))

    if meter is None:
        return jsonify({"error": "Meter not found"}), 404

    # Parse date filters (default to today)
    today = date.today()
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str).date()
        else:
            start_date = today

        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str).date()
        else:
            end_date = today
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DD)"}), 400

    # Ensure end_date includes the full day
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # Cap at 100

    # Query transactions for this meter within date range
    query = Transaction.query.filter(
        Transaction.meter_id == meter.id,
        Transaction.created_at >= start_datetime,
        Transaction.created_at <= end_datetime
    ).order_by(Transaction.created_at.desc())

    # Get total count
    total = query.count()

    # Apply pagination
    transactions = query.offset((page - 1) * per_page).limit(per_page).all()

    # Calculate totals for the date range
    from sqlalchemy import func
    totals = db.session.query(
        func.sum(Transaction.amount).label('total_amount'),
        func.sum(Transaction.consumption_kwh).label('total_consumption'),
        func.count(Transaction.id).label('transaction_count')
    ).filter(
        Transaction.meter_id == meter.id,
        Transaction.created_at >= start_datetime,
        Transaction.created_at <= end_datetime
    ).first()

    # Convert to SAST for display
    transactions_data = []
    for t in transactions:
        t_dict = t.to_dict()
        # Convert UTC to SAST (UTC+2)
        if t.created_at:
            sast_time = t.created_at + timedelta(hours=2)
            t_dict["created_at_sast"] = sast_time.strftime("%Y-%m-%d %H:%M:%S")
        transactions_data.append(t_dict)

    return jsonify({
        "data": transactions_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0
        },
        "summary": {
            "total_amount": float(totals.total_amount) if totals.total_amount else 0.0,
            "total_consumption": float(totals.total_consumption) if totals.total_consumption else 0.0,
            "transaction_count": totals.transaction_count or 0
        },
        "filters": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "meter_id": meter.id,
            "meter_serial": meter.serial_number
        }
    }), 200
