"""
Module   : Pydantic Schemas
Owner    : Database Engineer
Purpose  : Request/response schemas mirroring the models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---- Auth / Identity (stubs for future use) ----
class RegisterRequest(BaseModel):
    abha_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    abha_id: str
    otp: str


# ---- Conversation Engine (Module A) ----
class StartSessionRequest(BaseModel):
    language: str = Field(default="en", pattern="^(en|hi|mr|ta|te|bn|gu|kn|ml|pa)$")
    ayush_mode: bool = False


class StartSessionResponse(BaseModel):
    session_id: str
    next_question: Dict[str, Any]


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: Optional[str] = None
    audio_b64: Optional[str] = None  # base64-encoded audio bytes


class AnswerResponse(BaseModel):
    session_id: str
    state: str
    red_flag: Dict[str, Any]
    next_question: Optional[Dict[str, Any]]
    complete: bool


class RedFlagCheckRequest(BaseModel):
    text: str


class RedFlagCheckResponse(BaseModel):
    triggered: bool
    matched_rules: List[Dict[str, str]] = []
    highest_severity: str = "none"


class HistorySessionOut(BaseModel):
    session_id: str
    language: str
    chief_complaint: str
    hpi: Dict[str, str]
    past_medical_history: List[str]
    drug_allergy_history: List[str]
    family_history: List[str]
    personal_history: Dict[str, str]
    review_of_systems: Dict[str, str]
    ayush: Dict[str, str]
    red_flags_triggered: List[Dict[str, str]]
    state: str


# ---- Triage / Alerts (Module A red-flag contract) ----
class TriageAlertRequest(BaseModel):
    patient_id: str
    session_id: str
    severity: str = Field(pattern="^(high|critical)$")
    matched_rules: List[Dict[str, str]]


class TriageAlertOut(BaseModel):
    id: str
    patient_id: str
    session_id: str
    severity: str
    matched_rules: List[Dict[str, str]]
    created_at: float
    acknowledged: bool
    requires_immediate_attention: bool


class TriageQueueResponse(BaseModel):
    alerts: List[TriageAlertOut]


# ---- Document Digitization (Module B) ----
class ParsedDocumentOut(BaseModel):
    document_type: str
    date: Optional[str]
    diagnoses: List[str]
    medications: List[Dict[str, Any]]
    investigations: List[Dict[str, Any]]
    raw_text: str


class DocumentTimelineOut(BaseModel):
    type: str
    date: Optional[str]
    diagnoses: List[str]
    medications: List[Dict[str, Any]]
    investigations: List[Dict[str, Any]]


# ---- Consent & ABDM (Module D) ----
class ConsentGrantRequest(BaseModel):
    patient_id: str
    purposes: List[str]  # e.g. ["history_capture", "document_digitization", "fhir_push"]
    granted: bool


class ConsentGrantResponse(BaseModel):
    consent_id: str
    patient_id: str
    purposes: List[str]
    granted: bool
    timestamp: float


class FHIRPushRequest(BaseModel):
    patient: Dict[str, Any]
    chief_complaint: Optional[str] = None
    diagnoses: List[str] = []
    medications: List[Dict[str, Any]] = []
    investigations: List[Dict[str, Any]] = []


class FHIRPushResponse(BaseModel):
    success: bool
    status_code: Optional[int]
    dry_run: bool
    message: str
    latency_ms: float


class ABDMStatusResponse(BaseModel):
    patient_id: str
    last_push: Optional[FHIRPushResponse]
    status: str  # "pending", "success", "failed", "not_attempted"


# ---- Summary / Physician Console (Module C - future) ----
class SummaryGenerateRequest(BaseModel):
    patient_id: str
    session_id: str


class SummaryConfirmRequest(BaseModel):
    patient_id: str
    summary: Dict[str, Any]
    confirmed: bool


# ---- Health ----
class HealthResponse(BaseModel):
    status: str = "ok"