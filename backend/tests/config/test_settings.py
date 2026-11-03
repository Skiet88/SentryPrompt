import pytest

pytest.importorskip("pydantic_settings")

from pydantic import ValidationError

from app.config.settings import Settings


def make(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_defaults(monkeypatch):
    for var in ("APP_ENV", "LLM_PROVIDER", "GROQ_MODEL", "CONTEXT_DETECTOR_TIMEOUT_SECONDS"):
        monkeypatch.delenv(var, raising=False)
    settings = make()
    assert (settings.app_env, settings.llm_provider, settings.groq_model) == (
        "development",
        "groq",
        "llama-3.1-8b-instant",
    )
    assert settings.context_detector_timeout_seconds == 1.5
    assert settings.docs_enabled and not settings.is_production


def test_reads_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_PAID_TIER", "true")
    monkeypatch.setenv("CORS_ORIGINS", '["https://sentryprompt.example"]')
    settings = make()
    assert settings.llm_provider == "gemini"
    assert settings.gemini_paid_tier is True
    assert settings.cors_origins == ["https://sentryprompt.example"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"app_env": "staging"},
        {"cors_origins": ["*"]},
        {"cors_origins": ["https://*.example.com"]},
        {"app_env": "production", "cors_origins": ["http://insecure.example"]},
        {"max_request_bytes": 0},
        {"context_detector_timeout_seconds": 0},
        {"context_detector_timeout_seconds": 60},
        {"log_level": "TRACE"},
    ],
)
def test_unsafe_or_invalid_settings_rejected(overrides):
    with pytest.raises(ValidationError):
        make(**overrides)


def test_production_with_https_origins_accepted():
    settings = make(app_env="production", cors_origins=["https://sentryprompt.example"])
    assert settings.is_production and not settings.docs_enabled
