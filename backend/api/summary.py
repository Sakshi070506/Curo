"""
Module   : Summary API
Owner    : Summary/LLM Engineer
Purpose  : Generate & manage the structured case summary.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from backend.api.stores import document_store, summary_store
from backend.database.schemas import SummaryConfirmRequest, SummaryGenerateRequest
from backend.dependencies import get_dialogue_manager

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_summary(req: SummaryGenerateRequest):
    """Generate structured case summary from interview + documents."""
    from backend.ai.summary.synthesizer import synthesize

    dm = get_dialogue_manager()
    try:
        session = dm.get_session(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    interview = session.to_dict()

    # Get documents for this patient
    patient_id = getattr(session, "patient_id", None) or req.patient_id or req.session_id
    docs = document_store.get(patient_id, [])

    document_json = {"documents": docs}

    result = await synthesize(interview, document_json)

    summary_id = f"summary_{req.session_id[:8]}"
    summary_store[summary_id] = {
        "summary_id": summary_id,
        "patient_id": patient_id,
        "session_id": req.session_id,
        "summary": result.summary,
        "source_attribution": result.source_attribution,
        "missing_sections": result.missing_sections,
        "status": "draft",
    }

    return {
        "summary_id": summary_id,
        "summary": result.summary,
        "source_attribution": result.source_attribution,
        "missing_sections": result.missing_sections,
    }


@router.get("/{summary_id}")
async def get_summary(summary_id: str):
    if summary_id not in summary_store:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary_store[summary_id]


@router.post("/{summary_id}/confirm")
async def confirm_summary(summary_id: str, req: SummaryConfirmRequest):
    if summary_id not in summary_store:
        raise HTTPException(status_code=404, detail="Summary not found")
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Confirmation required")
    summary_store[summary_id]["status"] = "confirmed"
    summary_store[summary_id]["summary"] = req.summary
    return {"status": "confirmed", "summary_id": summary_id}


@router.patch("/{summary_id}/edit")
async def edit_summary(summary_id: str, patches: dict[str, Any]):
    if summary_id not in summary_store:
        raise HTTPException(status_code=404, detail="Summary not found")
    summary = summary_store[summary_id]["summary"]
    # Apply patches (deep merge for nested dicts)
    def deep_merge(base: dict, updates: dict) -> dict:
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    summary_store[summary_id]["summary"] = deep_merge(summary, patches)
    summary_store[summary_id]["status"] = "edited"
    return {"status": "edited", "summary_id": summary_id, "summary": summary_store[summary_id]["summary"]}
