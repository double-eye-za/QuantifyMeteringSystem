"""
Meter Telemetry routes — view and export raw KPM31 telemetry data.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime

from flask import jsonify, request, render_template, send_file
from flask_login import login_required

from ...db import db
from ...models import Kpm31Telemetry, Meter
from ...utils.pagination import paginate_query, parse_pagination_params
from ...utils.decorators import requires_permission
from . import api_v1


# ───────────────────────────────────────────────────────
# Page route
# ───────────────────────────────────────────────────────

@api_v1.route("/meter-telemetry", methods=["GET"])
@login_required
@requires_permission("meters.view")
def meter_telemetry_page():
    """Render the meter telemetry page with filters and initial data."""
    # Get KPM31 meters for the filter dropdown
    kpm31_meters = (
        Meter.query
        .filter_by(lorawan_device_type="kpm31", is_active=True)
        .order_by(Meter.serial_number)
        .all()
    )
    meters_list = [
        {"id": m.id, "serial_number": m.serial_number, "model": m.model or "KPM31"}
        for m in kpm31_meters
    ]

    # Read current filter values so the template can pre-select them
    current_filters = {
        "meter_id": request.args.get("meter_id", type=int),
        "phase_type": request.args.get("phase_type") or None,
        "date_from": request.args.get("date_from") or None,
        "date_to": request.args.get("date_to") or None,
    }

    # Quick stats
    total_records = Kpm31Telemetry.query.count()
    single_count = Kpm31Telemetry.query.filter_by(phase_type="single").count()
    three_count = Kpm31Telemetry.query.filter_by(phase_type="three").count()

    return render_template(
        "telemetry/meter_telemetry.html",
        meters=meters_list,
        current_filters=current_filters,
        stats={
            "total": total_records,
            "single": single_count,
            "three": three_count,
        },
    )


# ───────────────────────────────────────────────────────
# JSON API for AJAX table filtering
# ───────────────────────────────────────────────────────

@api_v1.route("/api/meter-telemetry", methods=["GET"])
@login_required
@requires_permission("meters.view")
def list_meter_telemetry_api():
    """JSON API endpoint for meter telemetry with filters and pagination."""
    meter_id = request.args.get("meter_id", type=int)
    phase_type = request.args.get("phase_type") or None
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None

    query = (
        db.session.query(Kpm31Telemetry, Meter.serial_number)
        .join(Meter, Kpm31Telemetry.meter_id == Meter.id)
    )

    if meter_id:
        query = query.filter(Kpm31Telemetry.meter_id == meter_id)
    if phase_type:
        query = query.filter(Kpm31Telemetry.phase_type == phase_type)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Kpm31Telemetry.recorded_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            # Include the whole day
            dt_to = dt_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Kpm31Telemetry.recorded_at <= dt_to)
        except ValueError:
            pass

    query = query.order_by(Kpm31Telemetry.recorded_at.desc())

    # Pagination
    page, per_page = parse_pagination_params()
    total = query.order_by(None).count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()

    from math import ceil
    pages = ceil(total / per_page) if per_page else 1

    data = []
    for telemetry, serial_number in items:
        row = telemetry.to_dict()
        row["serial_number"] = serial_number
        data.append(row)

    return jsonify({
        "data": data,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": pages,
    })


# ───────────────────────────────────────────────────────
# CSV Export
# ───────────────────────────────────────────────────────

# Columns to include in CSV (human-readable header → to_dict() key)
CSV_COLUMNS = [
    ("ID", "id"),
    ("Recorded At", "recorded_at"),
    ("Device Timestamp", "device_timestamp"),
    ("Phase Type", "phase_type"),
    # Single-phase
    ("Voltage (V)", "voltage"),
    ("Current (A)", "current"),
    ("Prepaid Balance (kWh)", "prepaid_balance_kwh"),
    ("Current Demand (A)", "current_demand"),
    # Three-phase voltages
    ("Voltage A (V)", "voltage_a"),
    ("Voltage B (V)", "voltage_b"),
    ("Voltage C (V)", "voltage_c"),
    ("Voltage AB (V)", "voltage_ab"),
    ("Voltage BC (V)", "voltage_bc"),
    ("Voltage CA (V)", "voltage_ca"),
    # Three-phase currents
    ("Current A (A)", "current_a"),
    ("Current B (A)", "current_b"),
    ("Current C (A)", "current_c"),
    # Three-phase power
    ("Active Power A (kW)", "active_power_a"),
    ("Active Power B (kW)", "active_power_b"),
    ("Active Power C (kW)", "active_power_c"),
    ("Apparent Power A (kVA)", "apparent_power_a"),
    ("Apparent Power B (kVA)", "apparent_power_b"),
    ("Apparent Power C (kVA)", "apparent_power_c"),
    ("PF A", "power_factor_a"),
    ("PF B", "power_factor_b"),
    ("PF C", "power_factor_c"),
    # System totals
    ("Total Active Power (kW)", "total_active_power"),
    ("Total Reactive Power (kvar)", "total_reactive_power"),
    ("Total Apparent Power (kVA)", "total_apparent_power"),
    ("Total Power Factor", "total_power_factor"),
    ("Frequency (Hz)", "frequency"),
    # Demand
    ("Active Demand (kW)", "active_demand"),
    ("Reactive Demand (kvar)", "reactive_demand"),
    ("Apparent Demand (kVA)", "apparent_demand"),
    # Sequence components
    ("Voltage Zero Seq (V)", "voltage_zero_seq"),
    ("Voltage Pos Seq (V)", "voltage_pos_seq"),
    ("Voltage Neg Seq (V)", "voltage_neg_seq"),
    ("Current Zero Seq (A)", "current_zero_seq"),
    ("Current Pos Seq (A)", "current_pos_seq"),
    ("Current Neg Seq (A)", "current_neg_seq"),
    # Fundamental
    ("Voltage Fund A (V)", "voltage_fund_a"),
    ("Voltage Fund B (V)", "voltage_fund_b"),
    ("Voltage Fund C (V)", "voltage_fund_c"),
    ("Current Fund A (A)", "current_fund_a"),
    ("Current Fund B (A)", "current_fund_b"),
    ("Current Fund C (A)", "current_fund_c"),
    # Unbalance
    ("Voltage Unbalance (%)", "voltage_unbalance"),
    ("Current Unbalance (%)", "current_unbalance"),
    # Metadata
    ("Isend", "isend"),
]

MAX_EXPORT_ROWS = 50000


@api_v1.route("/meter-telemetry/export", methods=["GET"])
@login_required
@requires_permission("meters.view")
def export_meter_telemetry():
    """Export meter telemetry data as CSV."""
    meter_id = request.args.get("meter_id", type=int)
    phase_type = request.args.get("phase_type") or None
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None

    query = (
        db.session.query(Kpm31Telemetry, Meter.serial_number)
        .join(Meter, Kpm31Telemetry.meter_id == Meter.id)
    )

    if meter_id:
        query = query.filter(Kpm31Telemetry.meter_id == meter_id)
    if phase_type:
        query = query.filter(Kpm31Telemetry.phase_type == phase_type)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Kpm31Telemetry.recorded_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            dt_to = dt_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Kpm31Telemetry.recorded_at <= dt_to)
        except ValueError:
            pass

    query = query.order_by(Kpm31Telemetry.recorded_at.desc())
    rows = query.limit(MAX_EXPORT_ROWS).all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row — add Meter Serial as the second column
    headers = [CSV_COLUMNS[0][0], "Meter Serial"] + [h for h, _ in CSV_COLUMNS[1:]]
    writer.writerow(headers)

    # Data rows
    for telemetry, serial_number in rows:
        d = telemetry.to_dict()
        row = [d.get(CSV_COLUMNS[0][1], ""), serial_number]
        for _, key in CSV_COLUMNS[1:]:
            val = d.get(key)
            row.append(val if val is not None else "")
        writer.writerow(row)

    output.seek(0)
    filename = f"meter_telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )
