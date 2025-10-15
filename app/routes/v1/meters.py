from __future__ import annotations

from datetime import datetime
from flask import jsonify, request, render_template
from flask_login import login_required

from ...models import Meter, MeterReading
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.route("/meters", methods=["GET"])
@login_required
def meters_page():
    """Render the meters page"""
    return render_template("meters/meters.html")


@api_v1.route("/meters/<meter_id>/details", methods=["GET"])
@login_required
def meter_details_page(meter_id: str):
    """Render the meter details page"""
    return render_template("meters/meter-details.html", meter_id=meter_id)


@api_v1.get("/api/meters")
@login_required
def list_meters():
    meter_type = request.args.get("meter_type")
    comm_status = request.args.get("communication_status")
    query = Meter.get_all(meter_type=meter_type, communication_status=comm_status)
    items, meta = paginate_query(query)
    return jsonify({"data": [m.to_dict() for m in items], **meta})


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
