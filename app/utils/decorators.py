from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort, request, jsonify, redirect, url_for, flash
from flask_login import current_user


def get_user_estate_filter(user=None):
    """Return estate_id to filter by, or None for unrestricted access.

    Super admins and users without an estate assignment see everything.
    Estate-scoped users are restricted to their assigned estate.
    """
    user = user or current_user
    if getattr(user, "is_super_admin", False):
        return None
    return getattr(user, "estate_id", None)


def get_allowed_estates(user=None):
    """Return estates the user can access — all for super_admin, one for estate managers."""
    from ..models.estate import Estate

    user = user or current_user
    if getattr(user, "is_super_admin", False) or not getattr(user, "estate_id", None):
        return Estate.query.filter_by(is_active=True).order_by(Estate.name).all()
    return Estate.query.filter_by(id=user.estate_id, is_active=True).all()


def requires_permission(permission_code: str):
    """Decorator to require a specific permission for a route."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = current_user
            if not getattr(user, "is_authenticated", False):
                if (
                    request.headers.get("X-Requested-With") == "XMLHttpRequest"
                    or request.is_json
                ):
                    return jsonify(
                        {
                            "error": "Session expired. Please log in again.",
                            "code": 401,
                            "redirect": url_for("api_v1.login_page"),
                        }
                    ), 401
                else:
                    flash(
                        "Your session has expired. Please log in again to continue.",
                        "warning",
                    )
                    return redirect(url_for("api_v1.login_page"))

            if getattr(user, "is_super_admin", False):
                return view_func(*args, **kwargs)
            role = getattr(user, "role", None)
            permission_set = getattr(role, "permission", None)
            permissions_json = getattr(permission_set, "permissions", {}) or {}

            # Check if user has the required permission
            allowed = permissions_json
            for key in permission_code.split("."):
                if isinstance(allowed, dict) and key in allowed:
                    allowed = allowed[key]
                else:
                    allowed = False
                    break
            if not bool(allowed):
                if (
                    request.headers.get("X-Requested-With") == "XMLHttpRequest"
                    or request.is_json
                ):
                    return jsonify(
                        {
                            "error": "You don't have permission to access this resource.",
                            "code": 403,
                        }
                    ), 403
                else:
                    flash("You don't have permission to access this resource.", "error")
                    return redirect(url_for("api_v1.dashboard"))
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
