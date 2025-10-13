# Import models so they are registered with SQLAlchemy metadata on app init
from .user import User  # noqa: F401
from .role import Role  # noqa: F401
from .estate import Estate  # noqa: F401
from .resident import Resident  # noqa: F401
from .meter import Meter  # noqa: F401
from .unit import Unit  # noqa: F401
from .meter_reading import MeterReading  # noqa: F401
from .wallet import Wallet  # noqa: F401
from .transaction import Transaction  # noqa: F401
from .payment_method import PaymentMethod  # noqa: F401
from .rate_table import RateTable  # noqa: F401
from .rate_table_tier import RateTableTier  # noqa: F401
from .time_of_use_rate import TimeOfUseRate  # noqa: F401
from .notification import Notification  # noqa: F401
from .audit_log import AuditLog  # noqa: F401
from .system_setting import SystemSetting  # noqa: F401
from .meter_alert import MeterAlert  # noqa: F401
from .reconciliation_report import ReconciliationReport  # noqa: F401

__all__ = [
    "User",
    "Role",
    "Estate",
    "Resident",
    "Meter",
    "Unit",
    "MeterReading",
    "Wallet",
    "Transaction",
    "PaymentMethod",
    "RateTable",
    "RateTableTier",
    "TimeOfUseRate",
    "Notification",
    "AuditLog",
    "SystemSetting",
    "MeterAlert",
    "ReconciliationReport",
]
