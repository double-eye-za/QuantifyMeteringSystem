from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from ..db import db


@dataclass
class Permission(db.Model):
    __tablename__ = "permissions"

    id: Optional[int]
    name: str
    description: Optional[str]
    permissions: dict

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.JSON, nullable=False, default=dict)
    roles = db.relationship("Role", back_populates="permission")

    def update_permissions(self, permissions_data):
        try:
            self.permissions = permissions_data
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def delete_permission(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    # Static methods removed; use app.services.permissions for CRUD operations
