# 🩺 MediKiosk — AI-Powered Patient Case-Taking Software — CORE BUILD

## 📌 Project Summary

We are building an **AI-powered clinical history-taking & document digitization platform** (SIH problem statement: *Patient Case-Taking Software*) that:

* Conducts structured clinical history interviews via **voice + touch**
* Digitizes prior prescriptions, lab reports & discharge summaries via **OCR**
* Auto-generates a **physician-ready structured case summary**
* Flags **red-flag / emergency symptoms** for priority triage
* Pushes the final record to **Hospital HIS/EMR + ABDM (ABHA)**
* Supports an **AYUSH history mode** (Dashavidha Pariksha) for Ayurvedic OPDs

---

# 🏆 Core USPs

| # | USP                          | Description                                              |
| - | ----------------------------- | --------------------------------------------------------- |
| 1 | Conversational History Engine | Adaptive voice+touch interview (SOCRATES-style probing)    |
| 2 | Multilingual ASR/TTS          | Hindi, English & regional languages, low-literacy friendly |
| 3 | Document Digitization         | OCR + entity extraction from handwritten/printed records   |
| 4 | Auto Case Summary             | Chief complaint → HPI → PMH → ROS, physician-editable       |
| 5 | Red-Flag Triage Alerts        | Emergency symptom detection → priority queue                |
| 6 | ABDM/ABHA Native Integration  | FHIR-based push to HIS + Personal Health Record             |
| 7 | AYUSH Mode                    | Dashavidha Pariksha capture for Ayurvedic OPDs               |

---

# 🔌 System Architecture

```
                        Patient-Facing Kiosk / Web / Tablet App
                                       ↓
                              API Gateway / Backend
                                       ↓
   ┌───────────────┬───────────────┬───────────────┬───────────────┐
   ↓               ↓               ↓               ↓               ↓
Conversation    Document AI     Clinical         Consent/ABDM    HIS/EMR
Engine (ASR/    (OCR+NER)       Ontology &       Layer (FHIR,    Connector
NLU/TTS)                        Summary Engine   ABHA)
   ↓               ↓               ↓               ↓               ↓
   └────────→ Clinical Data Store (SQL + Vector Store) ←───────────┘
                                       ↓
                        Structured History Summary Generator
                                       ↓
                   Physician Console  +  Triage/Alert Dashboard
```

---

# 🗣️ 1. Conversational Multimodal History Engine (Module A)

## Flow

```
Patient selects language → Consent (audio-guided)
        ↓
Chief complaint captured (voice or tap)
        ↓
Dialogue Manager (clinical ontology + SOCRATES framework)
        ↓
Adaptive follow-up questions (branch on complaint + prior answers)
        ↓
Dual-mode answer capture (ASR transcript OR touch selection)
        ↓
Red-flag classifier runs on every turn
        ↓
   ┌─── Red flag detected? ───┐
   YES                        NO
   ↓                           ↓
Priority alert to triage   Continue interview → Review of Systems
        ↓                           ↓
                    Structured history JSON saved
```

## Features

* Adaptive branching questionnaire (chief-complaint-driven decision tree + LLM fallback)
* Dual input: every question answerable by speech OR tap
* AYUSH mode: extended Dashavidha Pariksha (Prakriti, Vikriti, Sara, Samhanana, Pramana, Satmya, Sattva, Ahara Shakti, Vyayama Shakti, Vaya) + Ahara-Vihara
* Red-flag detection model (rule-based + classifier ensemble) → instant triage escalation
* TTS-based audio prompts for low-literacy/elderly patients

---

# 📄 2. Medical Document Digitization & Intelligence (Module B)

## Flow

```
Patient uploads/scans document (prescription / lab report / discharge summary)
        ↓
Image preprocessing (deskew, denoise, contrast normalize)
        ↓
OCR Engine (multilingual, handwritten + printed)
        ↓
Clinical NER (diagnoses, drugs, dosages, investigation values, procedures)
        ↓
Chronological sorting (date extraction & timeline ordering)
        ↓
Abnormal-value & drug-interaction flagging
        ↓
Structured document record stored + linked to patient timeline
```

## Features

* Multilingual, handwriting-tolerant OCR pipeline
* Entity extraction: diagnosis, medication + dosage, lab values + reference ranges, procedure history
* Automatic chronological medical timeline construction
* Abnormal lab-value highlighting + basic drug-interaction check (links to RAG module below)

---

# 🧾 3. Structured History Summary Generator (Module C)

## Purpose

Fuse conversational history + digitized documents into a single physician-ready summary, editable before saving.

## Flow

```
Conversational History JSON  +  Digitized Document Timeline
                    ↓
        Summary Synthesis Engine (LLM, constrained to clinical template)
                    ↓
Standard Format: Chief Complaint → HPI → PMH/PSH → Drug & Allergy →
                  Family → Personal → ROS → Prior Investigations
                    ↓
Bilingual rendering (patient audio confirmation | physician EN/HI text)
                    ↓
Physician Console: Accept / Amend / Reject
                    ↓
Final record saved → pushed downstream (Module D)
```

## Features

* Never autonomous — physician always confirms/edits before it's saved
* Bilingual output (local-language audio for patient, EN/HI text for physician)
* Displayed on consultation screen the moment patient is called in

---

# 🔐 4. Consent, Privacy & ABDM Integration (Module D)

## Flow

```
ABHA ID / Aadhaar-based patient authentication
        ↓
Granular, revocable consent capture (audio-explained for low literacy)
        ↓
Secure processing (encrypted in transit + at rest)
        ↓
Structured summary → FHIR bundle
        ↓
Push to Hospital HIS/EMR  +  ABDM Health Information Exchange (ABHA PHR)
        ↓
Session data purge (temporary buffers cleared post-submission)
```

## Features

* DPDP Act 2023 & ABDM consent-framework compliant
* FHIR-based interoperability with HIS/EMR
* Session-scoped temporary storage only — no residual PII after submission

---

# 🧠 5. Clinical Knowledge / RAG Layer (Supporting AI Layer)

## Purpose

* Ground the dialogue manager & document parser in verified clinical/drug knowledge
* Support drug-interaction and abnormal-value checks

## Flow

```
Extracted entity / symptom → Query → Embedding
        ↓
Vector Search over clinical knowledge base (SNOMED/ICD mapped)
        ↓
Top-k relevant clinical concepts
        ↓
Used to (a) drive adaptive questioning (b) validate extracted drug/lab entities
```

## Table

```
clinical_knowledge:
- concept_id (SNOMED/ICD code)
- concept_name
- category (symptom / drug / lab / procedure)
- related_questions
- embedding
```

---

# 🔌 6. API System

## Endpoints

### Auth & Identity

```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/abha-verify
```

### Conversation Engine

```
POST /api/history/start-session
POST /api/history/answer
GET  /api/history/session/{id}
POST /api/history/redflag-check
```

### Document Digitization

```
POST /api/documents/upload
GET  /api/documents/{patient_id}/timeline
POST /api/documents/extract
```

### Summary & Physician Console

```
GET  /api/summary/{patient_id}
POST /api/summary/{patient_id}/confirm
PATCH /api/summary/{patient_id}/edit
```

### Consent & ABDM

```
POST /api/consent/grant
POST /api/abdm/push-fhir
GET  /api/abdm/status/{patient_id}
```

### Triage / Alerts

```
POST /api/triage/alert
GET  /api/triage/queue
```

---

# 🗂️ Folder Structure

```
medikiosk-case-taking-system/
│
├── README.md
├── .env
├── .env.example
├── requirements.txt
├── package.json
│
├── backend/                          # 🔌 Core Backend (FastAPI)
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── history.py               # Conversation engine endpoints
│   │   ├── documents.py             # OCR / digitization endpoints
│   │   ├── summary.py               # Case summary endpoints
│   │   ├── consent.py               # Consent + ABDM endpoints
│   │   ├── triage.py                # Red-flag / priority alerts
│   │   └── health.py
│   │
│   ├── services/
│   │   ├── asr_service.py           # Speech-to-text (Bhashini/AI4Bharat)
│   │   ├── tts_service.py           # Text-to-speech prompts
│   │   ├── dialogue_manager.py      # Adaptive questioning logic
│   │   ├── redflag_service.py       # Emergency symptom classifier
│   │   ├── ocr_service.py           # Document OCR pipeline
│   │   ├── fhir_service.py          # ABDM/HIS FHIR integration
│   │   └── notification_service.py  # Triage alerts to staff
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── models.py                 # patients, sessions, documents, summaries
│   │   ├── schemas.py
│   │   └── migrations/
│   │
│   ├── ai/
│   │   ├── nlu/
│   │   │   ├── intent_classifier.py
│   │   │   ├── entity_extractor.py
│   │   │   └── clinical_ontology.py  # SOCRATES / Dashavidha Pariksha trees
│   │   │
│   │   ├── ocr/
│   │   │   ├── preprocessor.py
│   │   │   ├── extractor.py
│   │   │   └── parser.py             # diagnoses, drugs, lab values
│   │   │
│   │   ├── rag/
│   │   │   ├── embedding.py
│   │   │   ├── retrieval.py
│   │   │   └── interaction_checker.py
│   │   │
│   │   ├── summary/
│   │   │   ├── synthesizer.py        # LLM-based summary generation
│   │   │   └── templates.py          # standard clinical format templates
│   │   │
│   │   └── common/
│   │       ├── prompts.py
│   │       └── utils.py
│   │
│   ├── workers/
│   │   ├── triage_alert_worker.py
│   │   └── abdm_sync_worker.py
│   │
│   ├── utils/
│   │   ├── logger.py
│   │   ├── security.py               # encryption, consent audit trail
│   │   └── validators.py
│   │
│   └── tests/
│       ├── test_history_api.py
│       ├── test_ocr.py
│       └── test_fhir_push.py
│
├── frontend/                          # 🎨 Kiosk / Web App (React)
│   ├── public/
│   │   └── index.html
│   │
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── LanguageSelect.jsx
│   │   │   ├── ConsentScreen.jsx
│   │   │   ├── HistoryInterview.jsx  # voice + touch Q&A
│   │   │   ├── DocumentUpload.jsx
│   │   │   ├── SummaryReview.jsx
│   │   │   └── PhysicianConsole.jsx
│   │   │
│   │   ├── components/
│   │   │   ├── VoiceInputBar.jsx
│   │   │   ├── TouchOptionCard.jsx
│   │   │   ├── DocumentScanBox.jsx
│   │   │   ├── TimelineView.jsx
│   │   │   ├── RedFlagBanner.jsx
│   │   │   └── SummaryEditor.jsx
│   │   │
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── historyService.js
│   │   │   ├── documentService.js
│   │   │   └── abdmService.js
│   │   │
│   │   ├── hooks/
│   │   │   ├── useVoiceCapture.js
│   │   │   └── useSessionState.js
│   │   │
│   │   ├── context/
│   │   │   └── SessionContext.jsx
│   │   │
│   │   └── styles/
│   │       └── global.css
│   │
│   └── vite.config.js
│
├── scripts/
│   ├── seed_clinical_ontology.py
│   ├── run_workers.py
│   └── setup_db.py
│
└── docs/
    ├── architecture.md
    ├── api-docs.md
    └── setup-guide.md
```

---

# ⚙️ Tech Stack

* **Frontend (Kiosk/Web/Tablet):** React + Vite, Web Speech API fallback
* **Backend:** FastAPI (Python) for AI-heavy services
* **Database:** PostgreSQL (structured) + Vector store (pgvector/FAISS) for RAG
* **ASR/TTS:** Bhashini / AI4Bharat models (Indian languages)
* **OCR:** Vision API / Tesseract fine-tuned for handwritten Indian prescriptions
* **LLM:** Constrained dialogue + summarization (clinical-ontology grounded prompts)
* **Interoperability:** FHIR APIs, ABDM Health Information Exchange, ABHA auth
* **Security:** DPDP Act 2023-compliant encryption at rest & in transit, consent audit trail

---

# ⚠️ Build Order

```
1. Consent + ABHA auth flow
2. Conversational history engine (text-first, then add ASR/TTS)
3. Red-flag detection layer
4. OCR + document digitization pipeline
5. Clinical RAG / knowledge layer
6. Structured summary generator
7. Physician console (review/edit/confirm)
8. FHIR/ABDM + HIS push integration
9. Triage dashboard & alerts
10. UI polish + accessibility pass (low-literacy, multilingual)
```

---

# 🎯 Demo Flow

1. Patient selects language → grants consent (audio-guided)
2. Voice + touch interview captures chief complaint & HPI (show red-flag trigger on a sample "chest pain" case)
3. Upload a sample prescription/lab report → show OCR digitization + timeline
4. AI generates structured case summary → physician edits/confirms
5. Show FHIR push confirmation + ABHA record link
6. Show triage dashboard receiving the priority alert in real time

---

# 🔥 Why This Structure Works

### ✅ Separation of Concerns
Conversation AI ≠ Document AI ≠ Summary Engine ≠ Integration Layer — each module independently testable and demoable.

### ✅ Hackathon Friendly
Each module (A–D) maps directly to a jury-facing demo beat.

### ✅ Scalable Beyond Hackathon
Can extend to: mobile app for pre-visit history capture, more regional languages, deeper AYUSH modules, EHR analytics for hospital admin.

---

## 🚀 Ready for Implementation
