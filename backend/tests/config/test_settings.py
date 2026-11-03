import pytest

pytest.importorskip("pydantic_settings")

from app.config.settings import Settings  # noqa: E402


def test_defaults(monkeypatch):
    for var in ("APP_ENV", "LLM_PROVIDER", "GROQ_MODEL"):
        monkeypatch.delenv(var, raising=False)
    settings = Settings(_env_file=None)
    assert (settings.app_env, settings.llm_provider, settings.groq_model) == (
        "development", "groq", "llama-3.1-8b-instant",
    )


def test_reads_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_PAID_TIER", "true")
    monkeypatch.setenv("CORS_ORIGINS", '["https://sentryprompt.example"]')
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "gemini"
    assert settings.gemini_paid_tier is True
    assert settings.cors_origins == ["https://sentryprompt.example"]


def test_rejects_unknown_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(ValueError):
        Settings(_env_file=None)
