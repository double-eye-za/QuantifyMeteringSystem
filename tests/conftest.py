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
from app.models import User


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
        # create a default user
        user = User(
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password_hash="",
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
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )
