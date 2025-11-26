from __future__ import annotations
from flask import Flask, render_template
from config import Config
from app.db import db
from app.routes.v1 import api_v1
from app.auth import login_manager
import os
from flask_migrate import Migrate
from datetime import timedelta
from flask_login import current_user
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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

    @app.template_global()
    def has_permission(permission_code: str):
        """Check if current user has a specific permission."""
        user = current_user
        if not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_super_admin", False):
            return True
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
        return bool(allowed)

    @app.template_global()
    def is_super_admin():
        """Check if current user is a super admin."""
        user = current_user
        return getattr(user, "is_authenticated", False) and getattr(
            user, "is_super_admin", False
        )

    @app.template_filter("format_number")
    def format_number(value, decimals=0):
        """Format number with thousand separators (commas)"""
        if value is None:
            return "0"

        try:
            num = float(value)

            # Round to specified decimal places
            if decimals > 0:
                num = round(num, decimals)
                return f"{num:,.{decimals}f}"
            else:
                return f"{int(round(num)):,}"
        except (ValueError, TypeError):
            return "0"

    with app.app_context():
        from app.models import (
            User,
            Role,
            Estate,
            Person,
            UnitOwnership,
            UnitTenancy,
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

        # Register home page route
        @app.route('/')
        def home():
            """Landing page - redirect to login or dashboard"""
            from flask_login import current_user
            from flask import redirect, url_for, render_template

            # If user is already logged in, go to dashboard
            if current_user.is_authenticated:
                return redirect(url_for('api_v1.dashboard'))

            # Otherwise show welcome page with login button
            return render_template('home.html')

        # Register API blueprints
        app.register_blueprint(api_v1)

        # Register mobile API blueprint
        from app.routes.mobile import mobile_api
        app.register_blueprint(mobile_api)

        # Configure session timeout from settings
        configure_session_timeout(app)

        # Register error handlers
        register_error_handlers(app)

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


def register_error_handlers(app: Flask):
    """Register custom error handlers for better user experience"""

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors with custom template"""
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors"""
        return render_template("errors/403.html"), 403


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', debug=False, port=5000)
