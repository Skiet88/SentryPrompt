"""Application settings, read from environment variables and backend/.env.

Validated at startup, so an unsafe configuration stops the app instead of
running (SECURITY_RULES.md §0).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # hide_input_in_errors: an invalid setting must never print its value
    # (database passwords, API keys) to the console or logs.
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", hide_input_in_errors=True)

    app_env: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    # Largest prompt is 4,000 characters (FR-001); 64 KB leaves room for JSON
    # and multi-byte text while blocking oversized bodies.
    max_request_bytes: int = Field(default=65_536, gt=0, le=1_048_576)

    # ---- Database (Supabase PostgreSQL) -------------------------------------
    # Secret: SecretStr keeps it out of logs, reprs and error messages.
    database_url: SecretStr | None = None
    # Encrypt the database connection. Only "disable" for a local test database.
    database_ssl: Literal["require", "disable"] = "require"
    supabase_url: str = ""

    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_paid_tier: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    # Worst case for the context check. NFR-010 targets 2 s for the whole
    # screening; typical responses are well under that (measured by
    # run_context_eval.py), and a slow answer fails closed rather than passing.
    context_detector_timeout_seconds: float = Field(default=3.0, gt=0, le=10)

    # Screening calls a rate-limited LLM (Groq free tier: ~30 requests/min per
    # account), so limit per client and in total (SECURITY_RULES.md §4).
    screening_rate_limit_per_client: int = Field(default=10, gt=0, le=1000)
    screening_rate_limit_global: int = Field(default=25, gt=0, le=10_000)
    rate_limit_window_seconds: int = Field(default=60, gt=0, le=3600)

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard_origins(cls, origins: list[str]) -> list[str]:
        if any("*" in origin for origin in origins):
            raise ValueError("CORS_ORIGINS must list explicit origins, never '*'")
        return origins

    @field_validator("database_url")
    @classmethod
    def _postgres_url(cls, url: SecretStr | None) -> SecretStr | None:
        if url is None or not url.get_secret_value().strip():
            return None
        scheme = url.get_secret_value().split("://", 1)[0]
        if scheme not in ("postgresql", "postgres", "postgresql+asyncpg"):
            # The URL itself is never included in the message.
            raise ValueError("DATABASE_URL must be a postgresql:// connection string")
        return url

    @field_validator("supabase_url")
    @classmethod
    def _https_supabase_url(cls, url: str) -> str:
        if url and not url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use https://")
        return url.rstrip("/")

    @model_validator(mode="after")
    def _production_rules(self) -> Settings:
        if self.is_production and any(not o.startswith("https://") for o in self.cors_origins):
            raise ValueError("In production every CORS origin must use https://")
        if self.is_production and self.database_url is None:
            raise ValueError("DATABASE_URL is required in production")
        if self.is_production and self.database_ssl != "require":
            raise ValueError("DATABASE_SSL must be 'require' in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def unauthenticated_screening_enabled(self) -> bool:
        """TEMPORARY (agreed exception to SECURITY_RULES.md §2): until login
        exists (backend plan, step 6), the screening endpoint is served only
        outside production. Step 6 removes this and requires a verified login."""
        return not self.is_production

    @property
    def docs_enabled(self) -> bool:
        """Swagger/OpenAPI docs are served only outside production."""
        return not self.is_production
