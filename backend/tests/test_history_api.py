"""
Module   : History API Tests
Owner    : QA / Conversation AI Engineer
Purpose  : Unit/integration tests for history endpoints.
"""

from fastapi.testclient import TestClient

from backend.main import app


def test_start_session():
    client = TestClient(app)
    resp = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False})
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert data["next_question"]["question_id"] == "chief_complaint"


def test_answer_flow():
    client = TestClient(app)
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]

    # First answer
    resp = client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint",
        "answer_text": "chest pain"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "HPI_LOOP"
    assert "next_question" in data

    # Second answer
    qid = data["next_question"]["question_id"]
    resp = client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": qid,
        "answer_text": "it started this morning"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "HPI_LOOP"


def test_redflag_check_endpoint():
    client = TestClient(app)
    resp = client.post("/api/history/redflag-check", json={"text": "chest pain and breathless"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["triggered"] is True
    assert data["highest_severity"] == "critical"


def test_redflag_check_no_trigger():
    client = TestClient(app)
    resp = client.post("/api/history/redflag-check", json={"text": "mild headache"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["triggered"] is False


def test_get_session():
    client = TestClient(app)
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]

    # Submit one answer
    client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint",
        "answer_text": "chest pain"
    })

    # Get session
    resp = client.get(f"/api/history/session/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert data["chief_complaint"] == "chest pain"
    assert data["state"] == "HPI_LOOP"


def test_get_session_not_found():
    client = TestClient(app)
    resp = client.get("/api/history/session/invalid-session-id")
    assert resp.status_code == 404


def test_answer_with_audio():
    client = TestClient(app)
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]

    # Submit with base64 audio (mock)
    import base64
    audio_b64 = base64.b64encode(b"fake audio").decode()
    resp = client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint",
        "audio_b64": audio_b64
    })
    # Should work (mock ASR returns canned transcript)
    assert resp.status_code == 200
    data = resp.json()
    assert "state" in data


def test_answer_missing_both():
    client = TestClient(app)
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]

    resp = client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint"
    })
    assert resp.status_code == 400
