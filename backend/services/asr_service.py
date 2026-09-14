"""
Module   : Speech-to-Text Service
Owner    : Conversation AI Engineer
Purpose  : Wraps Bhashini/AI4Bharat ASR models for multilingual speech-to-text.

Design notes
------------
- Provider pattern: swap the ASR backend (Bhashini API, any other vendor, or a
  local mock for tests) without touching any calling code.
- Public entrypoint: ASRService().transcribe(audio_bytes, language_code) -> ASRResult
- MockASRProvider is deterministic (hash-based) so unit tests are reproducible
  without any network access or real audio pipeline.
"""

from __future__ import annotations

import base64
import hashlib
import os
import time
from dataclasses import dataclass
from typing import Optional, Protocol

try:
    import httpx
except ImportError:  # httpx is optional unless BhashiniASRProvider is actually used
    httpx = None


SUPPORTED_LANGUAGES = {
    "hi": "Hindi",
    "en": "English",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
}


class UnsupportedLanguageError(ValueError):
    """Raised when a language code isn't in SUPPORTED_LANGUAGES."""


@dataclass
class ASRResult:
    transcript: str
    confidence: float
    language_code: str
    provider: str
    latency_ms: float


class ASRProvider(Protocol):
    def transcribe(self, audio_bytes: bytes, language_code: str) -> ASRResult: ...


class BhashiniASRProvider:
    """Real ASR provider — calls the Bhashini / AI4Bharat inference API.

    Requires BHASHINI_API_KEY / BHASHINI_API_URL (see .env.example). Not exercised
    in the automated tests (no network access there) — MockASRProvider covers the
    behavioral contract instead.
    """

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, timeout: float = 15.0):
        self.api_key = api_key or os.getenv("BHASHINI_API_KEY")
        self.api_url = api_url or os.getenv("BHASHINI_API_URL")
        self.timeout = timeout

    def transcribe(self, audio_bytes: bytes, language_code: str) -> ASRResult:
        if not self.api_key or not self.api_url:
            raise RuntimeError(
                "Bhashini credentials missing. Set BHASHINI_API_KEY and BHASHINI_API_URL "
                "in .env, or inject MockASRProvider for local development."
            )
        if httpx is None:
            raise RuntimeError("httpx is required for BhashiniASRProvider. pip install httpx.")

        payload = {
            "config": {"language": {"sourceLanguage": language_code}},
            "audio": [{"audioContent": base64.b64encode(audio_bytes).decode()}],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        start = time.time()
        response = httpx.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        latency_ms = (time.time() - start) * 1000

        # NOTE: Bhashini's actual response shape depends on the deployed pipeline
        # config. Adjust this extraction once you have real sandbox credentials
        # and can inspect a live response.
        output = data.get("output", [{}])
        transcript = output[0].get("source", "") if output else ""
        confidence = float(output[0].get("confidence", 0.0)) if output else 0.0

        return ASRResult(
            transcript=transcript,
            confidence=confidence,
            language_code=language_code,
            provider="bhashini",
            latency_ms=latency_ms,
        )


class MockASRProvider:
    """Deterministic offline provider for local dev/tests.

    Returns a canned transcript derived from a hash of the audio bytes, so the
    same input always produces the same output without any real ASR backend.
    """

    _CANNED_TRANSCRIPTS = [
        "chest pain since this morning",
        "fever and cough for three days",
        "stomach ache after eating",
        "headache and dizziness",
        "difficulty breathing",
    ]

    def transcribe(self, audio_bytes: bytes, language_code: str) -> ASRResult:
        if not audio_bytes:
            raise ValueError("audio_bytes must not be empty")
        start = time.time()
        idx = int(hashlib.sha256(audio_bytes).hexdigest(), 16) % len(self._CANNED_TRANSCRIPTS)
        transcript = self._CANNED_TRANSCRIPTS[idx]
        latency_ms = (time.time() - start) * 1000
        return ASRResult(
            transcript=transcript,
            confidence=0.92,
            language_code=language_code,
            provider="mock",
            latency_ms=latency_ms,
        )


class ASRService:
    """Facade used by the rest of the app (e.g. backend/api/history.py).

    Defaults to BhashiniASRProvider when credentials are present in the
    environment, otherwise falls back to MockASRProvider — so the same code
    path works in prod and in local dev/tests.
    """

    def __init__(self, provider: Optional[ASRProvider] = None):
        self.provider = provider or self._default_provider()

    @staticmethod
    def _default_provider() -> ASRProvider:
        if os.getenv("BHASHINI_API_KEY") and os.getenv("BHASHINI_API_URL"):
            return BhashiniASRProvider()
        return MockASRProvider()

    def transcribe(self, audio_bytes: bytes, language_code: str = "en") -> ASRResult:
        if language_code not in SUPPORTED_LANGUAGES:
            raise UnsupportedLanguageError(
                f"'{language_code}' is not supported. Supported: {list(SUPPORTED_LANGUAGES)}"
            )
        return self.provider.transcribe(audio_bytes, language_code)


if __name__ == "__main__":
    svc = ASRService(provider=MockASRProvider())
    result = svc.transcribe(b"fake-audio-bytes-for-demo", "hi")
    print(result)
