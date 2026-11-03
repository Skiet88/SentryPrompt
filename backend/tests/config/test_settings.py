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
        "openai/gpt-oss-20b",
    )
    assert settings.context_detector_timeout_seconds == 3.0
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


def test_screening_rate_limit_defaults_and_dev_only_flag():
    settings = make()
    assert (settings.screening_rate_limit_per_client, settings.screening_rate_limit_global) == (10, 25)
    assert settings.unauthenticated_screening_enabled
    prod = make(app_env="production", cors_origins=["https://sentryprompt.example"])
    assert not prod.unauthenticated_screening_enabled


@pytest.mark.parametrize(
    "overrides",
    [
        {"screening_rate_limit_per_client": 0},
        {"screening_rate_limit_global": 0},
        {"rate_limit_window_seconds": 0},
    ],
)
def test_rate_limit_settings_must_be_positive(overrides):
    with pytest.raises(ValidationError):
        make(**overrides)
