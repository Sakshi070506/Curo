import pytest
from services.fhir_service import build_fhir_bundle, push_to_abdm, FHIRMappingError
from services.ocr_service import OCRService, MockExtractor, RuleBasedParser


# ---------------------------------------------------------------------------
# FHIR
# ---------------------------------------------------------------------------
SAMPLE_SUMMARY = {
    "patient": {"id": "p123", "name": "Test Patient", "abha_id": "12-3456-7890-1234", "gender": "male", "dob": "1990-01-01"},
    "chief_complaint": "chest pain",
    "diagnoses": ["suspected angina"],
    "medications": [{"name": "Aspirin", "dosage": "75mg", "frequency": "OD"}],
    "investigations": [{"test": "ECG", "value": 1, "abnormal": True}],
}


def test_build_fhir_bundle_structure():
    bundle = build_fhir_bundle(SAMPLE_SUMMARY)
    assert bundle["resourceType"] == "Bundle"
    resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Patient" in resource_types
    assert "Condition" in resource_types
    assert "MedicationStatement" in resource_types
    assert "Observation" in resource_types


def test_build_fhir_bundle_includes_chief_complaint_as_condition():
    bundle = build_fhir_bundle(SAMPLE_SUMMARY)
    conditions = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Condition"]
    condition_texts = [c["code"]["text"] for c in conditions]
    assert "chest pain" in condition_texts
    assert "suspected angina" in condition_texts


def test_build_fhir_bundle_requires_patient():
    with pytest.raises(FHIRMappingError):
        build_fhir_bundle({"chief_complaint": "fever"})


def test_build_fhir_bundle_requires_patient_id():
    with pytest.raises(FHIRMappingError):
        build_fhir_bundle({"patient": {"name": "No ID Patient"}})


def test_push_to_abdm_dry_run_without_credentials(monkeypatch):
    monkeypatch.delenv("ABDM_CLIENT_ID", raising=False)
    monkeypatch.delenv("ABDM_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("ABDM_BASE_URL", raising=False)
    bundle = build_fhir_bundle(SAMPLE_SUMMARY)
    result = push_to_abdm(bundle)
    assert result.success is True
    assert result.dry_run is True


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------
SAMPLE_DOC_TEXT = (
    "Discharge Summary dated 05/08/2026\n"
    "Dx: Type 2 Diabetes Mellitus\n"
    "Metformin 500mg BD\n"
    "HbA1c: 8.2 % (ref 4.0-5.6)\n"
)


def test_ocr_service_with_mock_extractor_end_to_end():
    service = OCRService(extractor=MockExtractor())
    result = service.process_document(SAMPLE_DOC_TEXT.encode("utf-8"))
    assert result.date == "2026-08-05"
    assert "Type 2 Diabetes Mellitus" in result.diagnoses
    assert any(m["name"].lower() == "metformin" for m in result.medications)
    assert any(i["test"].strip().lower() == "hba1c" for i in result.investigations)
    abnormal_flags = [i["abnormal"] for i in result.investigations if i["test"].strip().lower() == "hba1c"]
    assert abnormal_flags == [True]  # 8.2 is outside 4.0-5.6


def test_ocr_parser_flags_normal_value_as_not_abnormal():
    parser = RuleBasedParser()
    doc = parser.parse("Glucose: 90 mg/dl (ref 70-110)\n")
    assert doc.investigations[0]["abnormal"] is False


def test_ocr_multi_page_combines_text():
    service = OCRService(extractor=MockExtractor())
    page1 = b"Dx: Hypertension\n"
    page2 = b"Amlodipine 5mg OD\n"
    result = service.process_multi_page([page1, page2])
    assert "Hypertension" in result.diagnoses
    assert any(m["name"].lower() == "amlodipine" for m in result.medications)


def test_ocr_build_timeline_sorts_chronologically():
    service = OCRService(extractor=MockExtractor())
    doc_later = service.process_document(b"Report dated 10/09/2026\nDx: Follow-up\n")
    doc_earlier = service.process_document(b"Report dated 01/01/2026\nDx: Initial visit\n")
    timeline = OCRService.build_timeline([doc_later, doc_earlier])
    assert timeline[0]["date"] == "2026-01-01"
    assert timeline[1]["date"] == "2026-09-10"


def test_ocr_service_with_real_tesseract_if_available():
    """Bonus check: if Pillow + pytesseract + the tesseract binary are all
    available (as they are in this environment), the DEFAULT extractor should be
    TesseractExtractor and should manage to read simple rendered text."""
    try:
        from PIL import Image, ImageDraw
        import pytesseract  # noqa: F401
    except ImportError:
        pytest.skip("Pillow/pytesseract not installed in this environment")

    img = Image.new("RGB", (600, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "Dx: Hypertension", fill="black")
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    service = OCRService()  # default extractor -> should pick Tesseract
    result = service.process_document(buf.getvalue())
    assert "ypertension" in result.raw_text  # tolerate minor OCR noise on 'H'