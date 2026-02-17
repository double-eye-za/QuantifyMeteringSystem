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

    # ChirpStack API configuration (for LoRaWAN device control)
    CHIRPSTACK_API_URL = os.getenv("CHIRPSTACK_API_URL", "http://localhost:8080")
    CHIRPSTACK_API_KEY = os.getenv("CHIRPSTACK_API_KEY", "")
    CHIRPSTACK_TENANT_ID = os.getenv("CHIRPSTACK_TENANT_ID", "")
    CHIRPSTACK_PASSTHROUGH_PORT = int(os.getenv("CHIRPSTACK_PASSTHROUGH_PORT", "5"))

    # PayFast payment gateway configuration
    PAYFAST_MERCHANT_ID = os.getenv("PAYFAST_MERCHANT_ID", "10000100")
    PAYFAST_MERCHANT_KEY = os.getenv("PAYFAST_MERCHANT_KEY", "46f0cd694581a")
    PAYFAST_PASSPHRASE = os.getenv("PAYFAST_PASSPHRASE", "jt7NOE43FZPn")
    PAYFAST_SANDBOX = os.getenv("PAYFAST_SANDBOX", "true").lower() in ("true", "1", "yes")
    PAYFAST_PROCESS_URL = os.getenv(
        "PAYFAST_PROCESS_URL",
        "https://sandbox.payfast.co.za/eng/process",
    )
    PAYFAST_VALIDATE_URL = os.getenv(
        "PAYFAST_VALIDATE_URL",
        "https://sandbox.payfast.co.za/eng/query/validate",
    )

    # Email / Flask-Mail configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@quantifymetering.com")
