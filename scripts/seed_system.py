"""
Minimal System Seeder
Creates only essential system data (roles, permissions, admin user)
Does NOT delete existing data or create demo data
Safe to run on production with real meter data
"""
import os
import sys
import logging

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from application import create_app
from app.db import db
from app.models import User, Role
from app.models.permissions import Permission
from app.services.permissions import create_permission

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ensure_roles_and_permissions():
    """Create system roles with permissions if they don't exist"""
    logging.info("Setting up roles and permissions...")

    # Define permissions for each role
    super_admin_permissions = {
        "estates": {"view": True, "create": True, "edit": True, "delete": True},
        "units": {"view": True, "create": True, "edit": True, "delete": True},
        "meters": {"view": True, "create": True, "edit": True, "delete": True},
        "residents": {"view": True, "create": True, "edit": True, "delete": True},
        "rate_tables": {"view": True, "create": True, "edit": True, "delete": True},
        "settings": {"view": True, "edit": True},
        "audit_logs": {"view": True},
        "wallets": {"view": True},
        "transactions": {"view": True},
        "notifications": {"view": True},
        "reports": {"view": True},
        "users": {
            "view": True,
            "create": True,
            "edit": True,
            "delete": True,
            "enable": True,
            "disable": True,
        },
        "roles": {"view": True, "create": True, "edit": True, "delete": True},
    }

    admin_permissions = {
        "estates": {"view": True, "create": True, "edit": True, "delete": True},
        "units": {"view": True, "create": True, "edit": True, "delete": True},
        "meters": {"view": True, "create": True, "edit": True, "delete": True},
        "residents": {"view": True, "create": True, "edit": True, "delete": True},
        "rate_tables": {"view": True, "create": True, "edit": True, "delete": True},
        "settings": {"view": False, "edit": False},
        "audit_logs": {"view": False},
        "wallets": {"view": True},
        "transactions": {"view": True},
        "notifications": {"view": True},
        "reports": {"view": True},
        "users": {
            "view": True,
            "create": True,
            "edit": True,
            "delete": False,
            "enable": True,
            "disable": True,
        },
        "roles": {"view": True, "create": False, "edit": False, "delete": False},
    }

    standard_permissions = {
        "estates": {"view": True, "create": False, "edit": False, "delete": False},
        "units": {"view": True, "create": False, "edit": False, "delete": False},
        "meters": {"view": True, "create": False, "edit": False, "delete": False},
        "residents": {"view": False, "create": False, "edit": False, "delete": False},
        "rate_tables": {"view": True, "create": False, "edit": False, "delete": False},
        "settings": {"view": False, "edit": False},
        "audit_logs": {"view": False},
        "wallets": {"view": True},
        "transactions": {"view": True},
        "notifications": {"view": True},
        "reports": {"view": False},
        "users": {"view": False, "create": False, "edit": False, "delete": False},
        "roles": {"view": False, "create": False, "edit": False, "delete": False},
    }

    def get_or_create_role(name: str, description: str, permissions_data: dict, is_system: bool = False):
        """Create role with permissions if it doesn't exist"""
        role = Role.query.filter_by(name=name).first()

        if role and role.permission_id:
            logging.info(f"  ✓ Role '{name}' already exists (ID: {role.id})")
            return role.id

        # Create or get permission
        perm_name = f"{name} Permissions"
        perm = Permission.query.filter_by(name=perm_name).first()

        if not perm:
            logging.info(f"  → Creating permissions for '{name}'...")
            perm = create_permission(
                name=perm_name,
                description=f"Permissions for {name}",
                permissions_data=permissions_data,
            )
            db.session.flush()

        # Create or update role
        if not role:
            logging.info(f"  → Creating role '{name}'...")
            role = Role(
                name=name,
                description=description,
                permission_id=perm.id,
                is_system_role=is_system,
            )
            db.session.add(role)
        else:
            role.permission_id = perm.id
            role.is_system_role = is_system

        db.session.commit()
        logging.info(f"  ✓ Role '{name}' ready (ID: {role.id})")
        return role.id

    # Create roles
    super_admin_role_id = get_or_create_role(
        "Super Administrator",
        "Full system access with all permissions",
        super_admin_permissions,
        is_system=True
    )

    admin_role_id = get_or_create_role(
        "Administrator",
        "Administrative access to manage estates, units, and meters",
        admin_permissions,
        is_system=False
    )

    standard_role_id = get_or_create_role(
        "Standard User",
        "View-only access to basic features",
        standard_permissions,
        is_system=False
    )

    logging.info("✓ Roles and permissions configured")
    return super_admin_role_id, admin_role_id, standard_role_id


def ensure_super_admin_user(super_admin_role_id: int):
    """Create or update super admin user"""
    logging.info("Setting up super admin user...")

    user = User.query.filter_by(email="admin@example.com").first()

    if not user:
        logging.info("  → Creating super admin user...")
        user = User(
            username="admin",
            email="admin@example.com",
            first_name="System",
            last_name="Administrator",
            is_active=True,
            is_super_admin=True,
            role_id=super_admin_role_id,
        )
        # Set password using the User model's method
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash("password")
        db.session.add(user)
        db.session.commit()
        logging.info(f"  ✓ Super admin created (ID: {user.id})")
        logging.info("  📧 Email: admin@example.com")
        logging.info("  🔑 Password: password")
    else:
        # Update existing user
        user.role_id = super_admin_role_id
        user.is_super_admin = True
        user.is_active = True
        db.session.commit()
        logging.info(f"  ✓ Super admin updated (ID: {user.id})")
        logging.info("  📧 Email: admin@example.com")


def main():
    """Run minimal system seed"""
    app = create_app()

    with app.app_context():
        logging.info("=" * 60)
        logging.info("MINIMAL SYSTEM SEEDER")
        logging.info("=" * 60)
        logging.info("This will create essential system data only")
        logging.info("Existing data (meters, readings, etc.) will NOT be affected")
        logging.info("=" * 60)

        try:
            # Create roles and permissions
            super_admin_role_id, admin_role_id, standard_role_id = ensure_roles_and_permissions()

            # Create super admin user
            ensure_super_admin_user(super_admin_role_id)

            logging.info("=" * 60)
            logging.info("✅ SYSTEM SEED COMPLETED SUCCESSFULLY")
            logging.info("=" * 60)
            logging.info("")
            logging.info("You can now login with:")
            logging.info("  Email: admin@example.com")
            logging.info("  Password: password")
            logging.info("")
            logging.info("⚠️  IMPORTANT: Change the password after first login!")
            logging.info("=" * 60)

        except Exception as e:
            logging.error(f"❌ Seeding failed: {e}", exc_info=True)
            db.session.rollback()
            sys.exit(1)


if __name__ == "__main__":
    main()
