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
from .models import User


login_manager = LoginManager()
login_manager.login_view = None
login_manager.login_message = None


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


def set_password(user: User, password: str) -> None:
    user.password_hash = generate_password_hash(password)


def check_password(user: User, password: str) -> bool:
    return check_password_hash(user.password_hash or "", password)


User.set_password = set_password
User.check_password = check_password
