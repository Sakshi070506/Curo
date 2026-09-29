"""
Module   : Configuration
Owner    : Backend Lead
Purpose  : Centralized environment/config loader (Pydantic Settings).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


def _find_repo_root() -> Path:
    """Walk up from this file to find the repo root (contains .env.example)."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".env.example").exists():
            return current
        current = current.parent
    return Path.cwd()


REPO_ROOT = _find_repo_root()
ENV_PATH = REPO_ROOT / ".env"


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./curo.db",
        validation_alias="DATABASE_URL"
    )

    # Auth
    jwt_secret: str = Field(default="changeme", validation_alias="JWT_SECRET")
    jwt_expiry_minutes: int = Field(default=60, validation_alias="JWT_EXPIRY_MINUTES")
    auth_required: bool = Field(default=False, validation_alias="AUTH_REQUIRED")

    # ASR / TTS (Bhashini / AI4Bharat)
    bhashini_api_key: str | None = Field(default=None, validation_alias="BHASHINI_API_KEY")
    bhashini_api_url: str | None = Field(default=None, validation_alias="BHASHINI_API_URL")

    # OCR
    ocr_provider: str = Field(default="tesseract", validation_alias="OCR_PROVIDER")
    vision_api_key: str | None = Field(default=None, validation_alias="VISION_API_KEY")
    vision_api_url: str | None = Field(default=None, validation_alias="VISION_API_URL")
    tesseract_cmd: str | None = Field(default=None, validation_alias="TESSERACT_CMD")

    # ABDM Sandbox
    abdm_client_id: str | None = Field(default=None, validation_alias="ABDM_CLIENT_ID")
    abdm_client_secret: str | None = Field(default=None, validation_alias="ABDM_CLIENT_SECRET")
    abdm_base_url: str = Field(default="https://dev.abdm.gov.in", validation_alias="ABDM_BASE_URL")

    # LLM
    llm_provider: str = Field(default="mock", validation_alias="LLM_PROVIDER")
    llm_base_url: str = Field(default="https://api.openai.com/v1", validation_alias="LLM_BASE_URL")
    llm_api_key: str | None = Field(default=None, validation_alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", validation_alias="LLM_MODEL")

    # Embeddings
    embedding_provider: str = Field(default="mock", validation_alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL")
    embedding_api_url: str | None = Field(default=None, validation_alias="EMBEDDING_API_URL")
    embedding_api_key: str | None = Field(default=None, validation_alias="EMBEDDING_API_KEY")

    # Drug Interactions CSV
    drug_interactions_csv: str | None = Field(default=None, validation_alias="DRUG_INTERACTIONS_CSV")

    # SMS Escalation
    sms_escalation_numbers_raw: str = Field(default="", validation_alias="SMS_ESCALATION_NUMBERS")

    @property
    def sms_escalation_numbers(self) -> list[str]:
        if not self.sms_escalation_numbers_raw:
            return []
        return [n.strip() for n in self.sms_escalation_numbers_raw.split(",") if n.strip()]

    # Misc
    env: str = Field(default="development", validation_alias="ENV")
    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")
    cors_origins_raw: str = Field(default="*", validation_alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        if not self.cors_origins_raw:
            return ["*"]
        return [n.strip() for n in self.cors_origins_raw.split(",") if n.strip()]

    model_config = ConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
