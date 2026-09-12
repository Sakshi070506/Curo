"""
Module   : Shared LLM Prompts
Owner    : Summary/LLM Engineer
Purpose  : Central prompt library. Versioned task registry.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptSpec:
    task: str
    version: str
    system: str
    user_template: str
    output_schema: dict[str, Any]
    notes: str = ""


PROMPT_TASKS: dict[str, PromptSpec] = {
    "summarize_case": PromptSpec(
        task="summarize_case",
        version="1.0.0",
        system=(
            "You are a clinical summarization engine. Fuse the patient interview JSON and "
            "digitized document timeline into a single structured case summary. "
            "Output ONLY valid JSON matching the schema. "
            "If a field has no source data, output \"not mentioned\" — never guess or invent. "
            "Every field must be traceable to interview or documents. "
            "No free-form narrative; use the exact section keys below."
        ),
        user_template=(
            "INTERVIEW JSON:\n{interview_json}\n\n"
            "DOCUMENT TIMELINE JSON:\n{document_json}\n\n"
            "Produce the structured summary now."
        ),
        output_schema={
            "chief_complaint": "string",
            "hpi": {
                "onset": "string",
                "character": "string",
                "radiation": "string",
                "severity": "string",
                "exacerbating": "string",
                "relieving": "string",
            },
            "past_medical_history": "array[string]",
            "drug_allergy_history": "array[string]",
            "family_history": "array[string]",
            "personal_history": "object",
            "review_of_systems": "object",
            "prior_investigations": "array[object]",
            "ayush": "object",
            "source_attribution": "string",
        },
        notes=(
            "Align with Module C standard format: Chief Complaint → HPI → PMH/PSH → "
            "Drug & Allergy → Family → Personal → ROS → Prior Investigations → "
            "[AYUSH] Dashavidha Pariksha. Final schema alignment pending "
            "backend/database/schemas.py (AGENTS §3)."
        ),
    ),
    "generate_next_question": PromptSpec(
        task="generate_next_question",
        version="1.0.0",
        system=(
            "You drive an adaptive clinical interview (SOCRATES framework). "
            "Given the chief complaint and previous Q&A, return the NEXT single question. "
            "Output ONLY valid JSON. No extra text."
        ),
        user_template=(
            "Chief complaint: {chief_complaint}\n"
            "Previous Q&A:\n{previous_qa}\n\n"
            "Return the next SOCRATES probe question."
        ),
        output_schema={
            "question_id": "string",
            "question_text": "string",
            "options": "array[string]",
            "branch": "string",
        },
    ),
    "extract_entities": PromptSpec(
        task="extract_entities",
        version="1.0.0",
        system=(
            "Extract SOCRATES slots from patient free-text answer. "
            "Output ONLY valid JSON with the exact keys below. "
            "If a slot is not mentioned, use \"not mentioned\"."
        ),
        user_template="Patient answer: {answer_text}\n\nExtract SOCRATES entities.",
        output_schema={
            "site": "string",
            "onset": "string",
            "character": "string",
            "radiation": "string",
            "associated": "array[string]",
            "timing": "string",
            "exacerbating": "string",
            "relieving": "string",
            "severity": "string",
        },
    ),
    "extract_document_entities": PromptSpec(
        task="extract_document_entities",
        version="1.0.0",
        system=(
            "Parse clinical entities from OCR text of a medical document "
            "(prescription, lab report, discharge summary). "
            "Output ONLY valid JSON. Use \"not mentioned\" for absent fields. "
            "Extract: diagnoses, medications (name, dosage, frequency, duration), "
            "investigations (test, value, unit, ref_range, abnormal), procedures, dates."
        ),
        user_template="Document OCR text:\n{ocr_text}\n\nExtract structured entities.",
        output_schema={
            "diagnoses": "array[string]",
            "medications": "array[object]",
            "investigations": "array[object]",
            "procedures": "array[string]",
            "dates": "array[string]",
        },
    ),
    "classify_redflag": PromptSpec(
        task="classify_redflag",
        version="1.0.0",
        system=(
            "Classify whether the patient's symptom description indicates a "
            "red-flag/emergency condition requiring immediate triage escalation. "
            "Output ONLY valid JSON."
        ),
        user_template="Patient answer: {answer_text}\n\nClassify for red-flag.",
        output_schema={
            "is_redflag": "boolean",
            "severity": "string",  # critical | high | moderate | low
            "symptoms": "array[string]",
            "recommended_action": "string",
        },
    ),
}


def get_prompt(task: str) -> PromptSpec:
    if task not in PROMPT_TASKS:
        raise KeyError(f"Unknown prompt task: {task}")
    return PROMPT_TASKS[task]


def render(task: str, **vars: Any) -> str:
    spec = get_prompt(task)
    return spec.user_template.format(**vars)


__all__ = ["PromptSpec", "PROMPT_TASKS", "get_prompt", "render"]