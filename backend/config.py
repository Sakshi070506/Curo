"""
Module   : Configuration
Owner    : Backend Lead
Purpose  : Centralized environment/config loader (Pydantic Settings).
"""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/medikiosk",
        validation_alias="DATABASE_URL"
    )

    # Auth
    jwt_secret: str = Field(default="changeme", validation_alias="JWT_SECRET")
    jwt_expiry_minutes: int = Field(default=60, validation_alias="JWT_EXPIRY_MINUTES")

    # ASR / TTS (Bhashini / AI4Bharat)
    bhashini_api_key: Optional[str] = Field(default=None, validation_alias="BHASHINI_API_KEY")
    bhashini_api_url: Optional[str] = Field(default=None, validation_alias="BHASHINI_API_URL")

    # OCR
    ocr_provider: str = Field(default="tesseract", validation_alias="OCR_PROVIDER")
    vision_api_key: Optional[str] = Field(default=None, validation_alias="VISION_API_KEY")

    # ABDM Sandbox
    abdm_client_id: Optional[str] = Field(default=None, validation_alias="ABDM_CLIENT_ID")
    abdm_client_secret: Optional[str] = Field(default=None, validation_alias="ABDM_CLIENT_SECRET")
    abdm_base_url: str = Field(default="https://dev.abdm.gov.in", validation_alias="ABDM_BASE_URL")

    # Misc
    env: str = Field(default="development", validation_alias="ENV")
    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


Settings.model_rebuild()
settings = Settings()