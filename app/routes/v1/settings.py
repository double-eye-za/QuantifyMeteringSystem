from __future__ import annotations

from flask import render_template
from flask_login import login_required

from . import api_v1


@api_v1.route("/settings", methods=["GET"])
@login_required
def settings_page():
    return render_template("settings/settings.html")
