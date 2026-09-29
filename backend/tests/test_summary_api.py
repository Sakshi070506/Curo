"""
Tests for Summary API endpoints.
"""

from fastapi.testclient import TestClient

from backend.main import app


def test_generate_summary():
    client = TestClient(app)
    # First create a session
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]

    # Answer a few questions
    client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint",
        "answer_text": "chest pain"
    })

    # Generate summary
    resp = client.post("/api/summary/generate", json={
        "patient_id": "p123",
        "session_id": sid
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "summary_id" in data
    assert "summary" in data
    assert data["summary"]["chief_complaint"] == "chest pain"


def test_get_summary():
    client = TestClient(app)
    # First generate a summary
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]
    client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint",
        "answer_text": "chest pain"
    })
    gen = client.post("/api/summary/generate", json={
        "patient_id": "p123",
        "session_id": sid
    }).json()
    summary_id = gen["summary_id"]

    # Get the summary
    resp = client.get(f"/api/summary/{summary_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary_id"] == summary_id
    assert data["status"] == "draft"


def test_get_summary_not_found():
    client = TestClient(app)
    resp = client.get("/api/summary/nonexistent")
    assert resp.status_code == 404


def test_confirm_summary():
    client = TestClient(app)
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]
    client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint",
        "answer_text": "chest pain"
    })
    gen = client.post("/api/summary/generate", json={
        "patient_id": "p123",
        "session_id": sid
    }).json()
    summary_id = gen["summary_id"]

    # Confirm the summary
    resp = client.post(f"/api/summary/{summary_id}/confirm", json={
        "summary_id": summary_id,
        "summary": gen["summary"],
        "confirmed": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "confirmed"


def test_confirm_summary_not_found():
    client = TestClient(app)
    resp = client.post("/api/summary/nonexistent/confirm", json={
        "summary_id": "nonexistent",
        "summary": {},
        "confirmed": True
    })
    assert resp.status_code == 404


def test_edit_summary():
    client = TestClient(app)
    start = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False}).json()
    sid = start["session_id"]
    client.post("/api/history/answer", json={
        "session_id": sid,
        "question_id": "chief_complaint",
        "answer_text": "chest pain"
    })
    gen = client.post("/api/summary/generate", json={
        "patient_id": "p123",
        "session_id": sid
    }).json()
    summary_id = gen["summary_id"]

    # Edit the summary
    resp = client.patch(f"/api/summary/{summary_id}/edit", json={
        "chief_complaint": "severe chest pain",
        "hpi": {"severity": "9/10"}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "edited"
    assert data["summary"]["chief_complaint"] == "severe chest pain"
    assert data["summary"]["hpi"]["severity"] == "9/10"


def test_edit_summary_not_found():
    client = TestClient(app)
    resp = client.patch("/api/summary/nonexistent/edit", json={
        "chief_complaint": "test"
    })
    assert resp.status_code == 404
