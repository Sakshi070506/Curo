"""
Module   : API Package Init
Owner    : Backend Lead
Purpose  : Router aggregation.
"""

from fastapi import APIRouter

from api.health import router as health_router
from api.history import router as history_router
from api.triage import router as triage_router
from api.documents import router as documents_router
from api.consent import router as consent_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(history_router)
api_router.include_router(triage_router)
api_router.include_router(documents_router)
api_router.include_router(consent_router)