"""
Module   : OCR Extractor
Owner    : Document AI Engineer
Purpose  : Runs OCR engine on preprocessed image.
"""

import os
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    confidence: float
    language: str
    words: list[dict] | None = None


class BaseOCRExtractor(ABC):
    @abstractmethod
    def extract(self, image: "np.ndarray", lang: str = "hin+eng") -> OCRResult:
        pass


def _get_pytesseract():
    """Lazy import of pytesseract with fallback."""
    try:
        import pytesseract
        return pytesseract
    except ImportError as e:
        raise RuntimeError("pytesseract not available. Install with: pip install pytesseract") from e


class TesseractExtractor(BaseOCRExtractor):
    def __init__(self, tesseract_cmd: str | None = None):
        pytesseract = _get_pytesseract()
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif os.getenv("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")

    def extract(self, image: "np.ndarray", lang: str = "hin+eng") -> OCRResult:
        import numpy as np

        pytesseract = _get_pytesseract()

        if image is None or image.size == 0:
            return OCRResult(text="", confidence=0.0, language=lang)

        data = pytesseract.image_to_data(
            image, lang=lang, output_type=pytesseract.Output.DICT
        )

        words = []
        confidences = []
        for i in range(len(data["text"])):
            if data["text"][i].strip():
                words.append({
                    "text": data["text"][i],
                    "conf": float(data["conf"][i]),
                    "bbox": (data["left"][i], data["top"][i], data["width"][i], data["height"][i]),
                })
                confidences.append(float(data["conf"][i]))

        text = " ".join(w["text"] for w in words)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return OCRResult(text=text, confidence=avg_conf, language=lang, words=words)


class VisionAPIExtractor(BaseOCRExtractor):
    """Stub for cloud Vision API (Google/Azure/AWS)."""

    def __init__(self, api_key: str | None = None, endpoint: str | None = None):
        self.api_key = api_key or os.getenv("VISION_API_KEY")
        self.endpoint = endpoint or os.getenv("VISION_API_URL")

    def extract(self, image: "np.ndarray", lang: str = "hin+eng") -> OCRResult:
        # TODO: Implement actual Vision API call
        # For now, fall back to Tesseract
        warnings.warn("VisionAPIExtractor not implemented, falling back to Tesseract")
        fallback = TesseractExtractor()
        return fallback.extract(image, lang)


def get_extractor(provider: str | None = None) -> BaseOCRExtractor:
    """Factory function to get OCR extractor based on provider."""
    provider = provider or os.getenv("OCR_PROVIDER", "tesseract")
    if provider == "vision_api":
        return VisionAPIExtractor()
    return TesseractExtractor()


async def extract_text(
    image_bytes: bytes,
    lang: str = "hin+eng",
    provider: str | None = None,
    preprocess_level: str = "medium",
) -> OCRResult:
    """
    High-level function: preprocess image -> extract text.

    Returns OCRResult with text, confidence, and word-level details.
    """
    from .preprocessor import preprocess

    processed = preprocess(image_bytes, level=preprocess_level)
    extractor = get_extractor(provider)
    return extractor.extract(processed, lang=lang)


__all__ = [
    "OCRResult",
    "BaseOCRExtractor",
    "TesseractExtractor",
    "VisionAPIExtractor",
    "get_extractor",
    "extract_text",
]