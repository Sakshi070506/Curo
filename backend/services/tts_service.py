"""
Module   : Text-to-Speech Service
Owner    : Conversation AI Engineer
Purpose  : Generates audio prompts in the patient's language, with caching of
           common prompts so repeated phrases don't hit the TTS provider every time.

Design notes
------------
- Same provider pattern as asr_service.py: BhashiniTTSProvider for prod,
  MockTTSProvider for local dev/tests (no real audio backend required).
- TTSService caches results by (text, language) so `preload_common_prompts()`
  can warm the cache at startup for phrases like the consent explanation.
"""

from __future__ import annotations

import base64
import hashlib
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Protocol

try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class TTSResult:
    audio_bytes: bytes
    content_type: str
    language_code: str
    provider: str
    cached: bool
    latency_ms: float


class TTSProvider(Protocol):
    def synthesize(self, text: str, language_code: str) -> bytes: ...


class BhashiniTTSProvider:
    """Real TTS provider — calls the Bhashini / AI4Bharat inference API."""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, timeout: float = 15.0):
        self.api_key = api_key or os.getenv("BHASHINI_API_KEY")
        self.api_url = api_url or os.getenv("BHASHINI_API_URL")
        self.timeout = timeout

    def synthesize(self, text: str, language_code: str) -> bytes:
        if not self.api_key or not self.api_url:
            raise RuntimeError(
                "Bhashini credentials missing. Set BHASHINI_API_KEY / BHASHINI_API_URL, "
                "or inject MockTTSProvider for local development."
            )
        if httpx is None:
            raise RuntimeError("httpx is required for BhashiniTTSProvider. pip install httpx.")

        payload = {"config": {"language": {"sourceLanguage": language_code}}, "input": [{"source": text}]}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = httpx.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        # NOTE: adjust this extraction to match the real Bhashini pipeline response
        # once sandbox credentials are available.
        audio_items = data.get("audio", [{}])
        audio_b64 = audio_items[0].get("audioContent", "") if audio_items else ""
        return base64.b64decode(audio_b64) if audio_b64 else b""


class MockTTSProvider:
    """Deterministic offline provider. Produces a small synthetic payload (not
    real audio) so calling code, caching, and content-type handling can all be
    tested without a network connection or an audio backend installed."""

    def synthesize(self, text: str, language_code: str) -> bytes:
        if not text.strip():
            raise ValueError("text must not be empty")
        return f"MOCK_AUDIO::{language_code}::{text}".encode("utf-8")


class TTSService:
    """Facade with an in-memory cache keyed on (text, language)."""

    def __init__(self, provider: Optional[TTSProvider] = None, cache_size: int = 256):
        self.provider = provider or self._default_provider()
        self.cache_size = cache_size
        self._cache: Dict[str, TTSResult] = {}

    @staticmethod
    def _default_provider() -> TTSProvider:
        if os.getenv("BHASHINI_API_KEY") and os.getenv("BHASHINI_API_URL"):
            return BhashiniTTSProvider()
        return MockTTSProvider()

    @staticmethod
    def _cache_key(text: str, language_code: str) -> str:
        return hashlib.sha256(f"{language_code}::{text}".encode()).hexdigest()

    def synthesize(self, text: str, language_code: str = "en") -> TTSResult:
        key = self._cache_key(text, language_code)
        if key in self._cache:
            cached = self._cache[key]
            return TTSResult(
                audio_bytes=cached.audio_bytes,
                content_type=cached.content_type,
                language_code=language_code,
                provider=cached.provider,
                cached=True,
                latency_ms=0.0,
            )

        start = time.time()
        audio_bytes = self.provider.synthesize(text, language_code)
        latency_ms = (time.time() - start) * 1000

        result = TTSResult(
            audio_bytes=audio_bytes,
            content_type="audio/wav",
            language_code=language_code,
            provider=type(self.provider).__name__,
            cached=False,
            latency_ms=latency_ms,
        )

        if len(self._cache) >= self.cache_size:
            self._cache.pop(next(iter(self._cache)))  # drop oldest inserted key
        self._cache[key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()


# Common prompts worth pre-rendering at kiosk startup (docs/architecture.md,
# Module A: "TTS-based audio prompts for low-literacy/elderly patients").
COMMON_PROMPTS = {
    "en": {
        "welcome": "Welcome. Please select your preferred language.",
        "consent_request": "We need your consent to record your medical history. Do you agree?",
        "session_complete": "Thank you. Your history has been recorded.",
    },
    "hi": {
        "welcome": "स्वागत है। कृपया अपनी पसंदीदा भाषा चुनें।",
        "consent_request": "आपका मेडिकल इतिहास दर्ज करने के लिए हमें आपकी सहमति चाहिए। क्या आप सहमत हैं?",
        "session_complete": "धन्यवाद। आपका इतिहास दर्ज कर लिया गया है।",
    },
}


def preload_common_prompts(service: TTSService) -> int:
    """Warms the cache with COMMON_PROMPTS so the first patient of the day doesn't
    pay the synthesis latency cost. Returns the number of prompts preloaded."""
    count = 0
    for language_code, prompts in COMMON_PROMPTS.items():
        for _, text in prompts.items():
            service.synthesize(text, language_code)
            count += 1
    return count


if __name__ == "__main__":
    svc = TTSService(provider=MockTTSProvider())
    n = preload_common_prompts(svc)
    print(f"Preloaded {n} prompts")
    result = svc.synthesize(COMMON_PROMPTS["hi"]["welcome"], "hi")
    print("cached:", result.cached, "| provider:", result.provider, "| bytes:", len(result.audio_bytes))
