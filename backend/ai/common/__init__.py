"""
Module   : AI Common — Shared AI Layer
Owner    : ML Engineer / Summary LLM Engineer
Purpose  : Central exports for prompts, utils, and LLM client.
"""

from .client import (
    LLMClient,
    LLMConfig,
    MockLLMClient,
    get_client,
)
from .prompts import (
    PROMPT_TASKS,
    PromptSpec,
    get_prompt,
    render,
)
from .utils import (
    call_llm,
    clean_text,
    detect_language,
    log_llm,
    parse_llm_json,
)

__all__ = [
    "PROMPT_TASKS",
    "PromptSpec",
    "get_prompt",
    "render",
    "clean_text",
    "detect_language",
    "parse_llm_json",
    "call_llm",
    "log_llm",
    "LLMConfig",
    "LLMClient",
    "MockLLMClient",
    "get_client",
]
