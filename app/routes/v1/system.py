from __future__ import annotations

from datetime import datetime
from flask import jsonify

from ...models import Meter
from . import api_v1


@api_v1.get("/system/health")
def system_health():
    # Simple health summary
    meters_online = Meter.query.filter(Meter.communication_status == "online").count()
    meters_offline = Meter.query.filter(Meter.communication_status == "offline").count()
    return jsonify(
        {
            "data": {
                "status": "healthy",
                "database": "connected",
                "meters_online": meters_online,
                "meters_offline": meters_offline,
                "api_version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }
    )
