"""
Service layer for Device Type management
"""
from app.models import DeviceType
from app.db import db


def list_device_types(active_only=True):
    """Get all device types"""
    query = DeviceType.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(DeviceType.name).all()


def get_device_type_by_id(device_type_id):
    """Get a specific device type by ID"""
    return DeviceType.query.get(device_type_id)


def get_device_type_by_code(code):
    """Get a specific device type by code"""
    return DeviceType.query.filter_by(code=code).first()


def create_device_type(payload):
    """Create a new device type"""
    device_type = DeviceType(
        code=payload.get("code"),
        name=payload.get("name"),
        description=payload.get("description"),
        manufacturer=payload.get("manufacturer"),
        default_model=payload.get("default_model"),
        supports_temperature=payload.get("supports_temperature", False),
        supports_pulse=payload.get("supports_pulse", False),
        supports_modbus=payload.get("supports_modbus", False),
        is_active=payload.get("is_active", True),
    )
    db.session.add(device_type)
    db.session.commit()
    return device_type


def update_device_type(device_type_id, payload):
    """Update an existing device type"""
    device_type = get_device_type_by_id(device_type_id)
    if not device_type:
        return None

    if "code" in payload:
        device_type.code = payload["code"]
    if "name" in payload:
        device_type.name = payload["name"]
    if "description" in payload:
        device_type.description = payload["description"]
    if "manufacturer" in payload:
        device_type.manufacturer = payload["manufacturer"]
    if "default_model" in payload:
        device_type.default_model = payload["default_model"]
    if "supports_temperature" in payload:
        device_type.supports_temperature = payload["supports_temperature"]
    if "supports_pulse" in payload:
        device_type.supports_pulse = payload["supports_pulse"]
    if "supports_modbus" in payload:
        device_type.supports_modbus = payload["supports_modbus"]
    if "is_active" in payload:
        device_type.is_active = payload["is_active"]

    db.session.commit()
    return device_type


def delete_device_type(device_type_id):
    """Soft delete a device type by setting is_active to False"""
    device_type = get_device_type_by_id(device_type_id)
    if not device_type:
        return False

    device_type.is_active = False
    db.session.commit()
    return True
