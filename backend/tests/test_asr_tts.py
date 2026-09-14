import pytest
from services.asr_service import ASRService, MockASRProvider, UnsupportedLanguageError
from services.tts_service import TTSService, MockTTSProvider, preload_common_prompts, COMMON_PROMPTS


# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------
def test_asr_transcribe_returns_result():
    svc = ASRService(provider=MockASRProvider())
    result = svc.transcribe(b"some-audio-bytes", "en")
    assert result.transcript
    assert 0.0 <= result.confidence <= 1.0
    assert result.language_code == "en"
    assert result.provider == "mock"


def test_asr_deterministic_for_same_input():
    svc = ASRService(provider=MockASRProvider())
    r1 = svc.transcribe(b"identical-bytes", "en")
    r2 = svc.transcribe(b"identical-bytes", "en")
    assert r1.transcript == r2.transcript


def test_asr_rejects_unsupported_language():
    svc = ASRService(provider=MockASRProvider())
    with pytest.raises(UnsupportedLanguageError):
        svc.transcribe(b"audio", "xx")


def test_asr_rejects_empty_audio():
    svc = ASRService(provider=MockASRProvider())
    with pytest.raises(ValueError):
        svc.transcribe(b"", "en")


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------
def test_tts_synthesize_returns_audio():
    svc = TTSService(provider=MockTTSProvider())
    result = svc.synthesize("Hello there", "en")
    assert result.audio_bytes
    assert result.content_type == "audio/wav"
    assert result.cached is False


def test_tts_cache_hit_on_repeat():
    svc = TTSService(provider=MockTTSProvider())
    first = svc.synthesize("Please wait", "en")
    second = svc.synthesize("Please wait", "en")
    assert first.cached is False
    assert second.cached is True
    assert first.audio_bytes == second.audio_bytes


def test_tts_cache_is_per_language():
    svc = TTSService(provider=MockTTSProvider())
    en = svc.synthesize("Welcome", "en")
    hi = svc.synthesize("Welcome", "hi")
    assert en.cached is False
    assert hi.cached is False  # different language -> different cache key
    assert en.audio_bytes != hi.audio_bytes


def test_tts_rejects_empty_text():
    svc = TTSService(provider=MockTTSProvider())
    with pytest.raises(ValueError):
        svc.synthesize("   ", "en")


def test_preload_common_prompts_warms_cache():
    svc = TTSService(provider=MockTTSProvider())
    count = preload_common_prompts(svc)
    expected = sum(len(v) for v in COMMON_PROMPTS.values())
    assert count == expected
    # now every common prompt should be a cache hit
    result = svc.synthesize(COMMON_PROMPTS["hi"]["welcome"], "hi")
    assert result.cached is True


def test_tts_cache_eviction_respects_cache_size():
    svc = TTSService(provider=MockTTSProvider(), cache_size=2)
    svc.synthesize("one", "en")
    svc.synthesize("two", "en")
    svc.synthesize("three", "en")  # should evict the oldest entry
    assert len(svc._cache) <= 2