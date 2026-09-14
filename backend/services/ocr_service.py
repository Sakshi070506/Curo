"""
Module   : OCR Orchestrator
Owner    : Document AI Engineer
Purpose  : Runs preprocessing + OCR + parsing pipeline end-to-end for uploaded
           medical documents (prescriptions, lab reports, discharge summaries).

Design notes
------------
- Each stage (preprocess / extract / parse) is a swappable component so
  backend/ai/ocr/{preprocessor,extractor,parser}.py can plug in more advanced
  implementations later without changing OCRService's public API.
- Falls back gracefully: TesseractExtractor is used when Pillow + pytesseract +
  the tesseract binary are available; otherwise MockExtractor keeps the pipeline
  runnable and testable.
- Supports multi-page documents (list of images in, one combined parsed result out).
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Protocol

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None  # type: ignore

try:
    import pytesseract
except ImportError:
    pytesseract = None


# ---------------------------------------------------------------------------
# Stage protocols
# ---------------------------------------------------------------------------
class Preprocessor(Protocol):
    def process(self, image_bytes: bytes) -> bytes: ...


class Extractor(Protocol):
    def extract_text(self, image_bytes: bytes, language_hint: str = "eng") -> "ExtractionResult": ...


class Parser(Protocol):
    def parse(self, text: str) -> "ParsedDocument": ...


@dataclass
class ExtractionResult:
    text: str
    confidence: float


@dataclass
class ParsedDocument:
    document_type: str
    date: Optional[str]
    diagnoses: List[str] = field(default_factory=list)
    medications: List[Dict] = field(default_factory=list)
    investigations: List[Dict] = field(default_factory=list)
    raw_text: str = ""


# ---------------------------------------------------------------------------
# Default implementations
# ---------------------------------------------------------------------------
class DefaultPreprocessor:
    """Grayscale + contrast-normalize using Pillow, ahead of OCR.

    Passes bytes through unchanged in two cases:
    (a) Pillow isn't installed, or
    (b) the bytes aren't a decodable image at all — this lets MockExtractor
        consume plain UTF-8 "documents" directly in tests without a real image.

    NOTE: a real scanned/handwritten document (the actual target of Module B)
    benefits from denoising; a median filter was tried here and found to blur
    thin printed/handwritten strokes enough to hurt Tesseract's accuracy on
    typical prescription-photo resolutions, so it's deliberately left out.
    If you add denoising back for noisy real-world scans, verify it against a
    sample of real prescription photos before/after — synthetic clean text
    doesn't show the regression.
    """

    def process(self, image_bytes: bytes) -> bytes:
        if Image is None:
            return image_bytes
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except Exception:
            return image_bytes
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


class TesseractExtractor:
    """Real OCR via pytesseract, when the tesseract binary is installed."""

    def extract_text(self, image_bytes: bytes, language_hint: str = "eng") -> ExtractionResult:
        if Image is None or pytesseract is None:
            raise RuntimeError("Pillow and pytesseract are required for TesseractExtractor.")
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang=language_hint)
        # image_to_string doesn't return a single confidence value; a fuller
        # implementation should use image_to_data and average per-word confidences.
        return ExtractionResult(text=text, confidence=0.75 if text.strip() else 0.0)


class MockExtractor:
    """Deterministic offline OCR stand-in for tests/dev without a scanned document
    on hand. Interprets the input bytes as UTF-8 text directly (the 'image' the
    test hands in already *is* the text to be parsed) — useful for testing the
    parser stage in isolation from real OCR."""

    def extract_text(self, image_bytes: bytes, language_hint: str = "eng") -> ExtractionResult:
        try:
            text = image_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        return ExtractionResult(text=text, confidence=0.99 if text else 0.0)


DATE_PATTERN = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b")
MED_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z]+(?:in|ol|ide|one|ine|azole|cillin|mycin))\s+(\d+\s?mg)\s*(OD|BD|TDS|QID|once daily|twice daily)?",
    re.IGNORECASE,
)
LAB_VALUE_PATTERN = re.compile(
    r"\b([A-Za-z][A-Za-z0-9 ]{2,20}?)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(mg/dl|g/dl|%|mmol/l|/ul|iu/l)?"
    r"\s*(?:\(?ref(?:erence)?[:\s]*([\d.]+\s*-\s*[\d.]+)\)?)?",
    re.IGNORECASE,
)


class RuleBasedParser:
    """Regex-based clinical entity extraction — adequate for a hackathon MVP.
    backend/ai/ocr/parser.py can later replace this with an NER model without
    changing OCRService's public API."""

    def parse(self, text: str) -> ParsedDocument:
        return ParsedDocument(
            document_type=self._guess_document_type(text),
            date=self._extract_date(text),
            diagnoses=self._extract_diagnoses(text),
            medications=self._extract_medications(text),
            investigations=self._extract_investigations(text),
            raw_text=text,
        )

    @staticmethod
    def _guess_document_type(text: str) -> str:
        lowered = text.lower()
        if "lab" in lowered or "reference range" in lowered or " ref " in lowered:
            return "lab_report"
        if "discharge" in lowered:
            return "discharge_summary"
        return "prescription"

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        match = DATE_PATTERN.search(text)
        if not match:
            return None
        day, month, year = match.groups()
        if len(year) == 2:
            year = "20" + year
        try:
            return datetime(int(year), int(month), int(day)).date().isoformat()
        except ValueError:
            return None

    @staticmethod
    def _extract_medications(text: str) -> List[Dict]:
        results = []
        for match in MED_PATTERN.finditer(text):
            name, dosage, frequency = match.groups()
            results.append({"name": name, "dosage": dosage, "frequency": frequency or ""})
        return results

    @staticmethod
    def _extract_investigations(text: str) -> List[Dict]:
        results = []
        for match in LAB_VALUE_PATTERN.finditer(text):
            test, value, unit, ref_range = match.groups()
            test = test.strip()
            if len(test) < 3 or test.lower() in {"the", "and", "for", "dx"}:
                continue
            abnormal = False
            if ref_range:
                try:
                    low, high = (float(x.strip()) for x in ref_range.split("-"))
                    abnormal = not (low <= float(value) <= high)
                except ValueError:
                    pass
            results.append({
                "test": test,
                "value": float(value),
                "unit": unit or "",
                "ref_range": ref_range or "",
                "abnormal": abnormal,
            })
        return results

    @staticmethod
    def _extract_diagnoses(text: str) -> List[str]:
        diagnoses = []
        for line in text.splitlines():
            lowered = line.lower().strip()
            if lowered.startswith("dx:") or lowered.startswith("diagnosis:"):
                diagnoses.append(line.split(":", 1)[1].strip())
        return diagnoses


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class OCRService:
    def __init__(
        self,
        preprocessor: Optional[Preprocessor] = None,
        extractor: Optional[Extractor] = None,
        parser: Optional[Parser] = None,
    ):
        self.preprocessor = preprocessor or DefaultPreprocessor()
        self.extractor = extractor or self._default_extractor()
        self.parser = parser or RuleBasedParser()

    @staticmethod
    def _default_extractor() -> Extractor:
        if Image is not None and pytesseract is not None:
            return TesseractExtractor()
        return MockExtractor()

    def process_document(self, image_bytes: bytes, language_hint: str = "eng") -> ParsedDocument:
        preprocessed = self.preprocessor.process(image_bytes)
        extraction = self.extractor.extract_text(preprocessed, language_hint)
        return self.parser.parse(extraction.text)

    def process_multi_page(self, pages: List[bytes], language_hint: str = "eng") -> ParsedDocument:
        """Combine OCR text from multiple pages before parsing, so entities that
        span a page break (e.g. a lab table) still get extracted correctly."""
        combined_text = []
        for page_bytes in pages:
            preprocessed = self.preprocessor.process(page_bytes)
            extraction = self.extractor.extract_text(preprocessed, language_hint)
            combined_text.append(extraction.text)
        return self.parser.parse("\n".join(combined_text))

    @staticmethod
    def build_timeline(parsed_documents: List[ParsedDocument]) -> List[Dict]:
        """Sort parsed documents chronologically for the patient timeline
        (docs/module-B-document-digitization.md: 'Chronological organization')."""
        ordered = sorted(parsed_documents, key=lambda d: d.date or "0000-00-00")
        return [
            {
                "type": doc.document_type,
                "date": doc.date,
                "diagnoses": doc.diagnoses,
                "medications": doc.medications,
                "investigations": doc.investigations,
            }
            for doc in ordered
        ]


if __name__ == "__main__":
    sample_text = (
        "Discharge Summary dated 05/08/2026\n"
        "Dx: Type 2 Diabetes Mellitus\n"
        "Metformin 500mg BD\n"
        "HbA1c: 8.2 % (ref 4.0-5.6)\n"
    ).encode("utf-8")

    service = OCRService(extractor=MockExtractor())
    result = service.process_document(sample_text)
    print(result)
