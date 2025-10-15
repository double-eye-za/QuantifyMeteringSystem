from __future__ import annotations

from flask import render_template
from flask_login import login_required

from . import api_v1


@api_v1.route("/audit-logs", methods=["GET"])
@login_required
def audit_logs_page():
    return render_template("audit-logs/audit-logs.html")
