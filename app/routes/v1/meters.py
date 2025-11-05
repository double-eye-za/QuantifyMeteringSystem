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

from ...models import Meter, MeterReading, Unit, Wallet, Estate, MeterAlert, Resident
from ...utils.pagination import paginate_query, parse_pagination_params
from ...utils.audit import log_action
from ...utils.decorators import requires_permission
from . import api_v1

from ...services.meters import (
    list_meters as svc_list_meters,
    get_meter_by_id as svc_get_meter_by_id,
    create_meter as svc_create_meter,
    list_available_by_type as svc_list_available_by_type,
    list_for_meter_readings as svc_list_for_meter_readings,
)
from ...services.units import find_unit_by_meter_id as svc_find_unit_by_meter_id


@api_v1.route("/meters", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meters_page():
    """Render the meters page with meters, unit assignments, balances, filters and stats."""
    meter_type = request.args.get("meter_type") or None
    comm_status = request.args.get("communication_status") or None
    estate_id = request.args.get("estate_id", type=int) or None
    credit_status = request.args.get("credit_status") or None

    base_query = svc_list_meters(
        meter_type=meter_type, communication_status=comm_status
    )
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
        # Find assigned unit
        unit = Unit.query.filter(
            (Unit.electricity_meter_id == m.id)
            | (Unit.water_meter_id == m.id)
            | (Unit.solar_meter_id == m.id)
        ).first()
        # For bulk meters, resolve estate assignment directly on estate
        assigned_estate = None
        if not unit and m.meter_type in ("bulk_electricity", "bulk_water"):
            if m.meter_type == "bulk_electricity":
                assigned_estate = Estate.query.filter_by(
                    bulk_electricity_meter_id=m.id
                ).first()
            elif m.meter_type == "bulk_water":
                assigned_estate = Estate.query.filter_by(
                    bulk_water_meter_id=m.id
                ).first()
        # Estate filter via unit or assigned estate (for bulk meters) if requested
        if estate_id:
            unit_estate_id = unit.estate_id if unit else None
            bulk_estate_id = assigned_estate.id if assigned_estate else None
            if unit_estate_id != estate_id and bulk_estate_id != estate_id:
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
                "assigned_estate": {
                    "id": assigned_estate.id,
                    "name": assigned_estate.name,
                }
                if assigned_estate
                else None,
                "wallet": wallet.to_dict() if wallet else None,
                "credit_status": derived_credit,
            }
        )

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
    total_meters = Meter.query.count()
    total_active = Meter.query.filter(Meter.is_active == True).count()
    # Low credit meters evaluated via associated wallets
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

    # Units availability
    units_info = []
    for u in Unit.query.order_by(Unit.unit_number.asc()).all():
        units_info.append(
            {
                "id": u.id,
                "unit_number": u.unit_number,
                "estate_id": u.estate_id,
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

    return render_template(
        "meters/meters.html",
        meters=meters,
        estates=estates,
        units=units_info,
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
@requires_permission("meters.view")
def meter_details_page(meter_id: str):
    """Render the meter details page with enriched data for the selected meter."""
    from datetime import datetime, timedelta

    # Try to find by device_eui first (LoRaWAN devices), then by ID
    meter = Meter.query.filter_by(device_eui=meter_id).first()
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
    ).first()
    estate = Estate.query.get(unit.estate_id) if unit else None
    resident = (
        Resident.query.get(unit.resident_id) if unit and unit.resident_id else None
    )
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
        meter_id=meter.serial_number,
        meter=meter_dict,
        unit={
            "unit_number": unit.unit_number,
            "estate_name": estate.name if estate else None,
            "resident_name": (
                f"{resident.first_name} {resident.last_name}" if resident else None
            ),
        }
        if unit
        else None,
        wallet=wallet.to_dict() if wallet else None,
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
    ).first()
    if current_unit:
        if current_unit.electricity_meter_id == meter.id:
            current_unit.electricity_meter_id = None
        if current_unit.water_meter_id == meter.id:
            current_unit.water_meter_id = None
        if current_unit.solar_meter_id == meter.id:
            current_unit.solar_meter_id = None
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

    for f in ("serial_number", "meter_type", "installation_date", "is_active"):
        if f in payload:
            setattr(meter, f, payload[f])
    from ...db import db

    try:
        db.session.commit()
    except IntegrityError:
        return jsonify({"message": "Serial number already exists"}), 409
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
    Register a new meter (including LoRaWAN devices)

    Expected JSON payload:
    {
        "serial_number": "24e124136f215917",
        "meter_type": "electricity",
        "manufacturer": "Milesight",
        "model": "EM300-DI",
        "device_eui": "24e124136f215917",
        "lorawan_device_type": "milesight_em300",
        "communication_type": "cellular",
        "is_prepaid": true,
        "is_active": true
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get("serial_number"):
            return jsonify({"error": "serial_number is required"}), 400
        if not data.get("meter_type"):
            return jsonify({"error": "meter_type is required"}), 400

        # For LoRaWAN devices, device_eui is required
        if data.get("communication_type") == "cellular" and not data.get("device_eui"):
            return jsonify({"error": "device_eui is required for LoRaWAN devices"}), 400

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
        # TODO: Implement cost calculation with rate tables
        cost_message = "Rate table not configured"

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
