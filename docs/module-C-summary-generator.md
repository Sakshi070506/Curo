# Module C — Structured History Summary Generator

**Owner:** Summary/LLM Engineer
**Code:** `backend/api/summary.py`, `backend/ai/summary/`
**Frontend:** `frontend/src/pages/SummaryReview.jsx`, `PhysicianConsole.jsx`, `components/SummaryEditor.jsx`

## Goal

Fuse the conversational history (Module A output) and the digitized documents (Module B
output) into a single, concise, **physician-editable** case summary in a standard
format — displayed the moment the patient enters the consultation room.

## Standard Format

```
Chief Complaint
History of Present Illness (HPI)
Past Medical / Surgical History
Drug & Allergy History
Family History
Personal History
Review of Systems (ROS)
Prior Investigations Summary
[AYUSH-only] Dashavidha Pariksha Summary
```

## Key Behaviors

1. **Never autonomous** — this module produces a *draft*. The physician always
   accepts/amends/rejects before it's saved (`POST /api/summary/{id}/confirm` or
   `PATCH /api/summary/{id}/edit`).
2. **Grounded synthesis** — every field in the summary should be traceable back to
   either the interview session or a specific digitized document. Avoid the LLM
   inventing details not present in the source data (a hallucinated allergy is
   dangerous). Consider having `synthesizer.py` attach a `source` field per line.
3. **Bilingual output** — patient-facing confirmation is read back in their language
   (via TTS, reusing Module A's TTS service); physician-facing text is English/Hindi.
4. **Fast physician read** — the console should let a doctor absorb the whole picture
   in seconds; prioritize good formatting over cleverness.

## Data Flow

```
Module A output (session JSON) ─┐
                                  ├─→ synthesizer.py (LLM, template-constrained) → draft summary
Module B output (documents JSON)─┘
                                  ↓
                     Patient confirmation (audio playback)
                                  ↓
                     Physician review (SummaryEditor.jsx)
                                  ↓
                     Confirmed summary → Module D (FHIR push)
```

## Prompt Design Notes (`backend/ai/common/prompts.py`, `ai/summary/templates.py`)

* Constrain the LLM to only the standard-format sections above — no free-form additions.
* Feed it the raw structured JSON from Modules A & B, not prose, to reduce drift.
* Include an explicit instruction to mark any field as `"not mentioned"` rather than
  guessing, when source data is missing.

## Build Order

1. Hard-coded template rendering from the two input JSONs (no LLM yet) — proves the
   plumbing works end-to-end.
2. Swap in LLM-based synthesis for the free-text HPI narrative.
3. Add source-attribution per field.
4. Add bilingual rendering + TTS playback for patient confirmation.
5. Build the physician edit UI with section-level editing.

## Testing Notes

* Test with: (a) a patient with only conversational history, no documents, (b) only
  documents, no conversation (edge case), (c) both — confirm the summary handles all
  three gracefully.
