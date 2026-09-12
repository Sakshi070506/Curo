"""
Module   : Clinical Entity Extractor
Owner    : ML Engineer
Purpose  : Extracts symptoms/onset/duration from free text.
"""

from backend.ai.common import MockLLMClient, get_prompt, parse_llm_json, detect_language


SOCRATES_SLOTS = [
    "site",
    "onset",
    "character",
    "radiation",
    "associated",
    "timing",
    "exacerbating",
    "relieving",
    "severity",
]


async def extract_entities(
    answer_text: str,
    lang: str | None = None,
    current_complaint: str | None = None,
    client: MockLLMClient | None = None,
) -> dict:
    """
    Extract SOCRATES slots from patient free-text answer.

    Returns dict with all SOCRATES slots, using "not mentioned" for absent fields.
    """
    if lang is None:
        lang = detect_language(answer_text)

    if client is None:
        client = MockLLMClient()

    spec = get_prompt("extract_entities")
    user_prompt = spec.user_template.format(answer_text=answer_text)

    if current_complaint:
        user_prompt = f"Chief complaint: {current_complaint}\n{user_prompt}"

    messages = [
        {"role": "system", "content": spec.system},
        {"role": "user", "content": user_prompt},
    ]

    raw_response = await client.chat(messages, task="extract_entities")
    parsed = parse_llm_json(raw_response)

    result = {}
    for slot in SOCRATES_SLOTS:
        value = parsed.get(slot, "not mentioned")
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        result[slot] = value if value else "not mentioned"

    return result


def extract_entities_sync(
    answer_text: str,
    lang: str | None = None,
    current_complaint: str | None = None,
) -> dict:
    """Synchronous wrapper for extract_entities."""
    import asyncio
    return asyncio.run(extract_entities(answer_text, lang, current_complaint))


def merge_tapped_answer(extracted: dict, tapped_slots: dict) -> dict:
    """
    Merge LLM-extracted entities with tapped (touch) answers.
    Tapped answers take priority over voice extraction.
    """
    result = extracted.copy()
    for slot, value in tapped_slots.items():
        if value and value != "not mentioned":
            result[slot] = value
    return result


__all__ = [
    "extract_entities",
    "extract_entities_sync",
    "merge_tapped_answer",
    "SOCRATES_SLOTS",
]