from __future__ import annotations
from flask import Flask
from config import Config
from app.db import db
from app.routes.v1 import api_v1
from app.auth import login_manager
import os
from flask_migrate import Migrate


def create_app() -> Flask:
    app = Flask(__name__)
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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
