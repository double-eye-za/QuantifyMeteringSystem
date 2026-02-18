from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import random
import string

from sqlalchemy import CheckConstraint

from ..db import db


def generate_ticket_number():
    """Generate a unique ticket number like TKT-2024-ABC123"""
    year = datetime.utcnow().year
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TKT-{year}-{random_part}"


@dataclass
class Ticket(db.Model):
    """
    Support ticket model.
    Created by persons (mobile app users), managed by users (staff).
    """

    __tablename__ = "tickets"

    id: Optional[int]
    ticket_number: str
    subject: str
    description: str
    status: str
    priority: str
    category_id: Optional[int]
    created_by_person_id: int
    assigned_to_user_id: Optional[int]
    unit_id: Optional[int]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="open", nullable=False)
    priority = db.Column(db.String(20), default="medium", nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("ticket_categories.id"))
    created_by_person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"))
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('open','in_progress','pending','resolved','closed')",
            name="ck_tickets_status",
        ),
        CheckConstraint(
            "priority IN ('low','medium','high','urgent')",
            name="ck_tickets_priority",
        ),
    )

    # Relationships
    category = db.relationship("TicketCategory", back_populates="tickets")
    created_by_person = db.relationship("Person", backref="tickets")
    assigned_to_user = db.relationship("User", backref="assigned_tickets")
    unit = db.relationship("Unit", backref="tickets")
    messages = db.relationship(
        "TicketMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessage.created_at"
    )

    @staticmethod
    def generate_ticket_number():
        """Generate a unique ticket number"""
        return generate_ticket_number()

    @property
    def is_open(self) -> bool:
        return self.status in ("open", "in_progress", "pending")

    @property
    def message_count(self) -> int:
        return len(self.messages) if self.messages else 0

    @property
    def last_message(self):
        if self.messages:
            return self.messages[-1]
        return None

    @property
    def last_staff_response(self):
        """Get the last response from staff"""
        if self.messages:
            for msg in reversed(self.messages):
                if msg.sender_type == "staff":
                    return msg
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "category": self.category.to_dict() if self.category else None,
            "created_by_person": {
                "id": self.created_by_person.id,
                "name": self.created_by_person.full_name,
                "email": self.created_by_person.email,
            } if self.created_by_person else None,
            "assigned_to_user": {
                "id": self.assigned_to_user.id,
                "name": f"{self.assigned_to_user.first_name} {self.assigned_to_user.last_name}",
            } if self.assigned_to_user else None,
            "unit": {
                "id": self.unit.id,
                "unit_number": self.unit.unit_number,
            } if self.unit else None,
            "message_count": self.message_count,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_detailed(self):
        """Detailed dict with messages"""
        data = self.to_dict()
        data["messages"] = [msg.to_dict() for msg in self.messages]
        return data
