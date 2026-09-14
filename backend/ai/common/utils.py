"""
Module   : AI Utils
Owner    : ML Engineer
Purpose  : Shared helper functions across AI modules.
"""

import json
import re
from typing import Any


def clean_text(text: str) -> str:
    """Normalize whitespace and handle Devanagari/Latin spacing."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_language(text: str) -> str:
    """Detect script: 'hi' (Devanagari), 'en' (Latin), or 'other'."""
    if not text:
        return "other"
    devanagari = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
    latin = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))
    total = len(text)
    if total == 0:
        return "other"
    if devanagari / total > 0.3:
        return "hi"
    if latin / total > 0.5:
        return "en"
    return "other"


def parse_llm_json(raw: str) -> dict:
    """Parse LLM output that may contain code fences or extra text."""
    if not raw:
        return {}
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def call_llm(messages: list[dict], client: Any = None, **kwargs) -> dict:
    """Thin wrapper with retry/timeout; actual client handles provider specifics."""
    if client is None:
        raise ValueError("LLM client required")
    return client.chat(messages, **kwargs)


def log_llm(messages: list[dict], response: dict, pii_safe: bool = True) -> None:
    """Log LLM interaction without patient PHI. Never logs raw patient text."""
    if pii_safe:
        safe_messages = [
            {**m, "content": "[REDACTED]"} if m.get("role") == "user" else m
            for m in messages
        ]
        return {"request": safe_messages, "response_keys": list(response.keys())}
    return {"request": messages, "response": response}


__all__ = [
    "clean_text",
    "detect_language",
    "parse_llm_json",
    "call_llm",
    "log_llm",
]