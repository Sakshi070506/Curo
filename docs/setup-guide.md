# Setup Guide

## 1. Prerequisites

* Python 3.11+
* Node.js 18+
* PostgreSQL 15+ with the `pgvector` extension installable
* (Optional, for full functionality) API keys/access for:
  * Bhashini / AI4Bharat ASR & TTS
  * OCR provider (Tesseract is free/local; Vision API needs a key)
  * ABDM sandbox credentials (https://sandbox.abdm.gov.in/)

## 2. Clone & Configure

```bash
git clone <your-repo-url>
cd medikiosk-case-taking-system
cp .env.example .env
# edit .env with your local DB URL and any provider keys you have
```

## 3. Database

```bash
# create the database (adjust to your local Postgres setup)
createdb medikiosk

# enable pgvector (run inside psql, connected to the medikiosk db)
psql medikiosk -c "CREATE EXTENSION IF NOT EXISTS vector;"

# run the setup script (creates tables via SQLAlchemy models)
python scripts/setup_db.py

# seed the clinical question tree / knowledge base
python scripts/seed_clinical_ontology.py
```

## 4. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/api/health` — should return `{"status": "ok"}`.

## 5. Frontend

```bash
cd frontend
npm install
npm run dev
```
Visit the URL Vite prints (typically `http://localhost:5173`). API calls to `/api/*`
are proxied to the backend (see `frontend/vite.config.js`).

## 6. Background Workers (optional for local dev)

```bash
python scripts/run_workers.py
```
Runs the triage-alert and ABDM-sync workers so red-flag alerts and FHIR retries
actually process outside of the request/response cycle.

## 7. Running Tests

```bash
cd backend
pytest tests/
```

## 8. Common Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| Backend fails to start, DB connection error | `.env` `DATABASE_URL` wrong or DB not running | Check Postgres is running, verify credentials |
| `pgvector` extension error | Extension not installed on Postgres server | Install `postgresql-<version>-pgvector` package, retry `CREATE EXTENSION` |
| Frontend 404s on `/api/*` calls | Backend not running or wrong proxy port | Confirm backend is on `:8000`, matches `vite.config.js` proxy |
| ASR/OCR calls fail | Missing provider API key | Add key to `.env`, or fall back to local Tesseract/browser Web Speech API for demo |
