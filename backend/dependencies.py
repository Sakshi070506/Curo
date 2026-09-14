"""
Module   : Shared Dependencies
Owner    : Backend Lead
Purpose  : Reusable FastAPI dependencies (service singletons, DB session, auth guard).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from services.asr_service import ASRService
from services.dialogue_manager import DialogueManager
from services.fhir_service import ABDMPushResult
from services.notification_service import NotificationService
from services.ocr_service import OCRService
from services.redflag_service import RedFlagDetector
from services.tts_service import TTSService, preload_common_prompts


# In-memory singleton providers (for local dev / tests).
# In production, these would be DB-backed repositories via get_db().

_dialogue_manager: Optional[DialogueManager] = None
_notification_service: Optional[NotificationService] = None
_ocr_service: Optional[OCRService] = None
_asr_service: Optional[ASRService] = None
_tts_service: Optional[TTSService] = None
_redflag_detector: Optional[RedFlagDetector] = None


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


def preload_tts_prompts() -> int:
    """Warm the TTS cache with common prompts at startup."""
    svc = get_tts_service()
    return preload_common_prompts(svc)