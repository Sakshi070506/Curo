"""
Module   : OCR Package
Owner    : Document AI Engineer
Purpose  : OCR pipeline exports.
"""

from .extractor import (
    BaseOCRExtractor,
    OCRResult,
    TesseractExtractor,
    VisionAPIExtractor,
    extract_text,
    get_extractor,
)
from .parser import ParsedDocument, parse_document, parse_document_sync
from .preprocessor import PreprocessLevel, preprocess, preprocess_pipeline

__all__ = [
    "preprocess",
    "preprocess_pipeline",
    "PreprocessLevel",
    "OCRResult",
    "BaseOCRExtractor",
    "TesseractExtractor",
    "VisionAPIExtractor",
    "get_extractor",
    "extract_text",
    "ParsedDocument",
    "parse_document",
    "parse_document_sync",
]
