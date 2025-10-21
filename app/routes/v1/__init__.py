from __future__ import annotations

from flask import Blueprint, jsonify, redirect, url_for, flash, request
from ...auth import login_manager


api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Import submodules to register routes
from . import estates  # noqa: F401
from . import units  # noqa: F401
from . import meters  # noqa: F401
from . import wallets  # noqa: F401
from . import transactions  # noqa: F401
from . import rate_tables  # noqa: F401
from . import notifications  # noqa: F401
from . import reports  # noqa: F401
from . import system  # noqa: F401
from . import users  # noqa: F401
from . import roles  # noqa: F401
from . import audit_logs  # noqa: F401
from . import profile  # noqa: F401
from . import settings  # noqa: F401
from . import auth  # noqa: F401
from . import residents  # noqa: F401


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
