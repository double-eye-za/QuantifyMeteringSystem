from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint

from ..db import db


@dataclass
class Message(db.Model):
    """
    Broadcast message model.
    Allows admins to send messages to all users, estate users, or individuals.
    """

    __tablename__ = "messages"

    id: Optional[int]
    subject: str
    content: str
    message_type: str
    sender_user_id: int
    estate_id: Optional[int]
    recipient_person_id: Optional[int]
    recipient_count: int
    created_at: Optional[datetime]
    sent_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), nullable=False)
    sender_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    estate_id = db.Column(db.Integer, db.ForeignKey("estates.id"), nullable=True)
    recipient_person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    recipient_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "message_type IN ('broadcast', 'estate', 'individual')",
            name="ck_messages_type",
        ),
    )

    # Relationships
    sender = db.relationship("User", backref="sent_messages", foreign_keys=[sender_user_id])
    estate = db.relationship("Estate", backref="messages")
    recipient_person = db.relationship("Person", backref="direct_messages", foreign_keys=[recipient_person_id])
    recipients = db.relationship(
        "MessageRecipient",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    @property
    def message_type_display(self) -> str:
        """Get display name for message type"""
        return {
            'broadcast': 'All Users',
            'estate': 'Estate',
            'individual': 'Individual'
        }.get(self.message_type, self.message_type)

    @property
    def read_count(self) -> int:
        """Get count of recipients who have read the message"""
        return self.recipients.filter_by(is_read=True).count()

    @property
    def read_percentage(self) -> float:
        """Get percentage of recipients who have read the message"""
        if self.recipient_count == 0:
            return 0.0
        return round((self.read_count / self.recipient_count) * 100, 1)

    @property
    def is_sent(self) -> bool:
        """Check if message has been sent"""
        return self.sent_at is not None

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "subject": self.subject,
            "content": self.content,
            "message_type": self.message_type,
            "message_type_display": self.message_type_display,
            "sender": {
                "id": self.sender.id,
                "name": f"{self.sender.first_name} {self.sender.last_name}",
            } if self.sender else None,
            "estate": {
                "id": self.estate.id,
                "name": self.estate.name,
            } if self.estate else None,
            "recipient_person": {
                "id": self.recipient_person.id,
                "name": self.recipient_person.full_name,
                "email": self.recipient_person.email,
            } if self.recipient_person else None,
            "recipient_count": self.recipient_count,
            "read_count": self.read_count,
            "read_percentage": self.read_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }

    def to_dict_summary(self):
        """Lighter version for list views"""
        return {
            "id": self.id,
            "subject": self.subject,
            "message_type": self.message_type,
            "message_type_display": self.message_type_display,
            "recipient_count": self.recipient_count,
            "read_count": self.read_count,
            "read_percentage": self.read_percentage,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
