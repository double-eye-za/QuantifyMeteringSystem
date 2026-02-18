"""Portal-specific decorators for owner/tenant web portal routes."""
from __future__ import annotations

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required


def is_portal_user() -> bool:
    """Check if the currently authenticated user is a portal (mobile) user.

    Portal users have a session ID prefixed with 'mobile:' which is set
    by MobileUser.get_id(). Admin users return a plain integer string.
    """
    if not current_user.is_authenticated:
        return False
    return str(current_user.get_id()).startswith('mobile:')


def is_admin_user() -> bool:
    """Check if the currently authenticated user is an admin (staff) user."""
    if not current_user.is_authenticated:
        return False
    return not str(current_user.get_id()).startswith('mobile:')


def portal_login_required(f):
    """Decorator that requires the user to be logged in AND be a portal user.

    If the user is not logged in, they are redirected to the login page.
    If the user is logged in but is an admin user, they are redirected
    to the admin dashboard (they shouldn't be on portal pages).
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not is_portal_user():
            flash("This page is only accessible to residents.", "warning")
            return redirect(url_for("api_v1.dashboard"))
        return f(*args, **kwargs)
    return decorated_function
