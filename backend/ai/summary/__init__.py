"""
Module   : Summary Package
Owner    : Summary/LLM Engineer
Purpose  : Structured summary generation exports.
"""

from .synthesizer import SummaryResult, confirm, edit, synthesize, synthesize_sync
from .templates import (
    HPI_LABELS_EN,
    HPI_LABELS_HI,
    HPI_SUBSECTIONS,
    SECTION_LABELS_EN,
    SECTION_LABELS_HI,
    SECTIONS,
    render_patient_audio,
    render_template,
    validate_summary_structure,
)

__all__ = [
    "SummaryResult",
    "synthesize",
    "synthesize_sync",
    "confirm",
    "edit",
    "SECTIONS",
    "SECTION_LABELS_EN",
    "SECTION_LABELS_HI",
    "HPI_SUBSECTIONS",
    "HPI_LABELS_EN",
    "HPI_LABELS_HI",
    "render_template",
    "render_patient_audio",
    "validate_summary_structure",
]
