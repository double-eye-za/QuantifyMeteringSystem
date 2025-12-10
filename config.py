import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://localhost/quantify",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration with default timeout
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Celery configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "Africa/Johannesburg")
    CELERY_ENABLE_UTC = True

    # SMS configuration (Clickatell)
    CLICKATELL_API_KEY = os.getenv("CLICKATELL_API_KEY", "")
