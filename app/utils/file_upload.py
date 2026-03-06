"""File upload utilities for meter photos.

Handles validation, unique naming, directory creation, and deletion
of uploaded image files stored at app/static/uploads/meters/{meter_id}/.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Set, Tuple

from flask import current_app
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: Set[str] = {"jpg", "jpeg", "png", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_dir(meter_id: int) -> str:
    """Get (and create if needed) the upload directory for a specific meter."""
    upload_folder = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.static_folder, "uploads", "meters"),
    )
    meter_dir = os.path.join(upload_folder, str(meter_id))
    os.makedirs(meter_dir, exist_ok=True)
    return meter_dir


def save_upload(file: FileStorage, meter_id: int) -> Tuple[str, str, int, str]:
    """Save an uploaded file to the meter's directory.

    Args:
        file: The uploaded file (from request.files).
        meter_id: The meter this photo belongs to.

    Returns:
        Tuple of (stored_filename, original_filename, file_size, mime_type).

    Raises:
        ValueError: If file is invalid or has a disallowed extension.
    """
    if not file or not file.filename:
        raise ValueError("No file provided")

    if not allowed_file(file.filename):
        raise ValueError(
            f"File type not allowed. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    original_filename = file.filename
    ext = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    mime_type = file.content_type or f"image/{ext}"

    meter_dir = get_upload_dir(meter_id)
    filepath = os.path.join(meter_dir, stored_filename)

    file.save(filepath)
    file_size = os.path.getsize(filepath)

    logger.info(
        "Saved photo %s for meter %d (%d bytes)", stored_filename, meter_id, file_size
    )
    return stored_filename, original_filename, file_size, mime_type


def delete_upload(meter_id: int, filename: str) -> bool:
    """Delete an uploaded file from disk.

    Args:
        meter_id: The meter the photo belongs to.
        filename: The stored filename (UUID-based).

    Returns:
        True if the file was deleted, False if not found.
    """
    upload_folder = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.static_folder, "uploads", "meters"),
    )
    filepath = os.path.join(upload_folder, str(meter_id), filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        logger.info("Deleted photo %s for meter %d", filename, meter_id)
        return True
    logger.warning(
        "Photo file not found for deletion: %s (meter %d)", filename, meter_id
    )
    return False


def delete_meter_upload_dir(meter_id: int) -> bool:
    """Delete the entire upload directory for a meter (used when meter is deleted).

    Args:
        meter_id: The meter whose photo directory should be removed.

    Returns:
        True if the directory was removed, False if not found.
    """
    import shutil

    upload_folder = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.static_folder, "uploads", "meters"),
    )
    meter_dir = os.path.join(upload_folder, str(meter_id))
    if os.path.isdir(meter_dir):
        shutil.rmtree(meter_dir)
        logger.info("Deleted photo directory for meter %d", meter_id)
        return True
    return False
