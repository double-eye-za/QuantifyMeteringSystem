from __future__ import annotations

from flask import jsonify, request
from flask_login import login_user, logout_user, login_required, current_user

from ...models import User
from ...db import db
from . import api_v1


@api_v1.post("/auth/login")
def login():
    payload = request.get_json(force=True) or {}
    username = payload.get("username") or payload.get("email")
    password = payload.get("password")
    if not username or not password:
        return jsonify({"error": "Invalid credentials", "code": 401}), 401

    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    if not user or not getattr(user, "check_password")(user, password):
        return jsonify({"error": "Invalid credentials", "code": 401}), 401

    login_user(user)
    return jsonify({"message": "Logged in", "data": {"user_id": user.id}})


@api_v1.post("/auth/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})


@api_v1.post("/auth/change-password")
@login_required
def change_password():
    payload = request.get_json(force=True) or {}
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    if not current_password or not new_password:
        return jsonify({"error": "Missing password fields", "code": 400}), 400

    if not getattr(current_user, "check_password")(current_user, current_password):
        return jsonify({"error": "Current password incorrect", "code": 400}), 400

    getattr(current_user, "set_password")(current_user, new_password)
    db.session.commit()
    return jsonify({"message": "Password changed"})
