"""
Module   : Document Digitization API
Owner    : Document AI Engineer
Purpose  : Upload & digitize prior medical documents.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, UploadFile, status

from backend.api.stores import document_store
from backend.database.schemas import DocumentTimelineOut, ParsedDocumentOut
from backend.dependencies import get_ocr_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), patient_id: str = "anonymous"):
    """Upload a document file and run OCR immediately, store result."""
    svc = get_ocr_service()
    content = await file.read()
    result = svc.process_document(content)
    doc_out = result.__dict__
    doc_out["document_id"] = str(uuid.uuid4())
    doc_out["patient_id"] = patient_id
    if patient_id not in document_store:
        document_store[patient_id] = []
    document_store[patient_id].append(doc_out)
    return doc_out


@router.post("/extract", response_model=ParsedDocumentOut)
async def extract_document(file: UploadFile = File(...)):
    """Extract structured data from a document without persisting."""
    svc = get_ocr_service()
    content = await file.read()
    result = svc.process_document(content)
    return result.__dict__


@router.get("/{patient_id}/timeline", response_model=list[DocumentTimelineOut])
def get_timeline(patient_id: str):
    docs = document_store.get(patient_id, [])
    # Sort chronologically by date
    ordered = sorted(docs, key=lambda d: d.get("date") or "0000-00-00")
    return [
        {
            "document_id": d.get("document_id", ""),
            "type": d["document_type"],
            "date": d["date"],
            "diagnoses": d["diagnoses"],
            "medications": d["medications"],
            "investigations": d["investigations"],
            "procedures": d.get("procedures", []),
        }
        for d in ordered
    ]
