from __future__ import annotations

from flask import render_template
from flask_login import login_required

from . import api_v1


@api_v1.route("/roles", methods=["GET"])
@login_required
def roles_page():
    return render_template("roles&permissions/roles.html")
