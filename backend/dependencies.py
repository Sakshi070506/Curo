"""
Module   : Shared Dependencies
Owner    : Backend Lead
Purpose  : Reusable FastAPI dependencies (service singletons, DB session, auth guard).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.connection import get_engine, get_session_factory
from backend.services.asr_service import ASRService
from backend.services.dialogue_manager import DialogueManager
from backend.services.notification_service import NotificationService
from backend.services.ocr_service import OCRService
from backend.services.redflag_service import RedFlagDetector
from backend.services.tts_service import TTSService, preload_common_prompts

# In-memory singleton providers (for local dev / tests).
# In production, these would be DB-backed repositories via get_db().

_dialogue_manager: DialogueManager | None = None
_notification_service: NotificationService | None = None
_ocr_service: OCRService | None = None
_asr_service: ASRService | None = None
_tts_service: TTSService | None = None
_redflag_detector: RedFlagDetector | None = None


def get_dialogue_manager() -> DialogueManager:
    global _dialogue_manager
    if _dialogue_manager is None:
        _dialogue_manager = DialogueManager()
    return _dialogue_manager


def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service


def get_asr_service() -> ASRService:
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


def get_redflag_detector() -> RedFlagDetector:
    global _redflag_detector
    if _redflag_detector is None:
        _redflag_detector = RedFlagDetector()
    return _redflag_detector


# Database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    factory = get_session_factory(get_engine())
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Auth dependencies
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> dict | None:
    """Get current authenticated user from JWT token."""
    if not settings.auth_required or credentials is None:
        return None

    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # In production, fetch user from DB
        # For now, return mock user
        return {"id": user_id, "abha_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_auth(user: dict | None = Depends(get_current_user)) -> dict | None:
    """Dependency that requires authentication when auth_required is True."""
    if settings.auth_required and user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def preload_tts_prompts() -> int:
    """Warm the TTS cache with common prompts at startup."""
    svc = get_tts_service()
    return preload_common_prompts(svc)
