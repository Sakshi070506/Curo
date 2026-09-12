"""
Module   : OCR Package
Owner    : Document AI Engineer
Purpose  : OCR pipeline exports.
"""

from .preprocessor import preprocess, preprocess_pipeline, PreprocessLevel
from .extractor import OCRResult, BaseOCRExtractor, TesseractExtractor, VisionAPIExtractor, get_extractor, extract_text
from .parser import ParsedDocument, parse_document, parse_document_sync

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