from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint

from ..db import db


@dataclass
class TicketMessage(db.Model):
    """
    Messages/replies within a ticket conversation.
    Can be from either staff (users) or residents (persons).
    """

    __tablename__ = "ticket_messages"

    id: Optional[int]
    ticket_id: int
    message: str
    sender_type: str
    sender_id: int
    is_internal: Optional[bool]
    created_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'staff' or 'customer'
    sender_id = db.Column(db.Integer, nullable=False)  # user_id if staff, person_id if customer
    is_internal = db.Column(db.Boolean, default=False)  # Internal notes visible only to staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "sender_type IN ('staff','customer')",
            name="ck_ticket_messages_sender_type",
        ),
    )

    # Relationships
    ticket = db.relationship("Ticket", back_populates="messages")

    @property
    def sender_name(self) -> str:
        """Get the sender's name based on sender_type"""
        if self.sender_type == "staff":
            from .user import User
            user = User.query.get(self.sender_id)
            if user:
                return f"{user.first_name} {user.last_name}"
        else:
            from .person import Person
            person = Person.query.get(self.sender_id)
            if person:
                return person.full_name
        return "Unknown"

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "message": self.message,
            "sender_type": self.sender_type,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "is_internal": self.is_internal,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
