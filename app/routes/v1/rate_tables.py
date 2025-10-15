from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required

from ...models import RateTable
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.route("/rate-tables", methods=["GET"])
@login_required
def rate_tables_page():
    """Render the rate tables page"""
    return render_template("rate-tables/rate-table.html")


@api_v1.route("/rate-tables/builder", methods=["GET"])
@login_required
def rate_table_builder_page():
    """Render the rate table builder page"""
    return render_template("rate-tables/rate-table-builder.html")


@api_v1.get("/api/rate-tables")
@login_required
def list_rate_tables():
    utility_type = request.args.get("utility_type")
    is_active = request.args.get("is_active")
    is_active_bool = None
    if is_active is not None:
        is_active_bool = is_active.lower() in ("1", "true", "yes")
    query = RateTable.list_filtered(utility_type=utility_type, is_active=is_active_bool)
    items, meta = paginate_query(query)
    return jsonify({"data": [r.to_dict() for r in items], **meta})


@api_v1.get("/api/rate-tables/<int:rate_table_id>")
@login_required
def get_rate_table(rate_table_id: int):
    rt = RateTable.get_by_id(rate_table_id)
    if not rt:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": rt.to_dict()})
