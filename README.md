# 🩺 Curo — AI-Powered Patient Case-Taking Software

**SIH Problem Statement:** Patient Case-Taking Software
**Theme:** MedTech / BioTech / HealthTech

Curo is a patient-facing software platform that conducts a structured **clinical
history interview** (voice + touch), **digitizes prior medical documents** (OCR), and
generates a **physician-ready case summary** — all before the patient enters the
consultation room. It integrates with the **ABDM (ABHA)** ecosystem and hospital
**HIS/EMR** systems via FHIR, and includes an **AYUSH mode** for Ayurvedic OPDs.

> 👥 **New to this repo?** Read [`AGENTS.md`](./AGENTS.md) first — it tells you which
> module is yours, which files you own, and what to build first.

---

## 1. The Problem

Indian OPDs see 4,000–10,000 patients/day with 2–5 minute consultations. Doctors have
no time to properly elicit history, and patients' prior paper records are unstructured
and unread. See [`docs/problem-statement.md`](./docs/problem-statement.md) for the full
background brief.

## 2. What We're Building

| Module | What it does | Docs |
|---|---|---|
| **A — Conversation Engine** | Adaptive voice+touch clinical interview | [`docs/module-A-conversation-engine.md`](./docs/module-A-conversation-engine.md) |
| **B — Document Digitization** | OCR + entity extraction from prior records | [`docs/module-B-document-digitization.md`](./docs/module-B-document-digitization.md) |
| **C — Summary Generator** | Fuses interview + documents into a case summary | [`docs/module-C-summary-generator.md`](./docs/module-C-summary-generator.md) |
| **D — Consent & ABDM** | Consent capture, FHIR push to HIS/ABHA | [`docs/module-D-consent-abdm.md`](./docs/module-D-consent-abdm.md) |

Full system diagram and data flows: [`docs/architecture.md`](./docs/architecture.md)
Full API reference: [`docs/api-docs.md`](./docs/api-docs.md)

## 3. Repo Structure

```
medikiosk-case-taking-system/
├── AGENTS.md                # 👈 Who owns what — read this first
├── README.md                # This file
├── docs/                    # Architecture, API docs, module specs, setup guide
├── backend/                 # FastAPI backend (API, services, AI, DB, workers)
│   ├── api/                 # Route handlers (thin — no business logic)
│   ├── services/            # Business logic layer
│   ├── ai/                  # NLU, OCR, RAG, summary generation
│   ├── database/            # SQLAlchemy models + schemas + migrations
│   ├── workers/             # Background jobs (triage alerts, ABDM sync)
│   ├── utils/                # Logging, security, validators
│   └── tests/                # Backend tests
├── frontend/                # React kiosk/web app
│   └── src/
│       ├── pages/            # Screen-level components (one per patient-journey step)
│       ├── components/       # Reusable UI pieces
│       ├── services/         # API call wrappers
│       ├── hooks/             # Custom React hooks
│       └── context/           # Global state
└── scripts/                  # DB setup, ontology seeding, worker runner
```

Every file in `backend/` and `frontend/src/` starts with a header comment stating its
**Module**, **Owner (role)**, **Purpose**, and a **TODO** list — that's your task list.

## 4. Tech Stack

* **Frontend:** React + Vite
* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL + pgvector (for RAG)
* **ASR/TTS:** Bhashini / AI4Bharat (Indian languages)
* **OCR:** Tesseract / Vision API (tuned for handwritten Indian prescriptions)
* **LLM:** Used for adaptive dialogue + summary synthesis (ontology-constrained prompts)
* **Interoperability:** FHIR APIs, ABDM Health Information Exchange, ABHA auth
* **Security:** DPDP Act 2023-compliant encryption + consent audit trail

## 5. Getting Started

### Prerequisites
* Python 3.11+
* Node.js 18+
* PostgreSQL 15+ (with `pgvector` extension available)

### Backend setup
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
cp ../.env.example ../.env   # fill in DB_URL, ASR/OCR/ABDM keys
python ../scripts/setup_db.py
python ../scripts/seed_clinical_ontology.py
uvicorn main:app --reload --port 8000
```

### Frontend setup
```bash
cd frontend
npm install
npm run dev
```
The frontend dev server proxies `/api` calls to `http://localhost:8000` (see
`frontend/vite.config.js`).

### Running background workers
```bash
python scripts/run_workers.py
```

## 6. Environment Variables

See [`.env.example`](./.env.example) for the full list: database URL, ASR/TTS provider
keys, OCR provider keys, ABDM sandbox credentials, and JWT secret.

## 7. Contributing / Team Workflow

1. Check [`AGENTS.md`](./AGENTS.md) for your assigned module and files.
2. Create a branch: `feature/<module>-<short-description>`.
3. Keep business logic in `services/` — API route files in `api/` should stay thin.
4. Open a PR against `main`; at least one teammate from a different module reviews it
   (catches integration issues early — see "Cross-Module Contracts" in `AGENTS.md`).
5. Update the relevant `docs/module-*.md` file if your module's behavior changes.

## 8. Build Order (Hackathon Sprint Plan)

See the **Sprint Plan** table in [`AGENTS.md`](./AGENTS.md) for the day-by-day build
order and dependencies between modules.

## 9. Demo Flow

1. Select language → consent (audio-guided)
2. Voice + touch interview → show red-flag trigger on a sample "chest pain" case
3. Upload a sample prescription/lab report → OCR digitization + timeline
4. AI-generated case summary → physician edits/confirms
5. FHIR push confirmation + ABHA record link
6. Triage dashboard receives the priority alert in real time

---

## License
TBD by team (suggested: MIT for hackathon submission, revisit for production).
