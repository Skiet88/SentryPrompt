"""Application settings, read from environment variables and backend/.env."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    app_env: Literal["development", "production"] = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_paid_tier: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
