"""
Module   : Triage API
Owner    : Backend Engineer
Purpose  : Red-flag alert queue for hospital staff.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from database.schemas import TriageAlertOut, TriageAlertRequest, TriageQueueResponse
from dependencies import get_notification_service

router = APIRouter(prefix="/api/triage", tags=["triage"])


@router.post("/alert", response_model=TriageAlertOut, status_code=status.HTTP_201_CREATED)
def push_alert(req: TriageAlertRequest):
    svc = get_notification_service()
    alert = svc.push_triage_alert(
        patient_id=req.patient_id,
        session_id=req.session_id,
        severity=req.severity,
        matched_rules=req.matched_rules,
    )
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "session_id": alert.session_id,
        "severity": alert.severity,
        "matched_rules": alert.matched_rules,
        "created_at": alert.created_at,
        "acknowledged": alert.acknowledged,
        "requires_immediate_attention": alert.severity == "critical",
    }


@router.get("/queue", response_model=TriageQueueResponse)
def get_queue():
    svc = get_notification_service()
    alerts = svc.get_queue()
    return {
        "alerts": [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "session_id": a.session_id,
                "severity": a.severity,
                "matched_rules": a.matched_rules,
                "created_at": a.created_at,
                "acknowledged": a.acknowledged,
                "requires_immediate_attention": a.severity == "critical",
            }
            for a in alerts
        ]
    }


@router.post("/acknowledge/{alert_id}")
def acknowledge_alert(alert_id: str):
    svc = get_notification_service()
    ok = svc.acknowledge(alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"acknowledged": True}