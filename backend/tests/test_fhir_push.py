"""
Module   : FHIR Push Tests
Owner    : QA / Integration Engineer
Purpose  : Tests for FHIR bundle construction & ABDM push.
"""


import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.fhir_service import FHIRMappingError, build_fhir_bundle, push_to_abdm

SAMPLE_SUMMARY = {
    "patient": {"id": "p123", "name": "Test Patient", "abha_id": "12-3456-7890-1234", "gender": "male", "dob": "1990-01-01"},
    "chief_complaint": "chest pain",
    "diagnoses": ["suspected angina"],
    "medications": [{"name": "Aspirin", "dosage": "75mg", "frequency": "OD"}],
    "investigations": [{"test": "ECG", "value": 1, "abnormal": True}],
}


def test_build_fhir_bundle_structure():
    bundle = build_fhir_bundle(SAMPLE_SUMMARY)
    assert bundle["resourceType"] == "Bundle"
    resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Patient" in resource_types
    assert "Condition" in resource_types
    assert "MedicationStatement" in resource_types
    assert "Observation" in resource_types


def test_build_fhir_bundle_includes_chief_complaint_as_condition():
    bundle = build_fhir_bundle(SAMPLE_SUMMARY)
    conditions = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Condition"]
    condition_texts = [c["code"]["text"] for c in conditions]
    assert "chest pain" in condition_texts
    assert "suspected angina" in condition_texts


def test_build_fhir_bundle_requires_patient():
    with pytest.raises(FHIRMappingError):
        build_fhir_bundle({"chief_complaint": "fever"})


def test_build_fhir_bundle_requires_patient_id():
    with pytest.raises(FHIRMappingError):
        build_fhir_bundle({"patient": {"name": "No ID Patient"}})


def test_push_to_abdm_dry_run_without_credentials(monkeypatch):
    monkeypatch.delenv("ABDM_CLIENT_ID", raising=False)
    monkeypatch.delenv("ABDM_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("ABDM_BASE_URL", raising=False)
    bundle = build_fhir_bundle(SAMPLE_SUMMARY)
    result = push_to_abdm(bundle)
    assert result.success is True
    assert result.dry_run is True


def test_summary_to_fhir_input():
    """Test the contract function summary_to_fhir_input."""
    from backend.services.fhir_service import summary_to_fhir_input

    summary = {
        "chief_complaint": "chest pain",
        "diagnoses": ["angina"],
        "past_medical_history": ["hypertension"],
        "drug_allergy_history": ["penicillin"],
        "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BD"}],
        "prior_investigations": [{"test": "HbA1c", "value": 8.2, "unit": "%", "ref_range": "4.0-5.6", "abnormal": True}],
        "investigations": [{"test": "ECG", "value": 1, "abnormal": True}],
    }
    patient = {"id": "p123", "name": "Test Patient", "abha_id": "12-3456-7890-1234", "gender": "male", "dob": "1990-01-01"}

    fhir_input = summary_to_fhir_input(summary, patient)

    assert fhir_input["patient"] == patient
    assert fhir_input["chief_complaint"] == "chest pain"
    assert "angina" in fhir_input["diagnoses"]
    assert "hypertension" in fhir_input["diagnoses"]
    assert "chest pain" in fhir_input["diagnoses"]
    # Should include both structured medications and drug_allergy_history
    med_names = [m["name"] for m in fhir_input["medications"]]
    assert "Metformin" in med_names
    assert "penicillin" in med_names
    # Should include both prior_investigations and investigations
    assert len(fhir_input["investigations"]) >= 2


def test_fhir_push_dry_run_endpoint():
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


def test_abdm_status_endpoint():
    client = TestClient(app)
    resp = client.get("/api/abdm/status/unknown-patient")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_attempted"
    assert data["last_push"] is None
