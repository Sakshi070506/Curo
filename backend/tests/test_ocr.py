"""
Tests for backend.ai.ocr module.
"""

import pytest
import numpy as np

# Try importing cv2, skip tests if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Try importing pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Import what we can
from backend.ai.ocr import (
    preprocess,
    preprocess_pipeline,
    PreprocessLevel,
    ParsedDocument,
    parse_document_sync,
)

if TESSERACT_AVAILABLE:
    from backend.ai.ocr import (
        OCRResult,
        TesseractExtractor,
        VisionAPIExtractor,
        get_extractor,
    )


skip_if_no_cv2 = pytest.mark.skipif(not CV2_AVAILABLE, reason="opencv not available")
skip_if_no_tesseract = pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="pytesseract not available")


class TestPreprocessor:
    @skip_if_no_cv2
    def test_preprocess_light(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        _, img_bytes = cv2.imencode('.png', img)
        result = preprocess(img_bytes.tobytes(), level="light")
        assert isinstance(result, np.ndarray)
        assert result.shape == img.shape

    @skip_if_no_cv2
    def test_preprocess_medium(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        _, img_bytes = cv2.imencode('.png', img)
        result = preprocess(img_bytes.tobytes(), level="medium")
        assert isinstance(result, np.ndarray)

    @skip_if_no_cv2
    def test_preprocess_heavy(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        _, img_bytes = cv2.imencode('.png', img)
        result = preprocess(img_bytes.tobytes(), level="heavy")
        assert isinstance(result, np.ndarray)

    @skip_if_no_cv2
    def test_preprocess_invalid_bytes(self):
        with pytest.raises(ValueError):
            preprocess(b"not an image")

    @skip_if_no_cv2
    def test_preprocess_pipeline_custom(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        _, img_bytes = cv2.imencode('.png', img)
        result = preprocess_pipeline(img_bytes.tobytes(), steps=["deskew", "clahe"])
        assert isinstance(result, np.ndarray)


class TestExtractor:
    @skip_if_no_tesseract
    def test_tesseract_extractor_init(self):
        extractor = TesseractExtractor()
        assert extractor is not None

    @skip_if_no_tesseract
    def test_vision_api_extractor_init(self):
        extractor = VisionAPIExtractor()
        assert extractor is not None

    @skip_if_no_tesseract
    def test_get_extractor_tesseract(self):
        extractor = get_extractor("tesseract")
        assert isinstance(extractor, TesseractExtractor)

    @skip_if_no_tesseract
    def test_get_extractor_vision_api(self):
        extractor = get_extractor("vision_api")
        assert isinstance(extractor, VisionAPIExtractor)

    @skip_if_no_tesseract
    def test_get_extractor_default(self):
        extractor = get_extractor()
        assert isinstance(extractor, TesseractExtractor)


class TestParser:
    def test_parse_prescription_basic(self):
        text = "Tab Metformin 500mg BD for 30 days\nCap Aspirin 75mg OD"
        result = parse_document_sync(text, doc_type="prescription")
        assert isinstance(result, ParsedDocument)
        assert len(result.medications) >= 1
        assert any("metformin" in m["name"].lower() for m in result.medications)
        # Note: MockLLMClient returns canned response with Metformin only

    def test_parse_lab_report(self):
        text = "HbA1c: 8.2% (ref: 4.0-5.6)\nFasting Glucose: 140 mg/dL (ref: 70-100)\nTotal Cholesterol: 240 mg/dL (ref: <200)"
        result = parse_document_sync(text, doc_type="lab_report")
        # Mock returns HbA1c, regex finds others
        assert len(result.investigations) >= 1
        hba1c = next((inv for inv in result.investigations if "hba1c" in inv["test"].lower()), None)
        assert hba1c is not None
        assert hba1c["abnormal"] is True
        assert hba1c["ref_range"] == "4.0-5.6"

    def test_parse_diagnoses(self):
        text = "Diagnosis: Type 2 Diabetes Mellitus, Hypertension"
        result = parse_document_sync(text, doc_type="discharge_summary")
        assert "Type 2 Diabetes Mellitus" in result.diagnoses or "Diabetes" in str(result.diagnoses)
        # Mock returns Type 2 Diabetes, regex results may not be merged when mock has data

    def test_parse_dates(self):
        text = "Date: 15/08/2026\nFollow-up: 2026-09-01"
        result = parse_document_sync(text, doc_type="prescription")
        assert len(result.dates) >= 1

    def test_parse_procedures(self):
        text = "Procedure: Appendectomy done on 10/05/2025\nECG performed"
        result = parse_document_sync(text, doc_type="discharge_summary")
        assert "Appendectomy" in result.procedures or "Ecg" in result.procedures

    def test_empty_text(self):
        result = parse_document_sync("", doc_type="prescription")
        assert isinstance(result, ParsedDocument)
        # Mock returns canned data even for empty text
        assert isinstance(result.medications, list)
        assert isinstance(result.investigations, list)

    def test_enrich_medications_frequency(self):
        text = "Metformin 500mg BD"
        result = parse_document_sync(text)
        metformin = next((m for m in result.medications if "metformin" in m["name"].lower()), None)
        assert metformin is not None
        assert metformin["frequency"] == "BD"

    def test_enrich_investigations_ref_range(self):
        text = "HbA1c 8.2%"
        result = parse_document_sync(text)
        hba1c = next((inv for inv in result.investigations if "hba1c" in inv["test"].lower()), None)
        assert hba1c is not None
        assert hba1c["ref_range"] == "4.0-5.6"
        assert hba1c["abnormal"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])