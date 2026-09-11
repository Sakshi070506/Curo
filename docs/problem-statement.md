# Problem Statement — Patient Case-Taking Software

**Theme:** MedTech / BioTech / HealthTech

## Background

History taking — eliciting a patient's presenting complaints, history of present
illness, past medical/surgical history, drug and allergy history, family and personal
history, and a review of systems — is the single most important diagnostic activity in
clinical medicine. Classical teaching holds a well-conducted history yields the correct
diagnosis in 70–80% of cases, before examination or investigation.

India's public hospital OPDs register 4,000–10,000 patients/day, with doctor-patient
consultation time frequently 2–5 minutes — among the shortest globally. Within this
window the physician must elicit history, examine, review prior records, diagnose,
counsel, and prescribe — resulting in systematic under-elicitation, missed
comorbidities, and diagnostic error.

AYUSH institutions face an additional layer: Ayurvedic history-taking (Trividha,
Ashtavidha, Dashavidha Pariksha) requires assessing Prakriti, Vikriti, Agni, Koshtha,
Ahara-Vihara, Nidana, and Samprapti — far more extensive than allopathic intake, and
effectively impossible to capture manually within OPD time constraints.

## Documentation & Records Fragmentation

Patients typically carry physical, unstructured, handwritten, multi-language prior
records. There is no point-of-entry mechanism to digitize and organize these before the
consultation. The Ayushman Bharat Digital Mission (ABDM) — ABHA IDs, Health Information
Exchange, FHIR standards — solves the *infrastructure* problem, but the "first-mile"
problem (capturing structured history and digitizing documents *before* the encounter)
remains unsolved.

## The Problem, Precisely

> There is no purpose-built, patient-facing software platform that enables patients to
> independently and comprehensively record their medical history — through both natural
> spoken conversation and guided touchscreen interaction — and simultaneously digitize
> their existing physical medical documents, generating a structured, physician-ready
> clinical history summary that integrates with the hospital information system and the
> ABDM ecosystem before the patient enters the consultation room.

## Why Existing Solutions Fall Short

* **Hospital registration systems** capture only demographic/appointment data — no
  clinical history, no document processing.
* **Mobile health apps / tele-triage chatbots** require smartphone literacy, stable
  connectivity, and pre-visit enrolment — excluding elderly, rural, low-literacy, and
  first-visit patients who form the bulk of government OPD load.
* **Manual nurse-led triage desks** don't scale to 5,000+ daily patients and reintroduce
  the same time/transcription bottleneck.
* **Generic document scanners** digitize images but don't extract, structure, or link
  clinical content to a history or ABHA record.

## Specific Challenges a Solution Must Overcome

1. Multilingual, multi-accent voice capture in noisy hospital environments.
2. Accessibility for low-literacy/elderly users with zero training required.
3. Accurate conversion of free-form narration into standardized clinical history
   (+ AYUSH Dashavidha Pariksha where applicable).
4. Reliable OCR + structuring of handwritten/printed medical documents.
5. DPDP Act 2023 and ABDM consent-framework compliance for sensitive health data.

## Expected Solution — MediKiosk

An AI-powered clinical history software platform where any patient can:

1. Record a comprehensive medical history via voice + touch.
2. Scan/digitize existing physical medical documents.
3. Receive/produce a structured, physician-ready clinical history summary.
4. Have that summary pushed to the hospital HIS and linked to their ABHA record —
   all before the consultation, with minimal staff assistance.

See [`architecture.md`](./architecture.md) for the full technical design.
