# Module D — Consent, Privacy & ABDM Integration

**Owner:** Integration Engineer
**Code:** `backend/api/consent.py`, `backend/services/fhir_service.py`, `backend/workers/abdm_sync_worker.py`, `backend/utils/security.py`
**Frontend:** `frontend/src/pages/ConsentScreen.jsx`, `services/abdmService.js`

## Goal

Handle patient authentication (ABHA), consent capture, secure processing, and pushing
the finalized case summary into the hospital HIS/EMR and the ABDM ecosystem — compliant
with the Digital Personal Data Protection (DPDP) Act 2023 and the ABDM consent
framework.

## Key Behaviors

1. **ABHA-based authentication** — patient identifies via ABHA ID (or Aadhaar, or
   registers as new). See `backend/api/auth.py` for the verification endpoint.
2. **Granular, revocable consent** — patient explicitly consents to (a) data capture,
   (b) sharing with the hospital HIS, (c) linking to their ABHA Personal Health Record.
   Each is independently toggleable; audio-explained for low-literacy patients
   (reuse Module A's TTS service).
3. **Secure processing** — all voice/document data is encrypted in transit and at rest;
   PII fields get field-level encryption via `backend/utils/security.py`.
4. **FHIR mapping** — the confirmed summary (Module C output) is mapped into FHIR
   resources, at minimum:
   * `Patient`
   * `Condition` (chief complaint / diagnoses)
   * `MedicationStatement` (from drug & allergy history + documents)
   * `Observation` (investigation values)
5. **Push to ABDM Health Information Exchange + hospital HIS** via FHIR APIs.
6. **Session termination** — once submitted, clear temporary session buffers; nothing
   sensitive should linger outside the persisted, consented record.
7. **Retry/resilience** — `abdm_sync_worker.py` retries failed pushes with backoff
   rather than silently dropping data.

## Consent Record Shape (suggested)

```json
{
  "patient_id": "p123",
  "consents": {
    "data_capture": true,
    "share_with_his": true,
    "link_abha_phr": true
  },
  "consent_language": "hi",
  "timestamp": "2026-09-11T10:00:00Z",
  "audit_trail_id": "ct-9911"
}
```

## Build Order

1. Mock ABHA verification (hardcode a sandbox response) + consent capture UI/API.
2. Build the FHIR bundle mapping from a sample confirmed summary.
3. Push to ABDM **sandbox** (https://sandbox.abdm.gov.in/) and confirm round-trip.
4. Add the retry worker + audit trail + field-level encryption.
5. Wire the "push confirmation" signal back to the Physician Console so the demo can
   visibly show a successful ABHA link.

## Compliance Checklist

* [ ] No sensitive data logged in plaintext (check `backend/utils/logger.py` usage).
* [ ] Consent is granular and revocable, not a single "I agree" checkbox.
* [ ] Temporary session data is actually deleted post-submission, not just unlinked.
* [ ] Every ABDM/HIS push has an append-only audit trail entry.
