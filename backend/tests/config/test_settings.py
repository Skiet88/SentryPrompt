import pytest

pytest.importorskip("pydantic_settings")

from pydantic import ValidationError

from app.config.settings import Settings
from tests.conftest import PROD_SETTINGS


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
        {**PROD_SETTINGS, "cors_origins": ["http://insecure.example"]},
        {**PROD_SETTINGS, "database_url": None},
        {**PROD_SETTINGS, "database_ssl": "disable"},
        {"database_url": "mysql://user@host/db"},
        {"supabase_url": "http://insecure.supabase.co"},
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
    settings = make(**PROD_SETTINGS)
    assert settings.is_production and not settings.docs_enabled


def test_screening_rate_limit_defaults_and_dev_only_flag():
    settings = make()
    assert (settings.screening_rate_limit_per_client, settings.screening_rate_limit_global) == (10, 25)
    assert settings.unauthenticated_screening_enabled
    prod = make(**PROD_SETTINGS)
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


def test_database_url_is_secret_and_normalised():
    settings = make(
        database_url="postgresql://user:hunter2@db.example:5432/postgres",
        supabase_url="https://x.supabase.co/",
    )
    assert "hunter2" not in repr(settings) and "hunter2" not in str(settings.database_url)
    assert settings.supabase_url == "https://x.supabase.co"
    assert make(database_url="").database_url is None


def test_invalid_database_url_error_does_not_include_the_url():
    with pytest.raises(ValidationError) as caught:
        make(database_url="mysql://user:hunter2@host/db")
    assert "hunter2" not in str(caught.value)


def test_no_setting_value_is_ever_echoed_in_errors():
    with pytest.raises(ValidationError) as caught:
        make(groq_api_key="gsk_secret_value_123", context_detector_timeout_seconds="not-a-number")
    assert "gsk_secret_value_123" not in str(caught.value)
    assert "not-a-number" not in str(caught.value)
