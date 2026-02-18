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
# from . import residents  # DEPRECATED - Removed in favor of Person model
from . import persons
from . import unit_ownerships
from . import unit_tenancies
from . import device_types
from . import communication_types
from . import tickets
from . import messages
from . import invites
from . import lorawan


@login_manager.unauthorized_handler
def _unauthorized():
    """Handle unauthorized access - redirect to login with flash message"""
    flash("Your session has expired. Please log in again to continue.", "warning")
    return redirect(url_for("api_v1.login_page"))


@api_v1.before_request
def _block_portal_users():
    """Prevent portal (mobile) users from accessing admin routes.

    Portal users who somehow navigate to /api/v1/* pages are redirected
    to the portal dashboard. Login/logout routes are excluded so the
    unified login and logout flow still works for both user types.
    """
    from flask_login import current_user

    if not current_user.is_authenticated:
        return  # Let @login_required handle unauthenticated users

    if str(current_user.get_id()).startswith('mobile:'):
        # Allow portal users to use the shared login/logout routes
        allowed_endpoints = {
            'api_v1.login_page', 'api_v1.login', 'api_v1.logout',
        }
        if request.endpoint not in allowed_endpoints:
            flash("Please use the portal to access your account.", "info")
            return redirect(url_for("portal.portal_dashboard"))


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
