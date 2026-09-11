# Module A — Conversational Multimodal History Engine

**Owner:** Conversation AI Engineer
**Code:** `backend/api/history.py`, `backend/services/{asr,tts,dialogue_manager,redflag}_service.py`, `backend/ai/nlu/`
**Frontend:** `frontend/src/pages/HistoryInterview.jsx`, `components/VoiceInputBar.jsx`, `components/TouchOptionCard.jsx`, `components/RedFlagBanner.jsx`

## Goal

Conduct a structured clinical history interview through natural voice conversation
**and** guided touchscreen interaction, adapting questions to the patient's chief
complaint the way a physician would.

## Key Behaviors

1. **Chief complaint capture** — first open question, voice or tap.
2. **Adaptive branching (SOCRATES)** — for symptom-based complaints, probe:
   **S**ite, **O**nset, **C**haracter, **R**adiation, **A**ssociated symptoms,
   **T**iming, **E**xacerbating/relieving factors, **S**everity.
3. **Dual-mode input** — every question must be answerable by speaking OR tapping a
   pre-defined option; never force one modality.
4. **AYUSH mode** — if the OPD is Ayurvedic, extend the interview with Dashavidha
   Pariksha: Prakriti, Vikriti, Sara, Samhanana, Pramana, Satmya, Sattva, Ahara Shakti,
   Vyayama Shakti, Vaya + Ahara-Vihara (diet/lifestyle).
5. **Red-flag detection** — every answer is checked against a red-flag rule set
   (e.g., chest pain + dyspnoea, sudden severe headache, one-sided weakness). A positive
   match immediately fires a priority alert (`POST /api/triage/alert`) instead of
   waiting for the interview to finish.
6. **Review of Systems (ROS)** — after HPI, run a shortened systemic checklist.

## Session State Machine (suggested)

```
START → LANGUAGE_SELECTED → CONSENT_GRANTED → CHIEF_COMPLAINT
    → HPI_LOOP (branches per SOCRATES / red-flag check each turn)
    → PAST_HISTORY → DRUG_ALLERGY_HISTORY → FAMILY_HISTORY → PERSONAL_HISTORY
    → ROS → (AYUSH_MODE ? DASHAVIDHA_PARIKSHA : skip) → COMPLETE
```
Implement this in `dialogue_manager.py`; persist state per `session_id` so a patient
can pause/resume (e.g., stepping away to scan documents in Module B).

## Data Contract (→ consumed by Module C)

The finished session should serialize to roughly:

```json
{
  "session_id": "abc123",
  "language": "hi",
  "chief_complaint": "chest pain",
  "hpi": { "onset": "...", "character": "...", "radiation": "...", "severity": "7/10" },
  "past_medical_history": [...],
  "drug_allergy_history": [...],
  "family_history": [...],
  "personal_history": {...},
  "review_of_systems": {...},
  "ayush": { "prakriti": "...", "agni": "...", "...": "..." },
  "red_flags_triggered": []
}
```
Agree on the exact field names with the Summary/LLM Engineer before finalizing.

## Build Order

1. Text-only version of the state machine (no ASR/TTS) — validate the branching logic.
2. Wire up red-flag detection on each answer.
3. Add ASR (speech-to-text) and TTS (audio prompts).
4. Add AYUSH branch.
5. Add resume-session support.

## Testing Notes

* Test with at least one "emergency" scripted case (should trigger red flag) and one
  routine case (should complete normally) — see `backend/tests/test_history_api.py`.
