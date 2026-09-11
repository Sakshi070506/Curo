# Module B — Medical Document Digitization & Intelligence

**Owner:** Document AI Engineer
**Code:** `backend/api/documents.py`, `backend/services/ocr_service.py`, `backend/ai/ocr/`
**Frontend:** `frontend/src/pages/DocumentUpload.jsx`, `components/DocumentScanBox.jsx`, `components/TimelineView.jsx`

## Goal

Let the patient upload/scan prior prescriptions, lab reports, and discharge summaries,
and turn them into structured, dated, physician-usable data — without any manual
transcription.

## Pipeline

```
Upload (image/PDF)
    → preprocessor.py   (deskew, denoise, contrast normalize — OpenCV)
    → extractor.py       (OCR: Tesseract / Vision API, multilingual, handwriting-tolerant)
    → parser.py           (clinical NER: diagnoses, drugs+dosages, lab values+ranges, dates, procedures)
    → chronological sort  (order documents/entries by extracted date)
    → abnormal-value flagging (compare lab values to reference ranges)
    → interaction_checker.py (backend/ai/rag/ — cross-check extracted drugs)
```

## Key Behaviors

1. **Multi-document, multi-page support** — a patient may upload several documents in
   one session; each needs independent processing but a combined timeline.
2. **Multilingual OCR** — Hindi, English, and at least one additional regional script
   should be supported or gracefully degrade (return raw text + low-confidence flag).
3. **Handwriting tolerance** — printed prescriptions are the easy case; handwritten
   ones are the differentiator. Budget extra time/testing here.
4. **Entity extraction targets:**
   * Diagnoses (free text or coded)
   * Medications: name, dosage, frequency, duration
   * Investigations: test name, value, unit, reference range
   * Procedures/surgeries with approximate date
5. **Chronological organization** — every extracted document/entry gets a best-effort
   date; sort into a single patient timeline.
6. **Abnormal-value highlighting** — flag any lab value outside its reference range for
   physician attention (don't interpret clinically — just flag).

## Data Contract (→ consumed by Module C)

```json
{
  "patient_id": "p123",
  "documents": [
    {
      "document_id": "d1",
      "type": "lab_report",
      "date": "2026-08-01",
      "diagnoses": [],
      "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BD"}],
      "investigations": [{"test": "HbA1c", "value": 8.2, "unit": "%", "ref_range": "4.0-5.6", "abnormal": true}],
      "raw_ocr_confidence": 0.87
    }
  ]
}
```

## Build Order

1. Preprocessing + OCR on a printed sample doc → raw text out.
2. Parser: regex/NER for drug names + dosages (highest value, most tractable).
3. Date extraction + chronological sort.
4. Lab value + reference range extraction, abnormal flagging.
5. Handwritten document tuning (stretch goal if time allows).
6. Drug-interaction check hookup (`backend/ai/rag/interaction_checker.py`).

## Testing Notes

* Build a small fixture set (3–5 sample prescriptions/lab reports, scanned/photographed
  at realistic quality) and keep it in `backend/tests/` fixtures — use these for every
  OCR change so you can see regressions immediately.
