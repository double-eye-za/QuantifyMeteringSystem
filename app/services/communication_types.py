"""
Service layer for Communication Type management
"""
from app.models import CommunicationType
from app.db import db


def list_communication_types(active_only=True):
    """Get all communication types"""
    query = CommunicationType.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(CommunicationType.name).all()


def get_communication_type_by_id(comm_type_id):
    """Get a specific communication type by ID"""
    return CommunicationType.query.get(comm_type_id)


def get_communication_type_by_code(code):
    """Get a specific communication type by code"""
    return CommunicationType.query.filter_by(code=code).first()


def create_communication_type(payload):
    """Create a new communication type"""
    comm_type = CommunicationType(
        code=payload.get("code"),
        name=payload.get("name"),
        description=payload.get("description"),
        requires_device_eui=payload.get("requires_device_eui", False),
        requires_gateway=payload.get("requires_gateway", False),
        supports_remote_control=payload.get("supports_remote_control", False),
        is_active=payload.get("is_active", True),
    )
    db.session.add(comm_type)
    db.session.commit()
    return comm_type


def update_communication_type(comm_type_id, payload):
    """Update an existing communication type"""
    comm_type = get_communication_type_by_id(comm_type_id)
    if not comm_type:
        return None

    if "code" in payload:
        comm_type.code = payload["code"]
    if "name" in payload:
        comm_type.name = payload["name"]
    if "description" in payload:
        comm_type.description = payload["description"]
    if "requires_device_eui" in payload:
        comm_type.requires_device_eui = payload["requires_device_eui"]
    if "requires_gateway" in payload:
        comm_type.requires_gateway = payload["requires_gateway"]
    if "supports_remote_control" in payload:
        comm_type.supports_remote_control = payload["supports_remote_control"]
    if "is_active" in payload:
        comm_type.is_active = payload["is_active"]

    db.session.commit()
    return comm_type


def delete_communication_type(comm_type_id):
    """Soft delete a communication type by setting is_active to False"""
    comm_type = get_communication_type_by_id(comm_type_id)
    if not comm_type:
        return False

    comm_type.is_active = False
    db.session.commit()
    return True
