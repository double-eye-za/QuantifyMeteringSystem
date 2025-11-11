"""
Seed script for Device Types and Communication Types
Run this to populate the database with initial reference data
"""
import sys
import os

# Add parent directory to path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import db
from app.models import DeviceType, CommunicationType
from application import create_app


def seed_device_types():
    """Create initial device types"""
    device_types_data = [
        {
            "code": "milesight_em300",
            "name": "Milesight EM300-DI (Pulse Counter)",
            "description": "LoRaWAN pulse counter for electricity and water meters",
            "manufacturer": "Milesight",
            "default_model": "EM300-DI",
            "supports_temperature": True,
            "supports_pulse": True,
            "supports_modbus": False,
            "is_active": True,
        },
        {
            "code": "qalcosonic_w1",
            "name": "Qalcosonic W1 (Water Meter)",
            "description": "LoRaWAN ultrasonic water meter",
            "manufacturer": "Qalcosonic",
            "default_model": "W1",
            "supports_temperature": False,
            "supports_pulse": False,
            "supports_modbus": True,
            "is_active": True,
        },
        {
            "code": "kamstrup_multical",
            "name": "Kamstrup Multical (Heat/Water Meter)",
            "description": "4G/NB-IoT heat and water meter",
            "manufacturer": "Kamstrup",
            "default_model": "Multical 21",
            "supports_temperature": True,
            "supports_pulse": False,
            "supports_modbus": True,
            "is_active": True,
        },
        {
            "code": "fengbo_water",
            "name": "Fengbo 4G Water Meter",
            "description": "4G/NB-IoT water meter with remote shutoff",
            "manufacturer": "Fengbo",
            "default_model": "FB-4G",
            "supports_temperature": False,
            "supports_pulse": False,
            "supports_modbus": False,
            "is_active": True,
        },
    ]

    print("Seeding device types...")
    for data in device_types_data:
        existing = DeviceType.query.filter_by(code=data["code"]).first()
        if existing:
            print(f"  ⚠ Device type '{data['code']}' already exists, skipping")
            continue

        device_type = DeviceType(**data)
        db.session.add(device_type)
        print(f"  ✓ Created device type: {data['name']}")

    db.session.commit()
    print(f"Device types seeded successfully!\n")


def seed_communication_types():
    """Create initial communication types"""
    communication_types_data = [
        {
            "code": "lora",
            "name": "LoRaWAN",
            "description": "LoRaWAN communication via gateway",
            "requires_device_eui": True,
            "requires_gateway": True,
            "supports_remote_control": True,
            "is_active": True,
        },
        {
            "code": "cellular",
            "name": "4G/NB-IoT (Cellular)",
            "description": "Direct cellular communication (4G, NB-IoT, LTE-M)",
            "requires_device_eui": True,
            "requires_gateway": False,
            "supports_remote_control": True,
            "is_active": True,
        },
        {
            "code": "plc",
            "name": "PLC (Power Line Communication)",
            "description": "Communication over power lines",
            "requires_device_eui": False,
            "requires_gateway": False,
            "supports_remote_control": True,
            "is_active": True,
        },
        {
            "code": "wifi",
            "name": "WiFi",
            "description": "WiFi-enabled smart meters",
            "requires_device_eui": False,
            "requires_gateway": False,
            "supports_remote_control": True,
            "is_active": True,
        },
        {
            "code": "manual",
            "name": "Manual Reading",
            "description": "Manual meter readings (no remote communication)",
            "requires_device_eui": False,
            "requires_gateway": False,
            "supports_remote_control": False,
            "is_active": True,
        },
        {
            "code": "modbus",
            "name": "Modbus RTU/TCP",
            "description": "Modbus protocol (RS485/Ethernet)",
            "requires_device_eui": False,
            "requires_gateway": False,
            "supports_remote_control": True,
            "is_active": True,
        },
    ]

    print("Seeding communication types...")
    for data in communication_types_data:
        existing = CommunicationType.query.filter_by(code=data["code"]).first()
        if existing:
            print(f"  ⚠ Communication type '{data['code']}' already exists, skipping")
            continue

        comm_type = CommunicationType(**data)
        db.session.add(comm_type)
        print(f"  ✓ Created communication type: {data['name']}")

    db.session.commit()
    print(f"Communication types seeded successfully!\n")


def main():
    """Main seeding function"""
    app = create_app()

    with app.app_context():
        print("\n" + "=" * 60)
        print("DEVICE TYPES & COMMUNICATION TYPES SEEDING")
        print("=" * 60 + "\n")

        seed_device_types()
        seed_communication_types()

        print("=" * 60)
        print("✓ All reference data seeded successfully!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
