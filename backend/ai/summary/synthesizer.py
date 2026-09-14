"""
Module   : Summary Synthesizer
Owner    : Summary/LLM Engineer
Purpose  : LLM-based fusion of interview + documents into final summary.
"""

import json
from dataclasses import dataclass
from typing import Any

from backend.ai.common import MockLLMClient, get_prompt, parse_llm_json
from .templates import SECTIONS, validate_summary_structure


@dataclass
class SummaryResult:
    summary: dict[str, Any]
    source_attribution: dict[str, str]
    missing_sections: list[str]


async def synthesize(
    interview_json: dict[str, Any],
    document_json: dict[str, Any],
    lang: str = "en",
    client: MockLLMClient | None = None,
) -> SummaryResult:
    """
    Fuse conversational interview JSON and digitized documents into structured summary.

    Args:
        interview_json: Output from Module A (dialogue_manager session)
        document_json: Output from Module B (document timeline)
        lang: Language for output ('en' or 'hi')
        client: LLM client (defaults to MockLLMClient)

    Returns:
        SummaryResult with summary dict, source attribution, and missing sections
    """
    if client is None:
        client = MockLLMClient()

    spec = get_prompt("summarize_case")

    interview_str = json.dumps(interview_json, ensure_ascii=False)
    document_str = json.dumps(document_json, ensure_ascii=False)

    user_prompt = spec.user_template.format(
        interview_json=interview_str,
        document_json=document_str,
    )

    messages = [
        {"role": "system", "content": spec.system},
        {"role": "user", "content": user_prompt},
    ]

    raw_response = await client.chat(messages, task="summarize_case")
    parsed = parse_llm_json(raw_response)

    summary = _ensure_all_sections(parsed)
    
    # Merge document data into summary for fields not populated by LLM
    summary = _merge_document_data(summary, document_json)
    
    source_attr = _build_source_attribution(parsed, interview_json, document_json)
    missing = validate_summary_structure(summary)

    return SummaryResult(
        summary=summary,
        source_attribution=source_attr,
        missing_sections=missing,
    )


def _merge_document_data(summary: dict[str, Any], document_json: dict[str, Any]) -> dict[str, Any]:
    """Merge document data into summary for fields not populated by LLM."""
    documents = document_json.get("documents", [])
    if not documents:
        return summary
    
    for doc in documents:
        # Merge diagnoses into past_medical_history
        if doc.get("diagnoses"):
            existing = set(summary.get("past_medical_history", []))
            for diag in doc["diagnoses"]:
                if diag not in existing:
                    summary.setdefault("past_medical_history", []).append(diag)
        
        # Merge medications into drug_allergy_history
        if doc.get("medications"):
            existing = set(summary.get("drug_allergy_history", []))
            for med in doc["medications"]:
                med_name = med.get("name", "")
                if med_name and med_name not in existing:
                    summary.setdefault("drug_allergy_history", []).append(med_name)
        
        # Merge investigations into prior_investigations
        if doc.get("investigations"):
            summary.setdefault("prior_investigations", []).extend(doc["investigations"])
    
    return summary


def _ensure_all_sections(parsed: dict[str, Any]) -> dict[str, Any]:
    """Ensure all required sections exist with defaults."""
    defaults = {
        "chief_complaint": "not mentioned",
        "hpi": {
            "onset": "not mentioned",
            "character": "not mentioned",
            "radiation": "not mentioned",
            "severity": "not mentioned",
            "exacerbating": "not mentioned",
            "relieving": "not mentioned",
        },
        "past_medical_history": [],
        "past_surgical_history": [],
        "drug_allergy_history": [],
        "family_history": [],
        "personal_history": {},
        "review_of_systems": {},
        "prior_investigations": [],
        "ayush": {},
        "source_attribution": "interview+documents",
    }

    result = defaults.copy()
    result.update(parsed)

    if "hpi" in parsed and isinstance(parsed["hpi"], dict):
        result["hpi"].update(parsed["hpi"])

    if "ayush" in parsed and isinstance(parsed["ayush"], dict):
        result["ayush"].update(parsed["ayush"])

    return result


def _build_source_attribution(
    parsed: dict[str, Any],
    interview_json: dict[str, Any],
    document_json: dict[str, Any],
) -> dict[str, str]:
    """Build field-level source attribution."""
    attribution = {}

    interview_keys = set(_flatten_keys(interview_json))
    document_keys = set(_flatten_keys(document_json))

    for section, value in parsed.items():
        if section == "source_attribution":
            continue

        section_sources = []
        if _has_overlap(section, interview_keys):
            section_sources.append("interview")
        if _has_overlap(section, document_keys):
            section_sources.append("documents")

        if not section_sources:
            section_sources.append("llm_inference")

        attribution[section] = "+".join(section_sources)

    return attribution


def _flatten_keys(obj: Any, prefix: str = "") -> list[str]:
    """Flatten nested dict/list keys for comparison."""
    keys = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            keys.append(new_prefix)
            keys.extend(_flatten_keys(v, new_prefix))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            keys.extend(_flatten_keys(item, f"{prefix}[{i}]"))
    return keys


def _has_overlap(section: str, source_keys: set[str]) -> bool:
    """Check if section has data traceable to source."""
    section_prefixes = [
        section,
        f"{section}.",
    ]
    return any(
        any(key.startswith(prefix) for prefix in section_prefixes)
        for key in source_keys
    )


def confirm(summary_id: str, physician_edits: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Finalize summary after physician review.

    In production, this would persist to database. For now, returns merged result.
    """
    # TODO: Load summary from DB by summary_id, apply edits, persist confirmed version
    return {"summary_id": summary_id, "status": "confirmed", "edits_applied": physician_edits or {}}


def edit(summary_id: str, patches: dict[str, Any]) -> dict[str, Any]:
    """
    Apply physician edits to summary.

    Args:
        summary_id: Summary identifier
        patches: Dictionary of field paths to new values (e.g., {"hpi.severity": "9/10"})

    Returns:
        Updated summary
    """
    # TODO: Load from DB, apply patches with deep merge, persist
    return {"summary_id": summary_id, "status": "edited", "patches": patches}


def synthesize_sync(
    interview_json: dict[str, Any],
    document_json: dict[str, Any],
    lang: str = "en",
) -> SummaryResult:
    """Synchronous wrapper for synthesize."""
    import asyncio
    return asyncio.run(synthesize(interview_json, document_json, lang))


__all__ = [
    "SummaryResult",
    "synthesize",
    "synthesize_sync",
    "confirm",
    "edit",
]