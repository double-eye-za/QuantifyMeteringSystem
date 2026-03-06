from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class MeterPhoto(db.Model):
    __tablename__ = "meter_photos"

    id: Optional[int]
    meter_id: int
    filename: str
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    sort_order: Optional[int]
    uploaded_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    meter_id = db.Column(
        db.Integer,
        db.ForeignKey("meters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename = db.Column(db.String(255), nullable=False)  # UUID-based stored filename
    original_filename = db.Column(db.String(255), nullable=False)  # User's original filename
    file_size = db.Column(db.Integer, nullable=True)  # bytes
    mime_type = db.Column(db.String(50), nullable=True)  # e.g., image/jpeg
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    meter = db.relationship("Meter", back_populates="photos")

    def to_dict(self):
        return {
            "id": self.id,
            "meter_id": self.meter_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "sort_order": self.sort_order,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "url": f"/static/uploads/meters/{self.meter_id}/{self.filename}",
        }
