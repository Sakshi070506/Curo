"""
Module   : Health Check
Owner    : Backend Lead
Purpose  : Liveness/readiness probe.
"""

from __future__ import annotations

from fastapi import APIRouter

from database.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}