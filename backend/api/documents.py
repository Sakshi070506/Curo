"""
Module   : Document Digitization API
Owner    : Document AI Engineer
Purpose  : Upload & digitize prior medical documents.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from database.schemas import DocumentTimelineOut, ParsedDocumentOut
from dependencies import get_ocr_service

router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory per-patient document store (for demo without DB)
_document_store: Dict[str, List[Dict]] = {}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), patient_id: str = "anonymous"):
    """Upload a document file and run OCR immediately, store result."""
    svc = get_ocr_service()
    content = await file.read()
    result = svc.process_document(content)
    doc_out = result.__dict__
    if patient_id not in _document_store:
        _document_store[patient_id] = []
    _document_store[patient_id].append(doc_out)
    return doc_out


@router.post("/extract", response_model=ParsedDocumentOut)
async def extract_document(file: UploadFile = File(...)):
    """Extract structured data from a document without persisting."""
    svc = get_ocr_service()
    content = await file.read()
    result = svc.process_document(content)
    return result.__dict__


@router.get("/{patient_id}/timeline", response_model=List[DocumentTimelineOut])
def get_timeline(patient_id: str):
    docs = _document_store.get(patient_id, [])
    return [
        {
            "type": d["document_type"],
            "date": d["date"],
            "diagnoses": d["diagnoses"],
            "medications": d["medications"],
            "investigations": d["investigations"],
        }
        for d in docs
    ]