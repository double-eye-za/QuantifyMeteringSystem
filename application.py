from __future__ import annotations

from flask import Flask

from config import Config
from app.db import db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
