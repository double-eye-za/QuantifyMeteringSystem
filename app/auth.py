from __future__ import annotations

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from .db import db
from .models import User, MobileUser


login_manager = LoginManager()
login_manager.login_view = None
login_manager.login_message = None


@login_manager.user_loader
def load_user(user_id: str):
    """Load a user by session ID.

    Supports two user types:
      - Admin users: user_id is a plain integer string (e.g. "5")
      - Portal users: user_id is prefixed with "mobile:" (e.g. "mobile:12")

    The prefix is set by MobileUser.get_id() and ensures no collision
    between the users and mobile_users tables.
    """
    try:
        if user_id.startswith('mobile:'):
            mobile_id = int(user_id.split(':', 1)[1])
            return MobileUser.query.get(mobile_id)
        return User.query.get(int(user_id))
    except Exception:
        return None


def set_password(user: User, password: str) -> None:
    user.password_hash = generate_password_hash(password)


def check_password(user: User, password: str) -> bool:
    return check_password_hash(user.password_hash or "", password)


User.set_password = set_password
User.check_password = check_password
