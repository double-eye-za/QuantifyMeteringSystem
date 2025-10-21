from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort
from flask_login import current_user


def requires_permission(permission_code: str):
    """Decorator to require a specific permission for a route."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = current_user
            if not getattr(user, "is_authenticated", False):
                abort(401)
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
                abort(403)
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
