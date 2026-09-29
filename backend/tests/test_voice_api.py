"""
Tests for Voice API endpoints.
"""

import base64

from fastapi.testclient import TestClient

from backend.main import app


def test_tts_endpoint():
    client = TestClient(app)
    resp = client.post("/api/voice/tts", json={
        "text": "Hello world",
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "audio_b64" in data
    assert data["content_type"] == "audio/wav"
    assert data["language"] == "en"
    assert "cached" in data
    assert "provider" in data
    assert "latency_ms" in data


def test_tts_cache():
    client = TestClient(app)
    # First call
    resp1 = client.post("/api/voice/tts", json={
        "text": "Cache test",
        "language": "en"
    })
    assert resp1.json()["cached"] is False

    # Second call with same text
    resp2 = client.post("/api/voice/tts", json={
        "text": "Cache test",
        "language": "en"
    })
    assert resp2.json()["cached"] is True


def test_asr_endpoint():
    client = TestClient(app)
    audio_b64 = base64.b64encode(b"fake audio").decode()
    resp = client.post("/api/voice/asr", json={
        "audio_b64": audio_b64,
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "transcript" in data
    assert data["language"] == "en"
    assert "provider" in data
    assert "confidence" in data


def test_asr_invalid_audio():
    client = TestClient(app)
    resp = client.post("/api/voice/asr", json={
        "audio_b64": "not valid base64!",
        "language": "en"
    })
    assert resp.status_code == 400


def test_asr_unsupported_language():
    client = TestClient(app)
    audio_b64 = base64.b64encode(b"fake audio").decode()
    resp = client.post("/api/voice/asr", json={
        "audio_b64": audio_b64,
        "language": "xx"
    })
    assert resp.status_code == 400


def test_voice_prompts():
    client = TestClient(app)
    resp = client.get("/api/voice/prompts")
    assert resp.status_code == 200
    data = resp.json()
    assert "prompts" in data
    assert "en" in data["prompts"]
    assert "hi" in data["prompts"]
    assert "welcome" in data["prompts"]["en"]
