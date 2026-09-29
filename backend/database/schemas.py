"""
Module   : Pydantic Schemas
Owner    : Database Engineer
Purpose  : Request/response schemas mirroring the models.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---- Auth / Identity ----
class RegisterRequest(BaseModel):
    abha_id: str
    name: str
    phone: str | None = None
    email: str | None = None


class LoginRequest(BaseModel):
    abha_id: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    authenticated: bool
    abha_id: str | None = None
    name: str | None = None
    phone: str | None = None
    email: str | None = None


# ---- Conversation Engine (Module A) ----
class StartSessionRequest(BaseModel):
    language: str = Field(default="en", pattern="^(en|hi|mr|ta|te|bn|gu|kn|ml|pa)$")
    ayush_mode: bool = False


class StartSessionResponse(BaseModel):
    session_id: str
    next_question: dict[str, Any]


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: str | None = None
    audio_b64: str | None = None  # base64-encoded audio bytes


class AnswerResponse(BaseModel):
    session_id: str
    state: str
    red_flag: dict[str, Any]
    next_question: dict[str, Any] | None
    complete: bool


class RedFlagCheckRequest(BaseModel):
    text: str


class RedFlagCheckResponse(BaseModel):
    triggered: bool
    matched_rules: list[dict[str, str]] = []
    highest_severity: str = "none"


class HistorySessionOut(BaseModel):
    session_id: str
    language: str
    chief_complaint: str
    hpi: dict[str, str]
    past_medical_history: list[str]
    drug_allergy_history: list[str]
    family_history: list[str]
    personal_history: dict[str, str]
    review_of_systems: dict[str, str]
    ayush: dict[str, str]
    red_flags_triggered: list[dict[str, str]]
    state: str


# ---- Triage / Alerts (Module A red-flag contract) ----
class TriageAlertRequest(BaseModel):
    patient_id: str
    session_id: str
    severity: str = Field(pattern="^(high|critical)$")
    matched_rules: list[dict[str, str]]


class TriageAlertOut(BaseModel):
    id: str
    patient_id: str
    session_id: str
    severity: str
    matched_rules: list[dict[str, str]]
    created_at: float
    acknowledged: bool
    requires_immediate_attention: bool


class TriageQueueResponse(BaseModel):
    alerts: list[TriageAlertOut]


# ---- Document Digitization (Module B) ----
class ParsedDocumentOut(BaseModel):
    document_type: str
    document_id: str | None = None
    patient_id: str | None = None
    date: str | None
    diagnoses: list[str]
    medications: list[dict[str, Any]]
    investigations: list[dict[str, Any]]
    procedures: list[str] = []
    dates: list[str] = []
    raw_text: str
    raw_ocr_confidence: float = 0.0


class DocumentTimelineOut(BaseModel):
    document_id: str
    type: str
    date: str | None
    diagnoses: list[str]
    medications: list[dict[str, Any]]
    investigations: list[dict[str, Any]]
    procedures: list[str] = []


# ---- Consent & ABDM (Module D) ----
class ConsentGrantRequest(BaseModel):
    patient_id: str
    # Granular consent per purpose
    data_capture: bool = False
    share_with_his: bool = False
    link_abha_phr: bool = False
    consent_language: str = "en"


class ConsentGrantResponse(BaseModel):
    consent_id: str
    patient_id: str
    data_capture: bool
    share_with_his: bool
    link_abha_phr: bool
    consent_language: str
    timestamp: str  # ISO-8601
    audit_trail_id: str


class ConsentStatusResponse(BaseModel):
    patient_id: str
    data_capture: bool
    share_with_his: bool
    link_abha_phr: bool
    consent_language: str
    timestamp: str
    audit_trail_id: str


class FHIRPushRequest(BaseModel):
    patient: dict[str, Any]
    chief_complaint: str | None = None
    diagnoses: list[str] = []
    medications: list[dict[str, Any]] = []
    investigations: list[dict[str, Any]] = []


class FHIRPushResponse(BaseModel):
    success: bool
    status_code: int | None
    dry_run: bool
    message: str
    latency_ms: float


class ABDMStatusResponse(BaseModel):
    patient_id: str
    last_push: FHIRPushResponse | None
    status: str  # "pending", "success", "failed", "not_attempted"


# ---- Summary / Physician Console (Module C) ----
class SummaryGenerateRequest(BaseModel):
    patient_id: str
    session_id: str


class SummaryConfirmRequest(BaseModel):
    summary_id: str
    summary: dict[str, Any]
    confirmed: bool


class SummaryEditRequest(BaseModel):
    summary_id: str
    patches: dict[str, Any]


class SummaryResponse(BaseModel):
    summary_id: str
    patient_id: str
    session_id: str
    summary: dict[str, Any]
    source_attribution: dict[str, str]
    missing_sections: list[str]
    status: str


# ---- Voice (Module A - TTS/ASR) ----
class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class TTSResponse(BaseModel):
    audio_b64: str
    content_type: str
    language: str
    cached: bool
    provider: str
    latency_ms: float


class ASRRequest(BaseModel):
    audio_b64: str
    language: str = "en"


class ASRResponse(BaseModel):
    transcript: str
    confidence: float
    language: str
    provider: str
    latency_ms: float


class VoicePromptsResponse(BaseModel):
    prompts: dict[str, dict[str, str]]


# ---- Knowledge / RAG (Module E) ----
class KnowledgeSearchRequest(BaseModel):
    query: str
    k: int = 5
    category: str | None = None
    min_similarity: float = 0.3


class KnowledgeSearchResponse(BaseModel):
    results: list[dict[str, Any]]


class DrugInteractionRequest(BaseModel):
    medications: list[dict[str, Any]]


class DrugInteractionResponse(BaseModel):
    interactions: list[dict[str, Any]]
    highest_severity: str


# ---- Health ----
class HealthResponse(BaseModel):
    status: str = "ok"


class HealthReadyResponse(BaseModel):
    status: str
    database: str
    timestamp: str
