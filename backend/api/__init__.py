"""
Module   : API Package Init
Owner    : Backend Lead
Purpose  : Router aggregation.
"""

from fastapi import APIRouter

from backend.api.auth import router as auth_router
from backend.api.consent import router as consent_router
from backend.api.documents import router as documents_router
from backend.api.health import router as health_router
from backend.api.history import router as history_router
from backend.api.knowledge import router as knowledge_router
from backend.api.summary import router as summary_router
from backend.api.triage import router as triage_router
from backend.api.voice import router as voice_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(history_router)
api_router.include_router(triage_router)
api_router.include_router(documents_router)
api_router.include_router(consent_router)
api_router.include_router(summary_router)
api_router.include_router(auth_router)
api_router.include_router(voice_router)
api_router.include_router(knowledge_router)
