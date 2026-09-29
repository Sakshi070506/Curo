"""
Module   : Voice API
Owner    : Conversation AI Engineer
Purpose  : TTS/ASR endpoints for voice-enabled interview.
"""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException

from backend.database.schemas import (
    ASRRequest,
    ASRResponse,
    TTSRequest,
    TTSResponse,
    VoicePromptsResponse,
)
from backend.dependencies import get_asr_service, get_tts_service, require_auth
from backend.services.asr_service import UnsupportedLanguageError
from backend.services.tts_service import COMMON_PROMPTS

# Import exception for local tests
try:
    from backend.services.asr_service import UnsupportedLanguageError as ASRUnsupportedLanguageError
except ImportError:
    ASRUnsupportedLanguageError = None

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/tts", response_model=TTSResponse)
def text_to_speech(req: TTSRequest, user: dict | None = Depends(require_auth)):
    """Convert text to speech audio."""
    tts = get_tts_service()
    try:
        result = tts.synthesize(req.text, req.language)
        audio_b64 = base64.b64encode(result.audio_bytes).decode()
        return TTSResponse(
            audio_b64=audio_b64,
            content_type=result.content_type,
            language=result.language_code,
            cached=result.cached,
            provider=result.provider,
            latency_ms=result.latency_ms,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}")


@router.post("/asr", response_model=ASRResponse)
def speech_to_text(req: ASRRequest, user: dict | None = Depends(require_auth)):
    """Convert speech audio to text."""
    asr = get_asr_service()
    try:
        audio_bytes = base64.b64decode(req.audio_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid audio_b64: {exc}")

    try:
        result = asr.transcribe(audio_bytes, req.language)
        return ASRResponse(
            transcript=result.transcript,
            confidence=result.confidence,
            language=result.language_code,
            provider=result.provider,
            latency_ms=result.latency_ms,
        )
    except UnsupportedLanguageError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ASR failed: {exc}")


@router.get("/prompts", response_model=VoicePromptsResponse)
def get_common_prompts():
    """Get preloaded common TTS prompts for the kiosk UI."""
    return VoicePromptsResponse(prompts=COMMON_PROMPTS)
