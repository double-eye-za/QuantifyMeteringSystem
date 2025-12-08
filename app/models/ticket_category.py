from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class TicketCategory(db.Model):
    """
    Dynamic categories for support tickets.
    Categories can be added/removed by admins.
    """

    __tablename__ = "ticket_categories"

    id: Optional[int]
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    is_active: Optional[bool]
    display_order: Optional[int]
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500))
    icon = db.Column(db.String(50))  # Font Awesome icon class, e.g., "fa-wrench"
    color = db.Column(db.String(20))  # CSS color class or hex, e.g., "blue" or "#3B82F6"
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    tickets = db.relationship("Ticket", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "is_active": self.is_active,
            "display_order": self.display_order,
            "ticket_count": len(self.tickets) if self.tickets else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
