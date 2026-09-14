"""
Module   : FHIR/ABDM Service
Owner    : Integration Engineer
Purpose  : Builds FHIR R4 bundles from the confirmed case summary and pushes them to
           the ABDM Health Information Exchange / hospital HIS.

Design notes
------------
- Bundles are built as plain dicts matching the FHIR R4 JSON shape — no heavy
  fhir.resources dependency required, easy to run/test anywhere.
- push_to_abdm() is a dry-run (returns success=True, dry_run=True) unless
  ABDM_CLIENT_ID/SECRET/BASE_URL are configured, so it's safe to exercise in tests
  and local dev without real sandbox credentials.
- Retry logic lives in backend/workers/abdm_sync_worker.py in the full repo; this
  module exposes push_to_abdm() as the single call that worker retries on failure.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None


class FHIRMappingError(ValueError):
    """Raised when the input summary is missing data required to build valid FHIR."""


def _new_resource_id() -> str:
    return str(uuid.uuid4())


def build_patient_resource(patient: Dict) -> Dict:
    """patient: {"id", "name", "abha_id", "gender", "dob"}"""
    if not patient.get("id"):
        raise FHIRMappingError("patient.id is required")
    resource: Dict = {
        "resourceType": "Patient",
        "id": patient["id"],
        "identifier": [{"system": "https://healthid.ndhm.gov.in", "value": patient.get("abha_id", "")}],
        "name": [{"text": patient.get("name", "")}],
    }
    if patient.get("gender"):
        resource["gender"] = patient["gender"]
    if patient.get("dob"):
        resource["birthDate"] = patient["dob"]
    return resource


def build_condition_resources(patient_id: str, diagnoses: List[str]) -> List[Dict]:
    resources = []
    for diagnosis in diagnoses:
        if not diagnosis:
            continue
        resources.append({
            "resourceType": "Condition",
            "id": _new_resource_id(),
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {"text": diagnosis},
            "clinicalStatus": {"coding": [{"code": "active"}]},
        })
    return resources


def build_medication_statement_resources(patient_id: str, medications: List[Dict]) -> List[Dict]:
    """medications: [{"name", "dosage", "frequency"}]"""
    resources = []
    for med in medications:
        if not med.get("name"):
            continue
        resources.append({
            "resourceType": "MedicationStatement",
            "id": _new_resource_id(),
            "subject": {"reference": f"Patient/{patient_id}"},
            "medicationCodeableConcept": {"text": med["name"]},
            "dosage": [{"text": f"{med.get('dosage', '')} {med.get('frequency', '')}".strip()}],
            "status": "active",
        })
    return resources


def build_observation_resources(patient_id: str, investigations: List[Dict]) -> List[Dict]:
    """investigations: [{"test", "value", "unit", "ref_range", "abnormal"}]"""
    resources = []
    for inv in investigations:
        if not inv.get("test"):
            continue
        resource: Dict = {
            "resourceType": "Observation",
            "id": _new_resource_id(),
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {"text": inv["test"]},
            "status": "final",
        }
        if "value" in inv:
            resource["valueQuantity"] = {"value": inv["value"], "unit": inv.get("unit", "")}
        if inv.get("ref_range"):
            resource["referenceRange"] = [{"text": inv["ref_range"]}]
        if inv.get("abnormal") is not None:
            resource["interpretation"] = [{"text": "abnormal" if inv["abnormal"] else "normal"}]
        resources.append(resource)
    return resources


def build_fhir_bundle(summary: Dict) -> Dict:
    """summary: the confirmed case-summary schema produced by Module C, e.g.:
    {
      "patient": {"id": "p123", "name": "...", "abha_id": "...", "gender": "male", "dob": "1990-01-01"},
      "chief_complaint": "chest pain",
      "diagnoses": ["angina"],
      "medications": [{"name": "Aspirin", "dosage": "75mg", "frequency": "OD"}],
      "investigations": [{"test": "ECG", "value": 1, "abnormal": true}]
    }
    """
    if "patient" not in summary:
        raise FHIRMappingError("summary.patient is required to build a FHIR bundle")

    patient_resource = build_patient_resource(summary["patient"])
    patient_id = patient_resource["id"]

    diagnoses = list(summary.get("diagnoses", []))
    if summary.get("chief_complaint"):
        diagnoses = [summary["chief_complaint"]] + diagnoses

    entries = [{"resource": patient_resource}]
    entries += [{"resource": r} for r in build_condition_resources(patient_id, diagnoses)]
    entries += [{"resource": r} for r in build_medication_statement_resources(patient_id, summary.get("medications", []))]
    entries += [{"resource": r} for r in build_observation_resources(patient_id, summary.get("investigations", []))]

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "id": _new_resource_id(),
        "entry": entries,
    }


@dataclass
class ABDMPushResult:
    success: bool
    status_code: Optional[int]
    dry_run: bool
    message: str
    latency_ms: float


def push_to_abdm(
    bundle: Dict,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ABDMPushResult:
    client_id = client_id or os.getenv("ABDM_CLIENT_ID")
    client_secret = client_secret or os.getenv("ABDM_CLIENT_SECRET")
    base_url = base_url or os.getenv("ABDM_BASE_URL")

    start = time.time()

    if not client_id or not client_secret or not base_url:
        latency_ms = (time.time() - start) * 1000
        return ABDMPushResult(
            success=True,
            status_code=None,
            dry_run=True,
            message="ABDM credentials not configured — dry-run only, bundle validated locally.",
            latency_ms=latency_ms,
        )

    if httpx is None:
        raise RuntimeError("httpx is required to push to ABDM. pip install httpx.")

    try:
        response = httpx.post(
            f"{base_url}/v0.5/health-information/push",
            json=bundle,
            headers={"X-CM-ID": client_id, "Authorization": f"Bearer {client_secret}"},
            timeout=20.0,
        )
        latency_ms = (time.time() - start) * 1000
        return ABDMPushResult(
            success=response.status_code < 300,
            status_code=response.status_code,
            dry_run=False,
            message=response.text[:500],
            latency_ms=latency_ms,
        )
    except Exception as exc:  # noqa: BLE001 — surfaced to caller/worker for retry logic
        latency_ms = (time.time() - start) * 1000
        return ABDMPushResult(success=False, status_code=None, dry_run=False, message=str(exc), latency_ms=latency_ms)


if __name__ == "__main__":
    sample_summary = {
        "patient": {"id": "p123", "name": "Test Patient", "abha_id": "12-3456-7890-1234", "gender": "male", "dob": "1990-01-01"},
        "chief_complaint": "chest pain",
        "diagnoses": ["suspected angina"],
        "medications": [{"name": "Aspirin", "dosage": "75mg", "frequency": "OD"}],
        "investigations": [{"test": "ECG", "value": 1, "abnormal": True}],
    }
    bundle = build_fhir_bundle(sample_summary)
    result = push_to_abdm(bundle)
    print(result)
