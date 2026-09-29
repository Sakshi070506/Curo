"""
Module   : Database Repository
Owner    : Database Engineer
Purpose  : Repository layer for data access - allows swapping between in-memory and DB implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from backend.services.dialogue_manager import HistorySession


# In-memory implementations (for tests without DB)
class InMemoryPatientRepo:
    def __init__(self):
        self._patients: dict[str, dict] = {}

    async def create(self, patient: dict) -> dict:
        self._patients[patient["id"]] = patient
        return patient

    async def get(self, patient_id: str) -> dict | None:
        return self._patients.get(patient_id)

    async def get_by_abha_id(self, abha_id: str) -> dict | None:
        for p in self._patients.values():
            if p.get("abha_id") == abha_id:
                return p
        return None

    async def update(self, patient_id: str, updates: dict) -> dict | None:
        if patient_id in self._patients:
            self._patients[patient_id].update(updates)
            return self._patients[patient_id]
        return None

    async def delete(self, patient_id: str) -> bool:
        if patient_id in self._patients:
            del self._patients[patient_id]
            return True
        return False


class InMemorySessionRepo:
    def __init__(self):
        self._sessions: dict[str, HistorySession] = {}

    async def create(self, session: HistorySession) -> HistorySession:
        self._sessions[session.session_id] = session
        return session

    async def get(self, session_id: str) -> HistorySession | None:
        return self._sessions.get(session_id)

    async def get_by_patient(self, patient_id: str) -> list[HistorySession]:
        return [s for s in self._sessions.values() if s.patient_id == patient_id]

    async def update(self, session: HistorySession) -> HistorySession:
        self._sessions[session.session_id] = session
        return session

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


class InMemoryDocumentRepo:
    def __init__(self):
        self._docs: dict[str, dict] = {}

    async def create(self, doc: dict) -> dict:
        self._docs[doc["id"]] = doc
        return doc

    async def get(self, doc_id: str) -> dict | None:
        return self._docs.get(doc_id)

    async def get_by_patient(self, patient_id: str) -> list[dict]:
        return [d for d in self._docs.values() if d.get("patient_id") == patient_id]

    async def update(self, doc_id: str, updates: dict) -> dict | None:
        if doc_id in self._docs:
            self._docs[doc_id].update(updates)
            return self._docs[doc_id]
        return None

    async def delete(self, doc_id: str) -> bool:
        if doc_id in self._docs:
            del self._docs[doc_id]
            return True
        return False


class InMemorySummaryRepo:
    def __init__(self):
        self._summaries: dict[str, dict] = {}

    async def create(self, summary: dict) -> dict:
        self._summaries[summary["id"]] = summary
        return summary

    async def get(self, summary_id: str) -> dict | None:
        return self._summaries.get(summary_id)

    async def get_by_patient(self, patient_id: str) -> list[dict]:
        return [s for s in self._summaries.values() if s.get("patient_id") == patient_id]

    async def get_by_session(self, session_id: str) -> dict | None:
        for s in self._summaries.values():
            if s.get("session_id") == session_id:
                return s
        return None

    async def update(self, summary_id: str, updates: dict) -> dict | None:
        if summary_id in self._summaries:
            self._summaries[summary_id].update(updates)
            return self._summaries[summary_id]
        return None

    async def delete(self, summary_id: str) -> bool:
        if summary_id in self._summaries:
            del self._summaries[summary_id]
            return True
        return False


class InMemoryConsentRepo:
    def __init__(self):
        self._consents: dict[str, dict] = {}

    async def create(self, consent: dict) -> dict:
        self._consents[consent["id"]] = consent
        return consent

    async def get(self, consent_id: str) -> dict | None:
        return self._consents.get(consent_id)

    async def get_latest_by_patient(self, patient_id: str) -> dict | None:
        patient_consents = [c for c in self._consents.values() if c.get("patient_id") == patient_id]
        if not patient_consents:
            return None
        return max(patient_consents, key=lambda c: c.get("timestamp", datetime.min))

    async def revoke(self, consent_id: str) -> bool:
        if consent_id in self._consents:
            del self._consents[consent_id]
            return True
        return False


class InMemoryTriageRepo:
    def __init__(self):
        self._alerts: dict[str, dict] = {}

    async def create(self, alert: dict) -> dict:
        self._alerts[alert["id"]] = alert
        return alert

    async def get(self, alert_id: str) -> dict | None:
        return self._alerts.get(alert_id)

    async def get_pending(self) -> list[dict]:
        return [a for a in self._alerts.values() if not a.get("acknowledged", False)]

    async def acknowledge(self, alert_id: str, acknowledged_by: str) -> bool:
        if alert_id in self._alerts:
            self._alerts[alert_id]["acknowledged"] = True
            self._alerts[alert_id]["acknowledged_at"] = datetime.utcnow().isoformat()
            self._alerts[alert_id]["acknowledged_by"] = acknowledged_by
            return True
        return False


class InMemoryClinicalKnowledgeRepo:
    def __init__(self):
        self._concepts: dict[str, dict] = {}

    async def create(self, concept: dict) -> dict:
        self._concepts[concept["id"]] = concept
        return concept

    async def bulk_create(self, concepts: list[dict]) -> int:
        for c in concepts:
            self._concepts[c["id"]] = c
        return len(concepts)

    async def get(self, concept_id: str) -> dict | None:
        return self._concepts.get(concept_id)

    async def list_by_category(self, category: str) -> list[dict]:
        return [c for c in self._concepts.values() if c.get("category") == category]


class InMemoryAuditRepo:
    def __init__(self):
        self._logs: list[dict] = []

    async def create(self, log: dict) -> dict:
        self._logs.append(log)
        return log

    async def get_by_patient(self, patient_id: str) -> list[dict]:
        return [l for l in self._logs if l.get("patient_id") == patient_id]


# Abstract base for DB implementations
class PatientRepository(ABC):
    @abstractmethod
    async def create(self, patient: dict) -> dict: ...

    @abstractmethod
    async def get(self, patient_id: str) -> dict | None: ...

    @abstractmethod
    async def get_by_abha_id(self, abha_id: str) -> dict | None: ...

    @abstractmethod
    async def update(self, patient_id: str, updates: dict) -> dict | None: ...


class SessionRepository(ABC):
    @abstractmethod
    async def create(self, session: HistorySession) -> HistorySession: ...

    @abstractmethod
    async def get(self, session_id: str) -> HistorySession | None: ...

    @abstractmethod
    async def get_by_patient(self, patient_id: str) -> list[HistorySession]: ...

    @abstractmethod
    async def update(self, session: HistorySession) -> HistorySession: ...


class DocumentRepository(ABC):
    @abstractmethod
    async def create(self, doc: dict) -> dict: ...

    @abstractmethod
    async def get(self, doc_id: str) -> dict | None: ...

    @abstractmethod
    async def get_by_patient(self, patient_id: str) -> list[dict]: ...


class SummaryRepository(ABC):
    @abstractmethod
    async def create(self, summary: dict) -> dict: ...

    @abstractmethod
    async def get(self, summary_id: str) -> dict | None: ...

    @abstractmethod
    async def get_by_patient(self, patient_id: str) -> list[dict]: ...

    @abstractmethod
    async def get_by_session(self, session_id: str) -> dict | None: ...

    @abstractmethod
    async def update(self, summary_id: str, updates: dict) -> dict | None: ...


class ConsentRepository(ABC):
    @abstractmethod
    async def create(self, consent: dict) -> dict: ...

    @abstractmethod
    async def get_latest_by_patient(self, patient_id: str) -> dict | None: ...

    @abstractmethod
    async def revoke(self, consent_id: str) -> bool: ...


class TriageRepository(ABC):
    @abstractmethod
    async def create(self, alert: dict) -> dict: ...

    @abstractmethod
    async def get_pending(self) -> list[dict]: ...

    @abstractmethod
    async def acknowledge(self, alert_id: str, acknowledged_by: str) -> bool: ...


class ClinicalKnowledgeRepository(ABC):
    @abstractmethod
    async def bulk_create(self, concepts: list[dict]) -> int: ...

    @abstractmethod
    async def get(self, concept_id: str) -> dict | None: ...

    @abstractmethod
    async def list_by_category(self, category: str) -> list[dict]: ...


class AuditRepository(ABC):
    @abstractmethod
    async def create(self, log: dict) -> dict: ...

    @abstractmethod
    async def get_by_patient(self, patient_id: str) -> list[dict]: ...


# Factory to get the right implementation
def get_repositories(use_db: bool = False, session=None):
    """Get repository instances. For tests, use in-memory; for production, use DB."""
    if use_db and session:
        # TODO: Implement DB-backed repositories using SQLAlchemy session
        raise NotImplementedError("DB repositories not yet implemented")

    return {
        "patients": InMemoryPatientRepo(),
        "sessions": InMemorySessionRepo(),
        "documents": InMemoryDocumentRepo(),
        "summaries": InMemorySummaryRepo(),
        "consents": InMemoryConsentRepo(),
        "triage": InMemoryTriageRepo(),
        "clinical_knowledge": InMemoryClinicalKnowledgeRepo(),
        "audit": InMemoryAuditRepo(),
    }
