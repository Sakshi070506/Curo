"""
Module   : Intent Classifier
Owner    : ML Engineer
Purpose  : Classifies patient utterances into clinical intents.
"""

from backend.ai.common import MockLLMClient, get_prompt, parse_llm_json, detect_language


VALID_INTENTS = {
    "symptom_report",
    "general_query",
    "clarification",
    "affirmation",
    "negation",
    "dont_know",
}


async def classify_intent(utterance: str, lang: str | None = None, client: MockLLMClient | None = None) -> dict:
    """
    Classify patient utterance into clinical intent.

    Returns: {"intent": str, "confidence": float}
    """
    if lang is None:
        lang = detect_language(utterance)

    if client is None:
        client = MockLLMClient()

    spec = get_prompt("classify_intent")
    user_prompt = spec.user_template.format(utterance=utterance, lang=lang)

    messages = [
        {"role": "system", "content": spec.system},
        {"role": "user", "content": user_prompt},
    ]

    raw_response = await client.chat(messages, task="classify_intent")
    parsed = parse_llm_json(raw_response)

    intent = parsed.get("intent", "general_query")
    confidence = float(parsed.get("confidence", 0.5))

    if intent not in VALID_INTENTS:
        intent = "general_query"
        confidence = 0.3

    return {"intent": intent, "confidence": min(max(confidence, 0.0), 1.0)}


def classify_intent_sync(utterance: str, lang: str | None = None) -> dict:
    """Synchronous wrapper for classify_intent."""
    import asyncio
    return asyncio.run(classify_intent(utterance, lang))


__all__ = ["classify_intent", "classify_intent_sync", "VALID_INTENTS"]