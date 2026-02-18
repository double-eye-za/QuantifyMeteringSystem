from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class MessageRecipient(db.Model):
    """
    Message recipient tracking model.
    Tracks delivery and read status for each message recipient.
    """

    __tablename__ = "message_recipients"

    id: Optional[int]
    message_id: int
    person_id: int
    is_read: bool
    read_at: Optional[datetime]
    created_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('message_id', 'person_id', name='uq_message_recipient'),
        db.Index('ix_message_recipients_person_read', 'person_id', 'is_read'),
    )

    # Relationships
    message = db.relationship("Message", back_populates="recipients")
    person = db.relationship("Person", backref="received_messages")

    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "person": {
                "id": self.person.id,
                "name": self.person.full_name,
                "email": self.person.email,
            } if self.person else None,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_dict_for_mobile(self):
        """Message data formatted for mobile app"""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "subject": self.message.subject if self.message else None,
            "content": self.message.content if self.message else None,
            "message_type": self.message.message_type if self.message else None,
            "sender_name": f"{self.message.sender.first_name} {self.message.sender.last_name}" if self.message and self.message.sender else "System",
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sent_at": self.message.sent_at.isoformat() if self.message and self.message.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
