from __future__ import annotations

from flask import render_template
from flask_login import login_required

from . import api_v1


@api_v1.route("/profile", methods=["GET"])
@login_required
def profile_page():
    return render_template("profile/profile.html")
