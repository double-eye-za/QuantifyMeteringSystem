from __future__ import annotations
from flask import Flask
from config import Config
from app.db import db
from app.routes.v1 import api_v1
from app.auth import login_manager
import os
from flask_migrate import Migrate
from datetime import timedelta


def create_app() -> Flask:
    app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
    app.config.from_object(Config)
    # Allow runtime override of DB via env for tests

    env_db = os.getenv("DATABASE_URL")
    if env_db:
        app.config["SQLALCHEMY_DATABASE_URI"] = env_db

    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)

    with app.app_context():
        # Import models so tables are registered
        from app.models import (  # noqa: F401
            User,
            Role,
            Estate,
            Resident,
            Meter,
            Unit,
            MeterReading,
            Wallet,
            Transaction,
            PaymentMethod,
            RateTable,
            RateTableTier,
            TimeOfUseRate,
            Notification,
            AuditLog,
            SystemSetting,
            MeterAlert,
            ReconciliationReport,
        )

        # Register API blueprints
        app.register_blueprint(api_v1)

        # Configure session timeout from settings
        configure_session_timeout(app)

    return app


def configure_session_timeout(app: Flask):
    """Configure session timeout based on system settings with default fallback"""
    try:
        from app.models import SystemSetting

        # Get session timeout setting in minutes
        session_timeout_setting = SystemSetting.query.filter_by(
            setting_key="session_timeout"
        ).first()

        if session_timeout_setting and session_timeout_setting.setting_value:
            timeout_minutes = float(session_timeout_setting.setting_value)
            timeout_seconds = timeout_minutes * 60
            app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
                seconds=timeout_seconds
            )
            print(f"Session timeout configured: {timeout_minutes} minutes")
        else:
            # Use default 15 minutes if no setting found
            app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
            print("Using default session timeout: 15 minutes")

    except Exception as e:
        
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
        print(f"Warning: Could not load session timeout setting, using default: {e}")


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
