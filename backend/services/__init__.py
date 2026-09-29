"""
Package  : backend/services
Purpose  : Re-exports service facades for convenient importing elsewhere in the
           backend, e.g.:

    from services import ASRService, TTSService, DialogueManager, OCRService

Placement note: this file assumes it lives inside backend/services/ alongside the
other seven files delivered with it (asr_service.py, tts_service.py,
redflag_service.py, ocr_service.py, notification_service.py, fhir_service.py,
dialogue_manager.py). If your project's import style differs (e.g. you don't treat
backend/services as a package), delete this file's imports and import the modules
directly instead — nothing else in these files depends on this __init__.py.
"""

from .asr_service import ASRResult, ASRService, BhashiniASRProvider, MockASRProvider
from .dialogue_manager import DialogueManager, HistorySession, SessionState
from .fhir_service import ABDMPushResult, build_fhir_bundle, push_to_abdm
from .notification_service import NotificationService, TriageAlert
from .ocr_service import OCRService, ParsedDocument
from .redflag_service import RedFlagDetector, RedFlagResult, RedFlagRule, build_triage_alert_payload
from .tts_service import (
    BhashiniTTSProvider,
    MockTTSProvider,
    TTSResult,
    TTSService,
    preload_common_prompts,
)

__all__ = [
    "ASRService", "MockASRProvider", "BhashiniASRProvider", "ASRResult",
    "TTSService", "MockTTSProvider", "BhashiniTTSProvider", "TTSResult", "preload_common_prompts",
    "RedFlagDetector", "RedFlagResult", "RedFlagRule", "build_triage_alert_payload",
    "OCRService", "ParsedDocument",
    "NotificationService", "TriageAlert",
    "build_fhir_bundle", "push_to_abdm", "ABDMPushResult",
    "DialogueManager", "HistorySession", "SessionState",
]
