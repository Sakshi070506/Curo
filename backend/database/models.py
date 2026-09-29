"""
Module   : DB Models
Owner    : Database Engineer
Purpose  : SQLAlchemy models: patients, sessions, documents, summaries, consents, triage_alerts, clinical_knowledge.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    abha_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    dob: Mapped[str | None] = mapped_column(String(32), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    history_sessions: Mapped[list[HistorySession]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    documents: Mapped[list[Document]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    summaries: Mapped[list[Summary]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    consents: Mapped[list[ConsentRecord]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    triage_alerts: Mapped[list[TriageAlert]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class HistorySession(Base):
    __tablename__ = "history_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    ayush_mode: Mapped[bool] = mapped_column(default=False, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="START")

    # Interview data (JSON columns for flexible schema)
    chief_complaint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hpi: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    past_medical_history: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    drug_allergy_history: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    family_history: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    personal_history: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    review_of_systems: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ayush: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    red_flags_triggered: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)

    # Internal state cursors
    _socrates_idx: Mapped[int] = mapped_column(default=0, nullable=False)
    _ros_idx: Mapped[int] = mapped_column(default=0, nullable=False)
    _dashavidha_idx: Mapped[int] = mapped_column(default=0, nullable=False)
    _raw_answers: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    patient: Mapped[Patient] = relationship(back_populates="history_sessions")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("history_sessions.id", ondelete="SET NULL"), nullable=True)

    document_type: Mapped[str] = mapped_column(String(32), nullable=False)  # prescription, lab_report, discharge_summary
    date: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Extracted entities
    diagnoses: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    medications: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    investigations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    procedures: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    dates: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    raw_ocr_confidence: Mapped[float] = mapped_column(default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient: Mapped[Patient] = relationship(back_populates="documents")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("history_sessions.id", ondelete="CASCADE"), nullable=False)

    # Structured summary (Module C format)
    chief_complaint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hpi: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    past_medical_history: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    past_surgical_history: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    drug_allergy_history: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    family_history: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    personal_history: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    review_of_systems: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    prior_investigations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    ayush: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    source_attribution: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict, nullable=False)
    missing_sections: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)  # draft, confirmed, edited
    confirmed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    patient: Mapped[Patient] = relationship(back_populates="summaries")


class ConsentRecord(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)

    # Granular consent per purpose
    data_capture: Mapped[bool] = mapped_column(default=False, nullable=False)
    share_with_his: Mapped[bool] = mapped_column(default=False, nullable=False)
    link_abha_phr: Mapped[bool] = mapped_column(default=False, nullable=False)

    consent_language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    audit_trail_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Relationships
    patient: Mapped[Patient] = relationship(back_populates="consents")


class TriageAlert(Base):
    __tablename__ = "triage_alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("history_sessions.id", ondelete="CASCADE"), nullable=False)

    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # high, critical
    matched_rules: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    requires_immediate_attention: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged: Mapped[bool] = mapped_column(default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    patient: Mapped[Patient] = relationship(back_populates="triage_alerts")


class ClinicalKnowledge(Base):
    __tablename__ = "clinical_knowledge"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    concept_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # symptom, drug, lab, procedure, diagnosis
    icd_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    snomed_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_questions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # pgvector column (only populated for PostgreSQL)
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_clinical_knowledge_category_name", "category", "name"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # consent_granted, fhir_push, summary_generated, etc.
    event_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_logs_patient_created", "patient_id", "created_at"),
    )
