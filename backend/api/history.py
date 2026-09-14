"""
Module   : History/Conversation API
Owner    : Conversation AI Engineer
Purpose  : Endpoints for the voice+touch interview session.
"""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from config import settings
from database.schemas import (
    AnswerRequest,
    AnswerResponse,
    HistorySessionOut,
    RedFlagCheckRequest,
    RedFlagCheckResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from dependencies import (
    get_asr_service,
    get_dialogue_manager,
    get_notification_service,
    get_redflag_detector,
)
from services.redflag_service import build_triage_alert_payload

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/start-session", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(req: StartSessionRequest):
    dm = get_dialogue_manager()
    start = dm.start_session(language=req.language, ayush_mode=req.ayush_mode)
    return start


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(req: AnswerRequest):
    dm = get_dialogue_manager()
    asr = get_asr_service()

    # If only audio provided, transcribe first
    answer_text = req.answer_text
    if not answer_text and req.audio_b64:
        try:
            audio_bytes = base64.b64decode(req.audio_b64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid audio_b64: {exc}")
        # Use the session's language for ASR
        session = dm.get_session(req.session_id)
        asr_result = asr.transcribe(audio_bytes, session.language)
        answer_text = asr_result.transcript

    if not answer_text:
        raise HTTPException(status_code=400, detail="Either answer_text or audio_b64 must be provided")

    turn = dm.submit_answer(req.session_id, req.question_id, answer_text)

    # If red flag triggered, push to triage immediately (per Module A contract)
    if turn["red_flag"]["triggered"]:
        session = dm.get_session(req.session_id)
        try:
            # We need a patient_id - for now derive from session or use placeholder
            # In real flow, session would be linked to a patient
            patient_id = getattr(session, "patient_id", f"session_{req.session_id[:8]}")
            payload = build_triage_alert_payload(
                patient_id=patient_id,
                session_id=req.session_id,
                red_flag=type("obj", (object,), turn["red_flag"])()  # duck-type RedFlagResult
            )
            # The build_triage_alert_payload expects a RedFlagResult with matched_rules/highest_severity
            # Create a minimal object matching the expected interface
            from services.redflag_service import RedFlagResult
            rf_result = RedFlagResult(
                triggered=turn["red_flag"]["triggered"],
                matched_rules=turn["red_flag"]["matched_rules"],
                highest_severity=turn["red_flag"]["severity"],
            )
            payload = build_triage_alert_payload(
                patient_id=patient_id,
                session_id=req.session_id,
                red_flag=rf_result,
            )
            get_notification_service().push_triage_alert(
                patient_id=payload["patient_id"],
                session_id=payload["session_id"],
                severity=payload["severity"],
                matched_rules=payload["matched_rules"],
            )
        except Exception:
            # Don't fail the interview if triage push fails
            pass

    return turn


@router.get("/session/{session_id}", response_model=HistorySessionOut)
def get_session(session_id: str):
    dm = get_dialogue_manager()
    try:
        session = dm.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.post("/redflag-check", response_model=RedFlagCheckResponse)
def redflag_check(req: RedFlagCheckRequest):
    detector = get_redflag_detector()
    result = detector.check(req.text)
    return {
        "triggered": result.triggered,
        "matched_rules": result.matched_rules,
        "highest_severity": result.highest_severity,
    }