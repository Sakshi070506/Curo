"""
Tests for backend.ai.common shared AI layer.
"""

import pytest
from backend.ai.common import (
    clean_text,
    detect_language,
    parse_llm_json,
    get_prompt,
    render,
    PROMPT_TASKS,
    MockLLMClient,
    LLMConfig,
)


class TestUtils:
    def test_clean_text_basic(self):
        assert clean_text("  hello   world  ") == "hello world"
        assert clean_text("\n\tmultiple\nlines\t") == "multiple lines"
        assert clean_text("") == ""
        assert clean_text(None) == ""

    def test_detect_language_hindi(self):
        assert detect_language("मुझे सीने में दर्द है") == "hi"
        assert detect_language("सीने में दर्द") == "hi"

    def test_detect_language_english(self):
        assert detect_language("chest pain since morning") == "en"
        assert detect_language("I have a headache") == "en"

    def test_detect_language_mixed(self):
        # mostly devanagari
        assert detect_language("मुझे chest pain है") == "hi"
        # mostly latin
        assert detect_language("mujhe chest pain hai") == "en"

    def test_parse_llm_json_clean(self):
        raw = '{"key": "value", "num": 42}'
        assert parse_llm_json(raw) == {"key": "value", "num": 42}

    def test_parse_llm_json_with_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        assert parse_llm_json(raw) == {"key": "value"}

    def test_parse_llm_json_with_prefix_suffix(self):
        raw = 'Here is the result:\n{"key": "value"}\nDone.'
        assert parse_llm_json(raw) == {"key": "value"}

    def test_parse_llm_json_empty(self):
        assert parse_llm_json("") == {}
        assert parse_llm_json("not json") == {}


class TestPrompts:
    def test_all_tasks_registered(self):
        expected = {
            "summarize_case",
            "generate_next_question",
            "extract_entities",
            "extract_document_entities",
            "classify_redflag",
        }
        assert set(PROMPT_TASKS.keys()) == expected

    def test_get_prompt_returns_spec(self):
        spec = get_prompt("summarize_case")
        assert spec.task == "summarize_case"
        assert spec.version == "1.0.0"
        assert "output_schema" in spec.__dict__

    def test_get_prompt_unknown_raises(self):
        with pytest.raises(KeyError):
            get_prompt("unknown_task")

    def test_render_fills_placeholders(self):
        rendered = render("extract_entities", answer_text="chest pain since morning")
        assert "chest pain since morning" in rendered

    def test_summarize_case_output_schema_keys(self):
        spec = get_prompt("summarize_case")
        schema = spec.output_schema
        required = {
            "chief_complaint",
            "hpi",
            "past_medical_history",
            "drug_allergy_history",
            "family_history",
            "personal_history",
            "review_of_systems",
            "prior_investigations",
            "ayush",
            "source_attribution",
        }
        assert set(schema.keys()) == required


class TestMockLLMClient:
    @pytest.mark.asyncio
    async def test_mock_returns_schema_for_each_task(self):
        client = MockLLMClient()
        for task in PROMPT_TASKS:
            resp = await client.chat([], task=task)
            # parse_llm_json should succeed
            parsed = parse_llm_json(resp)
            assert isinstance(parsed, dict)
            # task-specific required keys present
            if task == "summarize_case":
                assert "chief_complaint" in parsed
            elif task == "generate_next_question":
                assert "question_id" in parsed
            elif task == "extract_entities":
                assert "site" in parsed
            elif task == "extract_document_entities":
                assert "diagnoses" in parsed
            elif task == "classify_redflag":
                assert "is_redflag" in parsed

    @pytest.mark.asyncio
    async def test_mock_unknown_task_returns_empty(self):
        client = MockLLMClient()
        resp = await client.chat([], task="unknown")
        assert parse_llm_json(resp) == {}

    def test_config_defaults_to_mock(self):
        cfg = LLMConfig()
        assert cfg.provider == "mock"


class TestLLMConfig:
    def test_config_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "http")
        monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
        monkeypatch.setenv("LLM_MODEL", "llama3")
        cfg = LLMConfig()
        assert cfg.provider == "http"
        assert cfg.base_url == "http://localhost:11434/v1"
        assert cfg.model == "llama3"