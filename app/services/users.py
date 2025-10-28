from __future__ import annotations

from typing import Optional, Tuple, List

from app.db import db
from app.models.user import User
from app.models.role import Role


def list_users(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    role_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 25,
):
    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(like),
                User.email.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
            )
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if role_id is not None:
        query = query.filter(User.role_id == role_id)

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return users, total


def get_user_by_id(user_id: int):
    return User.query.get(user_id)


def create_user(**data):
    user = User(
        username=data["username"],
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone"),
        is_active=data.get("is_active", True),
        role_id=data.get("role_id"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user_id: int, payload: dict):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    for f in [
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
        "role_id",
        "is_active",
    ]:
        if f in payload and payload[f] is not None:
            setattr(user, f, payload[f])
    if payload.get("password"):
        user.set_password(payload["password"])
    db.session.commit()


def delete_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        return
    if user.is_super_admin:
        raise ValueError("Cannot delete super administrator users")
    db.session.delete(user)
    db.session.commit()


def set_active_status(user_id: int, active: bool):
    user = User.query.get(user_id)
    if not user:
        return
    user.is_active = active
    db.session.commit()


def list_roles_for_dropdown():
    return [
        {"id": r.id, "name": r.name} for r in Role.query.order_by(Role.name.asc()).all()
    ]


def update_profile(user: User, payload: dict):
    if not user or not payload:
        return user
    for field in ("first_name", "last_name", "email", "phone"):
        if field in payload and payload[field] is not None:
            setattr(user, field, payload[field])
    db.session.commit()
    return user


def change_password(
    user: User, current_password: str, new_password: str, confirm_password: str
):
    if not current_password or not new_password or not confirm_password:
        return False, "All password fields are required"
    if new_password != confirm_password:
        return False, "New passwords do not match"
    if not user.check_password(current_password):
        return False, "Current password is incorrect"

    from app.utils.password import validate_password_policy

    is_valid, error_message = validate_password_policy(new_password)
    if not is_valid:
        return False, error_message

    user.set_password(new_password)
    db.session.commit()
    return True, None
