"""
Module   : In-Memory Stores
Owner    : Backend Lead
Purpose  : Shared in-memory stores for demo without DB.
           Replace with DB-backed repositories for production.
"""

from __future__ import annotations

# Per-patient document store
document_store: dict[str, list[dict]] = {}

# Per-summary-id summary store
summary_store: dict[str, dict] = {}

# Per-consent-id consent store
consent_store: dict[str, dict] = {}

# Per-patient-id ABDM push status
abdm_status: dict[str, dict | None] = {}

# In-memory user store for auth
user_store: dict[str, dict] = {}

# In-memory triage queue
triage_queue: list[dict] = {}
