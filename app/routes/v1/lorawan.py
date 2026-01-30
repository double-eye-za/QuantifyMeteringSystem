"""
LoRaWAN management routes for ChirpStack integration.

This module provides API endpoints for managing:
- LoRaWAN devices (create, list, get, delete)
- LoRaWAN gateways (create, list, get, delete)
- Device profiles and applications (list)
"""
from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required

from ...services import chirpstack_service
from ...utils.decorators import requires_permission
from ...utils.audit import log_action
from . import api_v1


# =============================================================================
# LORAWAN MANAGEMENT PAGE
# =============================================================================

@api_v1.route("/lorawan", methods=["GET"])
@login_required
@requires_permission("meters.view")
def lorawan_page():
    """Render the LoRaWAN management page."""
    return render_template("lorawan/index.html")


@api_v1.route("/lorawan/gateways", methods=["GET"])
@login_required
@requires_permission("meters.view")
def lorawan_gateways_page():
    """Render the LoRaWAN gateways management page."""
    return render_template("lorawan/gateways.html")


@api_v1.route("/lorawan/devices", methods=["GET"])
@login_required
@requires_permission("meters.view")
def lorawan_devices_page():
    """Render the LoRaWAN devices management page."""
    return render_template("lorawan/devices.html")


@api_v1.route("/lorawan/applications", methods=["GET"])
@login_required
@requires_permission("meters.view")
def lorawan_applications_page():
    """Render the LoRaWAN applications management page."""
    return render_template("lorawan/applications.html")


# =============================================================================
# CONNECTION TEST
# =============================================================================

@api_v1.route("/api/lorawan/test-connection", methods=["GET"])
@login_required
@requires_permission("meters.view")
def test_chirpstack_connection():
    """Test the connection to ChirpStack API."""
    success, message = chirpstack_service.test_connection()

    return jsonify({
        "success": success,
        "message": message,
    }), 200 if success else 500


# =============================================================================
# APPLICATIONS
# =============================================================================

@api_v1.route("/api/lorawan/applications", methods=["GET"])
@login_required
@requires_permission("meters.view")
def list_applications():
    """List all applications in ChirpStack."""
    success, result = chirpstack_service.list_applications()

    if success:
        return jsonify({
            "success": True,
            "applications": result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 500


@api_v1.route("/api/lorawan/applications", methods=["POST"])
@login_required
@requires_permission("meters.manage")
def create_application():
    """Create a new application in ChirpStack."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    name = data.get("name")
    if not name:
        return jsonify({"success": False, "error": "Application name is required"}), 400

    description = data.get("description", "")

    success, result = chirpstack_service.create_application(
        name=name,
        description=description,
    )

    if success:
        return jsonify({
            "success": True,
            "message": "Application created successfully",
            "application": result,
        }), 201

    return jsonify({
        "success": False,
        "error": result,
    }), 500


@api_v1.route("/api/lorawan/applications/<application_id>", methods=["PUT"])
@login_required
@requires_permission("meters.manage")
def update_application(application_id):
    """Update an existing application in ChirpStack."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    name = data.get("name")
    if not name:
        return jsonify({"success": False, "error": "Application name is required"}), 400

    description = data.get("description", "")

    success, result = chirpstack_service.update_application(
        application_id=application_id,
        name=name,
        description=description,
    )

    if success:
        return jsonify({
            "success": True,
            "message": "Application updated successfully",
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 500


@api_v1.route("/api/lorawan/applications/<application_id>", methods=["DELETE"])
@login_required
@requires_permission("meters.manage")
def delete_application(application_id):
    """Delete an application from ChirpStack."""
    success, result = chirpstack_service.delete_application(application_id)

    if success:
        return jsonify({
            "success": True,
            "message": result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 500


# =============================================================================
# DEVICE PROFILES
# =============================================================================

@api_v1.route("/api/lorawan/device-profiles", methods=["GET"])
@login_required
@requires_permission("meters.view")
def list_device_profiles():
    """List all device profiles in ChirpStack."""
    success, result = chirpstack_service.list_device_profiles()

    if success:
        return jsonify({
            "success": True,
            "deviceProfiles": result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 500


# =============================================================================
# TENANTS
# =============================================================================

@api_v1.route("/api/lorawan/tenants", methods=["GET"])
@login_required
@requires_permission("meters.view")
def list_tenants():
    """List all tenants in ChirpStack."""
    success, result = chirpstack_service.list_tenants()

    if success:
        return jsonify({
            "success": True,
            "tenants": result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 500


# =============================================================================
# DEVICES
# =============================================================================

@api_v1.route("/api/lorawan/devices", methods=["GET"])
@login_required
@requires_permission("meters.view")
def list_lorawan_devices():
    """
    List all devices in ChirpStack.

    Query params:
        application_id: Filter by application (optional)
        limit: Max results (default 100)
        offset: Pagination offset (default 0)
    """
    application_id = request.args.get("application_id")
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    success, result = chirpstack_service.list_devices(
        application_id=application_id,
        limit=limit,
        offset=offset,
    )

    if success:
        return jsonify({
            "success": True,
            "devices": result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 500


@api_v1.route("/api/lorawan/devices/<device_eui>", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_lorawan_device(device_eui: str):
    """Get details of a specific device from ChirpStack."""
    success, result = chirpstack_service.get_device_with_status(device_eui)

    if success:
        return jsonify({
            "success": True,
            **result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 404 if "not found" in str(result).lower() else 500


@api_v1.route("/api/lorawan/devices", methods=["POST"])
@login_required
@requires_permission("meters.create")
def create_lorawan_device():
    """
    Create a new device in ChirpStack.

    Expected JSON payload:
    {
        "device_eui": "0123456789abcdef",
        "name": "My Device",
        "application_id": "uuid-of-application",
        "device_profile_id": "uuid-of-device-profile",
        "description": "Optional description",
        "join_eui": "optional-join-eui",
        "app_key": "32-char-hex-key-for-otaa"
    }
    """
    data = request.get_json() or {}

    # Required fields
    required = ["device_eui", "name", "application_id", "device_profile_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}",
        }), 400

    # Validate device_eui format
    device_eui = data["device_eui"].lower().replace(":", "").replace("-", "")
    if len(device_eui) != 16 or not all(c in "0123456789abcdef" for c in device_eui):
        return jsonify({
            "success": False,
            "error": "Invalid device_eui format. Must be 16 hex characters.",
        }), 400

    # Create the device
    success, result = chirpstack_service.create_device(
        device_eui=device_eui,
        name=data["name"],
        application_id=data["application_id"],
        device_profile_id=data["device_profile_id"],
        description=data.get("description", ""),
        join_eui=data.get("join_eui"),
        skip_fcnt_check=data.get("skip_fcnt_check", False),
        is_disabled=data.get("is_disabled", False),
    )

    if not success:
        return jsonify({
            "success": False,
            "error": result,
        }), 400

    # Set OTAA keys if provided
    app_key = data.get("app_key")
    if app_key:
        app_key = app_key.lower().replace(":", "").replace("-", "")
        if len(app_key) != 32 or not all(c in "0123456789abcdef" for c in app_key):
            # Device created but keys failed - still return success with warning
            return jsonify({
                "success": True,
                "warning": "Device created but app_key format invalid. Set keys manually.",
                "device_eui": device_eui,
            }), 201

        keys_success, keys_result = chirpstack_service.set_device_keys(
            device_eui=device_eui,
            app_key=app_key,
        )

        if not keys_success:
            return jsonify({
                "success": True,
                "warning": f"Device created but failed to set keys: {keys_result}",
                "device_eui": device_eui,
            }), 201

    # Log the action
    log_action(
        "lorawan.device.create",
        entity_type="lorawan_device",
        entity_id=device_eui,
        new_values={
            "device_eui": device_eui,
            "name": data["name"],
            "application_id": data["application_id"],
        },
    )

    return jsonify({
        "success": True,
        "message": "Device created successfully",
        "device_eui": device_eui,
    }), 201


@api_v1.route("/api/lorawan/devices/<device_eui>", methods=["PUT"])
@login_required
@requires_permission("meters.edit")
def update_lorawan_device(device_eui: str):
    """
    Update an existing device in ChirpStack.

    Expected JSON payload (all fields optional):
    {
        "name": "New Name",
        "description": "New description",
        "is_disabled": false
    }
    """
    data = request.get_json() or {}

    success, result = chirpstack_service.update_device(
        device_eui=device_eui,
        name=data.get("name"),
        description=data.get("description"),
        is_disabled=data.get("is_disabled"),
        skip_fcnt_check=data.get("skip_fcnt_check"),
    )

    if success:
        log_action(
            "lorawan.device.update",
            entity_type="lorawan_device",
            entity_id=device_eui,
            new_values=data,
        )

        return jsonify({
            "success": True,
            "message": "Device updated successfully",
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 400


@api_v1.route("/api/lorawan/devices/<device_eui>", methods=["DELETE"])
@login_required
@requires_permission("meters.delete")
def delete_lorawan_device(device_eui: str):
    """Delete a device from ChirpStack."""
    success, result = chirpstack_service.delete_device(device_eui)

    if success:
        log_action(
            "lorawan.device.delete",
            entity_type="lorawan_device",
            entity_id=device_eui,
        )

        return jsonify({
            "success": True,
            "message": "Device deleted successfully",
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 400


@api_v1.route("/api/lorawan/devices/<device_eui>/keys", methods=["POST"])
@login_required
@requires_permission("meters.edit")
def set_lorawan_device_keys(device_eui: str):
    """
    Set OTAA keys for a device.

    Expected JSON payload:
    {
        "app_key": "32-character-hex-key"
    }
    """
    data = request.get_json() or {}

    app_key = data.get("app_key", "").lower().replace(":", "").replace("-", "")
    if len(app_key) != 32 or not all(c in "0123456789abcdef" for c in app_key):
        return jsonify({
            "success": False,
            "error": "Invalid app_key format. Must be 32 hex characters.",
        }), 400

    success, result = chirpstack_service.set_device_keys(
        device_eui=device_eui,
        app_key=app_key,
    )

    if success:
        log_action(
            "lorawan.device.set_keys",
            entity_type="lorawan_device",
            entity_id=device_eui,
        )

        return jsonify({
            "success": True,
            "message": "Device keys set successfully",
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 400


# =============================================================================
# GATEWAYS
# =============================================================================

@api_v1.route("/api/lorawan/gateways", methods=["GET"])
@login_required
@requires_permission("meters.view")
def list_lorawan_gateways():
    """
    List all gateways in ChirpStack.

    Query params:
        tenant_id: Filter by tenant (optional)
        limit: Max results (default 100)
        offset: Pagination offset (default 0)
    """
    tenant_id = request.args.get("tenant_id")
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    success, result = chirpstack_service.list_gateways(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )

    if success:
        return jsonify({
            "success": True,
            "gateways": result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 500


@api_v1.route("/api/lorawan/gateways/<gateway_id>", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_lorawan_gateway(gateway_id: str):
    """Get details of a specific gateway from ChirpStack."""
    success, result = chirpstack_service.get_gateway(gateway_id)

    if success:
        return jsonify({
            "success": True,
            **result,
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 404 if "not found" in str(result).lower() else 500


@api_v1.route("/api/lorawan/gateways", methods=["POST"])
@login_required
@requires_permission("meters.create")
def create_lorawan_gateway():
    """
    Create a new gateway in ChirpStack.

    Expected JSON payload:
    {
        "gateway_id": "0123456789abcdef",
        "name": "My Gateway",
        "tenant_id": "uuid-of-tenant",
        "description": "Optional description",
        "latitude": -26.2041,
        "longitude": 28.0473,
        "altitude": 1500
    }
    """
    data = request.get_json() or {}

    # Required fields
    required = ["gateway_id", "name", "tenant_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}",
        }), 400

    # Validate gateway_id format
    gateway_id = data["gateway_id"].lower().replace(":", "").replace("-", "")
    if len(gateway_id) != 16 or not all(c in "0123456789abcdef" for c in gateway_id):
        return jsonify({
            "success": False,
            "error": "Invalid gateway_id format. Must be 16 hex characters.",
        }), 400

    # Create the gateway
    success, result = chirpstack_service.create_gateway(
        gateway_id=gateway_id,
        name=data["name"],
        tenant_id=data["tenant_id"],
        description=data.get("description", ""),
        location_latitude=data.get("latitude"),
        location_longitude=data.get("longitude"),
        location_altitude=data.get("altitude"),
    )

    if not success:
        return jsonify({
            "success": False,
            "error": result,
        }), 400

    # Log the action
    log_action(
        "lorawan.gateway.create",
        entity_type="lorawan_gateway",
        entity_id=gateway_id,
        new_values={
            "gateway_id": gateway_id,
            "name": data["name"],
            "tenant_id": data["tenant_id"],
        },
    )

    return jsonify({
        "success": True,
        "message": "Gateway created successfully",
        "gateway_id": gateway_id,
    }), 201


@api_v1.route("/api/lorawan/gateways/<gateway_id>", methods=["PUT"])
@login_required
@requires_permission("meters.edit")
def update_lorawan_gateway(gateway_id: str):
    """
    Update an existing gateway in ChirpStack.

    Expected JSON payload (all fields optional):
    {
        "name": "New Name",
        "description": "New description",
        "latitude": -26.2041,
        "longitude": 28.0473,
        "altitude": 1500
    }
    """
    data = request.get_json() or {}

    success, result = chirpstack_service.update_gateway(
        gateway_id=gateway_id,
        name=data.get("name"),
        description=data.get("description"),
        location_latitude=data.get("latitude"),
        location_longitude=data.get("longitude"),
        location_altitude=data.get("altitude"),
    )

    if success:
        log_action(
            "lorawan.gateway.update",
            entity_type="lorawan_gateway",
            entity_id=gateway_id,
            new_values=data,
        )

        return jsonify({
            "success": True,
            "message": "Gateway updated successfully",
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 400


@api_v1.route("/api/lorawan/gateways/<gateway_id>", methods=["DELETE"])
@login_required
@requires_permission("meters.delete")
def delete_lorawan_gateway(gateway_id: str):
    """Delete a gateway from ChirpStack."""
    success, result = chirpstack_service.delete_gateway(gateway_id)

    if success:
        log_action(
            "lorawan.gateway.delete",
            entity_type="lorawan_gateway",
            entity_id=gateway_id,
        )

        return jsonify({
            "success": True,
            "message": "Gateway deleted successfully",
        }), 200

    return jsonify({
        "success": False,
        "error": result,
    }), 400
