"""
Module   : Consent & ABDM API
Owner    : Integration Engineer
Purpose  : Consent capture + FHIR push to HIS/ABDM.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from config import settings
from database.schemas import ABDMStatusResponse, ConsentGrantRequest, ConsentGrantResponse, FHIRPushRequest, FHIRPushResponse
from dependencies import get_ocr_service, get_tts_service
from services.fhir_service import ABDMPushResult, build_fhir_bundle, push_to_abdm

router = APIRouter(prefix="/api", tags=["consent", "abdm"])

# In-memory consent store and ABDM push status (for demo without DB)
_consent_store: Dict[str, Dict] = {}
_abdm_status: Dict[str, Optional[ABDMPushResult]] = {}


@router.post("/consent/grant", response_model=ConsentGrantResponse, status_code=status.HTTP_201_CREATED)
def grant_consent(req: ConsentGrantRequest):
    import time
    import uuid
    consent_id = str(uuid.uuid4())
    record = {
        "consent_id": consent_id,
        "patient_id": req.patient_id,
        "purposes": req.purposes,
        "granted": req.granted,
        "timestamp": time.time(),
    }
    _consent_store[consent_id] = record
    return record


@router.post("/abdm/push-fhir", response_model=FHIRPushResponse)
def push_fhir(req: FHIRPushRequest):
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
    _abdm_status[patient_id] = result

    return {
        "success": result.success,
        "status_code": result.status_code,
        "dry_run": result.dry_run,
        "message": result.message,
        "latency_ms": result.latency_ms,
    }


@router.get("/abdm/status/{patient_id}", response_model=ABDMStatusResponse)
def abdm_status(patient_id: str):
    last = _abdm_status.get(patient_id)
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