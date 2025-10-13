from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from . import api_v1


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
