# API Reference

Base URL (dev): `http://localhost:8000/api`

All endpoints (except `/health`) require a valid session/auth token unless noted.
Request/response bodies should mirror `backend/database/schemas.py` — that file is the
single source of truth; update this doc whenever a schema changes.

---

## Auth & Identity — owner: Backend Engineer

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register a new patient (name, DOB, phone) |
| POST | `/auth/login` | Login existing patient |
| POST | `/auth/abha-verify` | Verify/link ABHA ID via ABDM sandbox |

## Conversation Engine — owner: Conversation AI Engineer

| Method | Path | Description |
|---|---|---|
| POST | `/history/start-session` | Start a new interview session (returns `session_id`, first question) |
| POST | `/history/answer` | Submit an answer (voice transcript or tapped option) → returns next question or completion |
| GET | `/history/session/{id}` | Get full session state / captured answers so far |
| POST | `/history/redflag-check` | (internal) Run red-flag classifier on latest answer |

**Request example — `/history/answer`:**
```json
{
  "session_id": "abc123",
  "question_id": "chief_complaint",
  "answer_text": "chest pain since morning",
  "input_mode": "voice"
}
```

## Document Digitization — owner: Document AI Engineer

| Method | Path | Description |
|---|---|---|
| POST | `/documents/upload` | Upload a scanned image/PDF of a prior document |
| POST | `/documents/extract` | Trigger OCR + entity extraction on an uploaded document |
| GET | `/documents/{patient_id}/timeline` | Get chronologically ordered digitized documents |

## Summary — owner: Summary/LLM Engineer

| Method | Path | Description |
|---|---|---|
| GET | `/summary/{patient_id}` | Get the AI-generated structured case summary |
| POST | `/summary/{patient_id}/confirm` | Physician confirms/finalizes the summary |
| PATCH | `/summary/{patient_id}/edit` | Physician edits specific summary fields |

## Consent & ABDM — owner: Integration Engineer

| Method | Path | Description |
|---|---|---|
| POST | `/consent/grant` | Record granular patient consent |
| POST | `/abdm/push-fhir` | Push finalized summary as a FHIR bundle to ABDM/HIS |
| GET | `/abdm/status/{patient_id}` | Check ABDM push/sync status |

## Triage — owner: Backend Engineer

| Method | Path | Description |
|---|---|---|
| POST | `/triage/alert` | Raise a red-flag priority alert (called internally by red-flag service) |
| GET | `/triage/queue` | Get the current priority queue for staff dashboard |

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness/readiness probe → `{"status": "ok"}` |

---

## Adding a New Endpoint

1. Define request/response schema in `backend/database/schemas.py`.
2. Add the route in the relevant `backend/api/*.py` file (keep it thin — call a
   `services/*.py` function for the actual logic).
3. Document it here.
4. Add/update the matching call in `frontend/src/services/*.js`.
