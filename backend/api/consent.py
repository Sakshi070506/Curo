"""
Module   : Consent & ABDM API
Owner    : Integration Engineer
Purpose  : Consent capture + FHIR push to HIS/ABDM.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.stores import abdm_status, consent_store
from backend.config import settings
from backend.database.schemas import (
    ABDMStatusResponse,
    ConsentGrantRequest,
    ConsentGrantResponse,
    ConsentStatusResponse,
    FHIRPushRequest,
    FHIRPushResponse,
)
from backend.dependencies import require_auth
from backend.services.fhir_service import build_fhir_bundle, push_to_abdm

router = APIRouter(prefix="/api", tags=["consent", "abdm"])


@router.post("/consent/grant", response_model=ConsentGrantResponse, status_code=status.HTTP_201_CREATED)
def grant_consent(req: ConsentGrantRequest, user: dict = Depends(require_auth)):
    consent_id = str(uuid.uuid4())
    audit_trail_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    record = {
        "consent_id": consent_id,
        "patient_id": req.patient_id,
        "data_capture": req.data_capture,
        "share_with_his": req.share_with_his,
        "link_abha_phr": req.link_abha_phr,
        "consent_language": req.consent_language,
        "timestamp": timestamp,
        "audit_trail_id": audit_trail_id,
    }
    consent_store[consent_id] = record
    return record


@router.get("/consent/status/{patient_id}", response_model=ConsentStatusResponse)
def get_consent_status(patient_id: str):
    """Get the latest consent status for a patient."""
    # Find the most recent consent for this patient
    patient_consents = [c for c in consent_store.values() if c.get("patient_id") == patient_id]
    if not patient_consents:
        raise HTTPException(status_code=404, detail="No consent found for patient")

    latest = max(patient_consents, key=lambda c: c.get("timestamp", ""))
    return latest


@router.delete("/consent/revoke/{consent_id}")
def revoke_consent(consent_id: str):
    """Revoke a specific consent."""
    if consent_id not in consent_store:
        raise HTTPException(status_code=404, detail="Consent not found")
    del consent_store[consent_id]
    return {"revoked": True, "consent_id": consent_id}


@router.post("/abdm/push-fhir", response_model=FHIRPushResponse)
def push_fhir(req: FHIRPushRequest, user: dict = Depends(require_auth)):
    """Build FHIR bundle from summary and push to ABDM sandbox."""
    # Merge chief_complaint into diagnoses if provided
    diagnoses = list(req.diagnoses)
    if req.chief_complaint:
        diagnoses = [req.chief_complaint] + diagnoses

    summary = {
        "patient": req.patient,
        "chief_complaint": req.chief_complaint,
        "diagnoses": diagnoses,
        "medications": req.medications,
        "investigations": req.investigations,
    }

    try:
        bundle = build_fhir_bundle(summary)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid summary for FHIR: {exc}")

    # Use ABDM credentials from settings (env vars) for dry-run / real push
    result = push_to_abdm(
        bundle=bundle,
        client_id=settings.abdm_client_id,
        client_secret=settings.abdm_client_secret,
        base_url=settings.abdm_base_url,
    )

    # Store last push status for /status endpoint
    patient_id = req.patient.get("id", "unknown")
    abdm_status[patient_id] = result

    return {
        "success": result.success,
        "status_code": result.status_code,
        "dry_run": result.dry_run,
        "message": result.message,
        "latency_ms": result.latency_ms,
    }


@router.get("/abdm/status/{patient_id}", response_model=ABDMStatusResponse)
def abdm_status_endpoint(patient_id: str):
    last = abdm_status.get(patient_id)
    if last is None:
        return {
            "patient_id": patient_id,
            "last_push": None,
            "status": "not_attempted",
        }
    return {
        "patient_id": patient_id,
        "last_push": {
            "success": last.success,
            "status_code": last.status_code,
            "dry_run": last.dry_run,
            "message": last.message,
            "latency_ms": last.latency_ms,
        },
        "status": "success" if last.success else "failed",
    }
