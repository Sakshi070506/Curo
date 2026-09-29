"""
Module   : Security Utils
Owner    : Backend Lead / Integration Engineer
Purpose  : Field-level encryption + consent audit trail helpers.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import datetime

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class FieldEncryption:
    """Field-level encryption for PII using Fernet (AES-128-GCM)."""

    def __init__(self, key: bytes | None = None):
        if key is None:
            # Derive key from environment or generate
            master_key = os.getenv("ENCRYPTION_MASTER_KEY")
            if master_key:
                key = self._derive_key(master_key.encode())
            else:
                # Generate a new key for development
                key = Fernet.generate_key()
        self.fernet = Fernet(key)

    @staticmethod
    def _derive_key(password: bytes) -> bytes:
        """Derive a Fernet key from a password using PBKDF2."""
        salt = b"curo_salt_2024"  # In production, use a random salt per deployment
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        if not value:
            return ""
        encrypted = self.fernet.encrypt(value.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt a string value."""
        if not encrypted_value:
            return ""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode("utf-8"))
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode("utf-8")
        except Exception:
            return ""  # Return empty string on decryption failure


# Singleton instance
_field_encryption: FieldEncryption | None = None


def get_field_encryption() -> FieldEncryption:
    """Get the field encryption singleton."""
    global _field_encryption
    if _field_encryption is None:
        _field_encryption = FieldEncryption()
    return _field_encryption


class ConsentAuditLog:
    """Append-only consent audit trail."""

    def __init__(self):
        self._logs: list[dict] = []

    def log_consent(
        self,
        patient_id: str,
        action: str,  # granted, revoked, viewed
        consent_type: str,  # data_capture, share_with_his, link_abha_phr
        granted: bool,
        metadata: dict | None = None,
    ) -> dict:
        """Log a consent action."""
        log_entry = {
            "audit_id": secrets.token_urlsafe(16),
            "patient_id": patient_id,
            "action": action,
            "consent_type": consent_type,
            "granted": granted,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {},
        }
        self._logs.append(log_entry)
        return log_entry

    def get_audit_trail(self, patient_id: str) -> list[dict]:
        """Get full audit trail for a patient."""
        return [log for log in self._logs if log["patient_id"] == patient_id]

    def get_latest_consent(self, patient_id: str, consent_type: str) -> dict | None:
        """Get the latest consent decision for a specific type."""
        logs = [
            log for log in self._logs
            if log["patient_id"] == patient_id and log["consent_type"] == consent_type
        ]
        if not logs:
            return None
        return max(logs, key=lambda x: x["timestamp"])


# Singleton
_consent_audit_log: ConsentAuditLog | None = None


def get_consent_audit_log() -> ConsentAuditLog:
    """Get the consent audit log singleton."""
    global _consent_audit_log
    if _consent_audit_log is None:
        _consent_audit_log = ConsentAuditLog()
    return _consent_audit_log


def hash_pii(value: str) -> str:
    """Create a deterministic hash of PII for indexing without exposing the value."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def mask_pii(value: str, visible_chars: int = 4) -> str:
    """Mask PII for display (e.g., phone: 999******99)."""
    if not value or len(value) <= visible_chars * 2:
        return "*" * len(value) if value else ""
    return value[:visible_chars] + "*" * (len(value) - visible_chars * 2) + value[-visible_chars:]
