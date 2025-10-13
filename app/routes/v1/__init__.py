from __future__ import annotations

from flask import Blueprint


api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Import submodules to register routes
from . import estates  # noqa: F401
from . import units  # noqa: F401
from . import meters  # noqa: F401
from . import wallets  # noqa: F401
from . import transactions  # noqa: F401
from . import rate_tables  # noqa: F401
from . import notifications  # noqa: F401
from . import reports  # noqa: F401
from . import system  # noqa: F401
from . import auth  # noqa: F401
