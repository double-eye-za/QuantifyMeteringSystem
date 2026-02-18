from __future__ import annotations

import os
import tempfile
import pytest

import sys
from pathlib import Path

# Ensure project root is on sys.path so `application` is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from application import create_app
from app.db import db
from app.models import User, Role
from scripts.seed import ensure_roles_and_super_admin


@pytest.fixture(scope="session")
def app():
    # Use sqlite for tests to avoid needing Postgres
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"check_same_thread": False}},
            "SERVER_NAME": "localhost",
            "PRESERVE_CONTEXT_ON_EXCEPTION": False,
            "SECRET_KEY": "test-secret",
            "LOGIN_DISABLED": False,
        }
    )
    with app.app_context():
        db.create_all()

        # Create roles and super admin user
        ensure_roles_and_super_admin()

        # Get the super admin user that was created (username: takudzwa)
        user = User.query.filter_by(username="takudzwa").first()
        if not user:
            # Fallback: create admin user manually
            admin_role = Role.query.filter_by(name="Super Administrator").first()
            user = User(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                password_hash="",
                role=admin_role,
                is_super_admin=True,
            )
            from app.auth import set_password

            set_password(user, "password")
            db.session.add(user)
            db.session.commit()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client):
    return client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
