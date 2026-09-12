"""
Module   : LLM Client
Owner    : ML Engineer
Purpose  : Provider-agnostic LLM client with mock for dev.
"""

import os
import httpx
from typing import Any
from dataclasses import dataclass

from .prompts import PROMPT_TASKS


@dataclass
class LLMConfig:
    provider: str = "mock"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    timeout: float = 30.0
    max_retries: int = 2

    def __post_init__(self):
        self.provider = os.getenv("LLM_PROVIDER", self.provider)
        self.base_url = os.getenv("LLM_BASE_URL", self.base_url)
        self.api_key = os.getenv("LLM_API_KEY", self.api_key)
        self.model = os.getenv("LLM_MODEL", self.model)


class LLMClient:
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs,
    ) -> dict:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        for attempt in range(self.config.max_retries + 1):
            try:
                resp = await self._client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, IndexError) as e:
                if attempt == self.config.max_retries:
                    raise RuntimeError(f"LLM call failed after retries: {e}") from e
        return {}

    async def close(self):
        await self._client.aclose()


class MockLLMClient:
    """Returns deterministic, schema-conforming JSON for each prompt task."""

    _RESPONSES = {
        "summarize_case": {
            "chief_complaint": "chest pain",
            "hpi": {
                "onset": "2 hours ago",
                "character": "crushing",
                "radiation": "left arm",
                "severity": "8/10",
                "exacerbating": "exertion",
                "relieving": "rest",
            },
            "past_medical_history": ["hypertension"],
            "drug_allergy_history": ["penicillin"],
            "family_history": ["father: MI at 55"],
            "personal_history": {"smoking": "10 pack-years", "alcohol": "occasional"},
            "review_of_systems": {"cardiovascular": "positive for chest pain", "respiratory": "negative"},
            "prior_investigations": [],
            "ayush": {},
            "source_attribution": "interview+documents",
        },
        "generate_next_question": {
            "question_id": "socrates_onset",
            "question_text": "When did the pain start?",
            "options": ["sudden", "gradual", "intermittent"],
            "branch": "SOCRATES",
        },
        "extract_entities": {
            "site": "chest",
            "onset": "2 hours ago",
            "character": "crushing",
            "radiation": "left arm",
            "associated": ["dyspnoea", "diaphoresis"],
            "timing": "constant",
            "exacerbating": "exertion",
            "relieving": "rest",
            "severity": "8/10",
        },
        "extract_document_entities": {
            "diagnoses": ["Type 2 Diabetes Mellitus"],
            "medications": [
                {"name": "Metformin", "dosage": "500mg", "frequency": "BD", "duration": "ongoing"}
            ],
            "investigations": [
                {"test": "HbA1c", "value": 8.2, "unit": "%", "ref_range": "4.0-5.6", "abnormal": True}
            ],
            "procedures": [],
            "dates": ["2026-08-15"],
        },
        "classify_redflag": {
            "is_redflag": True,
            "severity": "critical",
            "symptoms": ["chest pain", "dyspnoea"],
            "recommended_action": "immediate_ecg_triage",
        },
    }

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig(provider="mock")

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2048,
        task: str | None = None,
        **kwargs,
    ) -> dict:
        if task and task in self._RESPONSES:
            import json
            return json.dumps(self._RESPONSES[task])
        return "{}"

    async def close(self):
        pass


def get_client(config: LLMConfig | None = None):
    cfg = config or LLMConfig()
    if cfg.provider == "mock":
        return MockLLMClient(cfg)
    return LLMClient(cfg)


__all__ = ["LLMConfig", "LLMClient", "MockLLMClient", "get_client"]