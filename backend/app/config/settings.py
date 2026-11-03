"""Application settings, read from environment variables and backend/.env.

Validated at startup, so an unsafe configuration stops the app instead of
running (SECURITY_RULES.md §0).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    app_env: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    # Largest prompt is 4,000 characters (FR-001); 64 KB leaves room for JSON
    # and multi-byte text while blocking oversized bodies.
    max_request_bytes: int = Field(default=65_536, gt=0, le=1_048_576)

    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_paid_tier: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    context_detector_timeout_seconds: float = Field(default=1.5, gt=0, le=10)

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard_origins(cls, origins: list[str]) -> list[str]:
        if any("*" in origin for origin in origins):
            raise ValueError("CORS_ORIGINS must list explicit origins, never '*'")
        return origins

    @model_validator(mode="after")
    def _production_rules(self) -> Settings:
        if self.is_production and any(not o.startswith("https://") for o in self.cors_origins):
            raise ValueError("In production every CORS origin must use https://")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def docs_enabled(self) -> bool:
        """Swagger/OpenAPI docs are served only outside production."""
        return not self.is_production
