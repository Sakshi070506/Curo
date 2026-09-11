# AGENTS.md — Team Roles, Ownership & Task Board

This file exists so anyone who clones this repo — teammate or AI coding assistant —
immediately knows **who/what owns each folder**, **what needs to be built**, and **in
what order**. Assign a real teammate's name next to each role below once your team is
finalized.

---

## 1. Roles ("Agents") & Module Ownership

| Role (Agent)                     | Assigned To | Owns (folders)                                                        | Primary Responsibility |
|-----------------------------------|-------------|-------------------------------------------------------------------------|--------------------------|
| **Backend Lead**                  | _TBD_       | `backend/main.py`, `backend/config.py`, `backend/dependencies.py`, `backend/utils/` | App skeleton, DB wiring, cross-cutting concerns, code review gatekeeper |
| **Conversation AI Engineer**      | _TBD_       | `backend/api/history.py`, `backend/services/asr_service.py`, `backend/services/tts_service.py`, `backend/services/dialogue_manager.py`, `backend/services/redflag_service.py`, `backend/ai/nlu/` | Voice+touch adaptive interview engine (Module A) |
| **Document AI Engineer**          | _TBD_       | `backend/api/documents.py`, `backend/services/ocr_service.py`, `backend/ai/ocr/` | OCR + document digitization pipeline (Module B) |
| **ML / RAG Engineer**             | _TBD_       | `backend/ai/rag/`, `backend/ai/nlu/clinical_ontology.py`, `scripts/seed_clinical_ontology.py` | Clinical knowledge base, vector search, drug-interaction checks |
| **Summary / LLM Engineer**        | _TBD_       | `backend/api/summary.py`, `backend/ai/summary/` | Fuses interview + documents into the physician-ready summary (Module C) |
| **Integration Engineer**          | _TBD_       | `backend/api/consent.py`, `backend/services/fhir_service.py`, `backend/workers/abdm_sync_worker.py`, `backend/utils/security.py` | Consent capture, FHIR/ABDM/HIS integration (Module D) |
| **Database Engineer**             | _TBD_       | `backend/database/`, `scripts/setup_db.py` | Schema design, migrations, pgvector setup |
| **Backend Engineer (generalist)** | _TBD_       | `backend/api/auth.py`, `backend/api/triage.py`, `backend/services/notification_service.py`, `backend/workers/triage_alert_worker.py` | Auth, triage queue, notifications |
| **Frontend Lead**                 | _TBD_       | `frontend/src/App.jsx`, `frontend/src/main.jsx`, `frontend/src/context/`, `frontend/src/styles/` | App shell, routing, global state, design system |
| **Frontend Engineer(s)**          | _TBD_       | `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/services/`, `frontend/src/hooks/` | Kiosk screens for the patient journey |
| **QA / Testing**                  | _TBD_       | `backend/tests/` | Test coverage across modules, integration testing before demo |

> One person can hold more than one role on a small team — the split above is meant to
> make hand-off points explicit, not to require 11 separate people.

---

## 2. Every Code File Is Self-Documenting

Every file under `backend/` and `frontend/src/` already contains a header like this:

```python
"""
Module   : Dialogue Manager
Owner    : Conversation AI Engineer
Purpose  : Drives the adaptive clinical interview.
"""

# TODO: Implement SOCRATES branching for symptom-based complaints
# TODO: Implement AYUSH Dashavidha Pariksha branch
# TODO: Maintain session state machine
```

**Workflow:** open your assigned folder → read each file's header → the TODOs *are*
your task list. Check them off / delete them as you implement, and replace the stub
with real code.

---

## 3. Cross-Module Contracts (read this before you start)

These are the hand-off points between roles — get alignment on these early so modules
don't block each other:

| Contract | Between | What must be agreed |
|---|---|---|
| **History session JSON schema** | Conversation AI Engineer ↔ Summary/LLM Engineer | Shape of the captured interview data (chief complaint, HPI fields, ROS, AYUSH fields) |
| **Document extraction schema** | Document AI Engineer ↔ Summary/LLM Engineer | Shape of extracted diagnoses/drugs/lab values/dates |
| **Red-flag event payload** | Conversation AI Engineer ↔ Backend Engineer (triage) | What fields a red-flag alert carries (symptom, severity, patient_id, timestamp) |
| **FHIR bundle input** | Summary/LLM Engineer ↔ Integration Engineer | Final summary schema that gets mapped into FHIR resources |
| **API request/response shapes** | All backend roles ↔ Frontend Engineers | Keep `backend/database/schemas.py` as the single source of truth; frontend `services/*.js` should mirror it exactly |
| **Clinical ontology / question tree** | ML/RAG Engineer ↔ Conversation AI Engineer | `clinical_ontology.py` is the shared source both rely on |

**Rule of thumb:** if your change touches a schema listed above, ping the other owner
before merging.

---

## 4. Sprint Plan / Build Order

| Phase | Tasks | Owners | Exit Criteria |
|---|---|---|---|
| **0. Setup (Day 1)** | Repo scaffold ✅, DB schema, `.env` config, consent + ABHA auth stub | Backend Lead, Database Engineer, Integration Engineer | Backend boots, DB connected, login/consent works end-to-end (mocked ABHA) |
| **1. Core Interview (Day 1–2)** | Text-first dialogue manager, question tree, session API | Conversation AI Engineer | Can complete a full text-based interview via API/Postman |
| **2. Red-Flag Layer (Day 2)** | Rule-based red-flag detection + triage alert + dashboard stub | Conversation AI Engineer, Backend Engineer | Sample "chest pain" case triggers a visible alert |
| **3. Document Pipeline (Day 2–3)** | Preprocessing → OCR → entity parsing → timeline | Document AI Engineer | Upload a sample prescription → structured JSON out |
| **4. Voice Layer (Day 3)** | Plug ASR/TTS into the interview flow | Conversation AI Engineer | Interview completable by voice, not just text |
| **5. Knowledge/RAG Layer (Day 3)** | Seed clinical knowledge base, vector search, drug-interaction check | ML/RAG Engineer | Retrieval returns relevant concepts for a sample symptom |
| **6. Summary Generator (Day 3–4)** | Fuse interview + documents → structured summary, physician edit UI | Summary/LLM Engineer, Frontend Engineer | Summary renders correctly for a full sample patient |
| **7. FHIR/ABDM Push (Day 4)** | Map summary → FHIR bundle → push to sandbox HIS/ABDM | Integration Engineer | Push succeeds against sandbox with a visible confirmation |
| **8. Frontend Polish (Day 4–5)** | All kiosk screens wired to real APIs, accessibility pass | Frontend Lead + Engineers | Full patient journey walkable on a tablet-sized screen |
| **9. Integration Testing + Demo Prep (Day 5)** | End-to-end run-through, fix seams between modules | QA, all owners | Demo flow (README §9) runs without manual intervention |

Adjust day numbers to your actual hackathon timeline — the **order/dependencies**
matter more than the exact days.

---

## 5. Definition of Done (per module)

* Code matches the file's header **Purpose**, all TODOs addressed or consciously deferred.
* Endpoint(s) tested via `backend/tests/` or manually via Postman/curl.
* Any schema you introduce or change is reflected in `backend/database/schemas.py` and
  the relevant `docs/module-*.md`.
* No secrets committed — everything sensitive goes through `.env` (see `.env.example`).

---

## 6. Communication

* Daily 10-minute sync: what's blocked, what schema changed, what's demo-ready.
* Use PR descriptions to call out any cross-module contract changes (see §3).
* Keep `docs/architecture.md` updated if the actual system diverges from the plan —
  judges will read this.
