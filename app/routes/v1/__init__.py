from __future__ import annotations

from flask import Blueprint, jsonify, redirect, url_for, flash, request
from ...auth import login_manager


api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


from . import estates
from . import units
from . import meters
from . import wallets
from . import transactions
from . import rate_tables
from . import notifications
from . import reports
from . import system
from . import users
from . import roles
from . import audit_logs
from . import profile
from . import settings
from . import auth
from . import residents


@login_manager.unauthorized_handler
def _unauthorized():
    """Handle unauthorized access - redirect to login with flash message"""
    flash("Your session has expired. Please log in again to continue.", "warning")
    return redirect(url_for("api_v1.login_page"))


@api_v1.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 Unauthorized errors"""
    flash("Your session has expired. Please log in again to continue.", "warning")
    return redirect(url_for("api_v1.login_page"))


@api_v1.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 Forbidden errors"""
    flash("You don't have permission to access this resource.", "error")
    return redirect(url_for("api_v1.dashboard"))
