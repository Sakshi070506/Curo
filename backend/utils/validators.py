"""
Module   : Validators
Owner    : Backend Engineer
Purpose  : Shared input validation helpers.
"""

from __future__ import annotations

import re

from fastapi import HTTPException, UploadFile

# ABHA ID pattern: 14 digits with hyphens (XX-XXXX-XXXX-XXXX)
ABHA_ID_PATTERN = re.compile(r"^\d{2}-\d{4}-\d{4}-\d{4}$")

# Phone pattern: Indian mobile numbers
PHONE_PATTERN = re.compile(r"^(\+91|91)?[6-9]\d{9}$")

# Email pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Allowed file types for document upload
ALLOWED_DOCUMENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "application/pdf",
}

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_abha_id(abha_id: str) -> bool:
    """Validate ABHA ID format (XX-XXXX-XXXX-XXXX)."""
    return bool(ABHA_ID_PATTERN.match(abha_id))


def validate_phone(phone: str) -> bool:
    """Validate Indian phone number."""
    return bool(PHONE_PATTERN.match(phone))


def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(EMAIL_PATTERN.match(email))


def validate_file_upload(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}",
        )

    # Check file size by reading content
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {size} bytes exceeds maximum allowed {MAX_FILE_SIZE} bytes (10MB)",
        )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path traversal attempts
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    # Keep only alphanumeric, dots, hyphens, underscores
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:255 - len(ext) - 1] + ("." + ext if ext else "")
    return filename


def validate_date_iso(date_str: str) -> bool:
    """Validate ISO date format (YYYY-MM-DD)."""
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_language_code(lang: str) -> bool:
    """Validate supported language code."""
    supported = {"en", "hi", "mr", "ta", "te", "bn", "gu", "kn", "ml", "pa"}
    return lang in supported


def validate_severity(severity: str) -> bool:
    """Validate triage severity."""
    return severity in {"high", "critical"}


def validate_pagination(page: int, limit: int) -> tuple[int, int]:
    """Validate and clamp pagination parameters."""
    page = max(1, page)
    limit = min(max(1, limit), 100)
    return page, limit
