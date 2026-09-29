"""
Module   : Database Package
Owner    : Database Engineer
Purpose  : Database package exports.
"""

from backend.database.connection import (
    close_db,
    get_db,
    get_engine,
    get_session_factory,
    init_db,
)
from backend.database.models import (
    AuditLog,
    Base,
    ClinicalKnowledge,
    ConsentRecord,
    Document,
    HistorySession,
    Patient,
    Summary,
    TriageAlert,
)
from backend.database.repository import (
    AuditRepository,
    ClinicalKnowledgeRepository,
    ConsentRepository,
    DocumentRepository,
    PatientRepository,
    SessionRepository,
    SummaryRepository,
    TriageRepository,
    get_repositories,
)

__all__ = [
    # Models
    "Patient",
    "HistorySession",
    "Document",
    "Summary",
    "ConsentRecord",
    "TriageAlert",
    "ClinicalKnowledge",
    "AuditLog",
    "Base",
    # Connection
    "get_engine",
    "get_session_factory",
    "get_db",
    "init_db",
    "close_db",
    # Repository
    "get_repositories",
    "PatientRepository",
    "SessionRepository",
    "DocumentRepository",
    "SummaryRepository",
    "ConsentRepository",
    "TriageRepository",
    "ClinicalKnowledgeRepository",
    "AuditRepository",
]
