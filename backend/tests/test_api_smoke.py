"""API smoke tests - verify the FastAPI app boots and core endpoints respond."""
from fastapi.testclient import TestClient


def test_app_boots():
    from main import app
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_start_session():
    from main import app
    client = TestClient(app)
    resp = client.post("/api/history/start-session", json={"language": "en", "ayush_mode": False})
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert data["next_question"]["question_id"] == "chief_complaint"


def test_answer_flow():
    from main import app
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


def test_redflag_check_endpoint():
    from main import app
    client = TestClient(app)
    resp = client.post("/api/history/redflag-check", json={"text": "chest pain and breathless"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["triggered"] is True
    assert data["highest_severity"] == "critical"


def test_triage_alert_and_queue():
    from main import app
    client = TestClient(app)
    # Push alert
    resp = client.post("/api/triage/alert", json={
        "patient_id": "p1",
        "session_id": "s1",
        "severity": "critical",
        "matched_rules": [{"id": "acute_coronary_syndrome", "description": "Chest pain", "severity": "critical"}]
    })
    assert resp.status_code == 201
    alert = resp.json()
    assert alert["patient_id"] == "p1"
    assert alert["requires_immediate_attention"] is True

    # Get queue
    resp = client.get("/api/triage/queue")
    assert resp.status_code == 200
    queue = resp.json()
    assert len(queue) >= 1


def test_document_extract():
    from main import app
    client = TestClient(app)
    # Use mock extractor - the OCRService defaults to MockExtractor when tesseract not available
    resp = client.post(
        "/api/documents/extract",
        files={"file": ("test.txt", b"Discharge Summary dated 05/08/2026\nDx: Diabetes\nMetformin 500mg BD\n", "text/plain")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_type"] in ("prescription", "lab_report", "discharge_summary")
    assert data["date"] == "2026-08-05"


def test_fhir_push_dry_run():
    from main import app
    client = TestClient(app)
    resp = client.post("/api/abdm/push-fhir", json={
        "patient": {"id": "p123", "name": "Test Patient", "abha_id": "12-3456-7890-1234", "gender": "male", "dob": "1990-01-01"},
        "chief_complaint": "chest pain",
        "diagnoses": ["angina"],
        "medications": [{"name": "Aspirin", "dosage": "75mg", "frequency": "OD"}],
        "investigations": [{"test": "ECG", "value": 1, "abnormal": True}]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["dry_run"] is True