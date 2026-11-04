import asyncio
import logging

from app.config.startup_checks import ModelStatus, check_llm_model
from app.exception import ProviderError
from app.llm import LLMProviderFactory, ProviderRegistry
from tests.conftest import FakeProvider


def factory_for(availability) -> LLMProviderFactory:
    class Provider(FakeProvider):
        async def model_is_available(self):
            if isinstance(availability, Exception):
                raise availability
            return availability

    registry = ProviderRegistry()
    registry.register(Provider)
    return LLMProviderFactory(registry)


def run(config, availability, caplog):
    with caplog.at_level(logging.INFO, logger="app.config.startup_checks"):
        return asyncio.run(check_llm_model(config.with_(llm_provider="fake"), factory_for(availability)))


def test_available_model(config, caplog):
    assert run(config, True, caplog) is ModelStatus.AVAILABLE
    assert "fake model fake-model (available)" in caplog.text


def test_missing_model_warns_clearly(config, caplog):
    assert run(config, False, caplog) is ModelStatus.MISSING
    assert "is NOT offered by the provider" in caplog.text


def test_provider_that_cannot_list_models(config, caplog):
    assert run(config, None, caplog) is ModelStatus.UNVERIFIED


def test_listing_error_does_not_block(config, caplog):
    error = ProviderError("fake request failed: HTTP 401 invalid_api_key")
    assert run(config, error, caplog) is ModelStatus.UNVERIFIED
    assert "HTTP 401 invalid_api_key" in caplog.text


def test_missing_key_reported_without_blocking(config, caplog):
    with caplog.at_level(logging.WARNING, logger="app.config.startup_checks"):
        status = asyncio.run(check_llm_model(config.with_(groq_api_key="")))
    assert status is ModelStatus.NOT_CONFIGURED
    assert "GROQ_API_KEY" in caplog.text


def test_database_check_reports_unreachable_database_without_details(caplog):
    from types import SimpleNamespace

    from pydantic import SecretStr

    from app.config.database import create_database_engine
    from app.config.startup_checks import check_database

    engine = create_database_engine(
        SimpleNamespace(
            database_url=SecretStr("postgresql://u:hunter2@127.0.0.1:1/db"), database_ssl="disable"
        ),
        pooled=False,
    )
    with caplog.at_level(logging.WARNING, logger="app.config.startup_checks"):
        assert asyncio.run(check_database(engine, timeout_seconds=5)) is None
    assert "not reachable or not migrated" in caplog.text
    assert "hunter2" not in caplog.text


def test_auth_check(caplog):
    import httpx
    from pydantic import SecretStr

    from app.config.startup_checks import check_auth

    def config(url="https://p.supabase.co", key="sb_secret_value"):
        from types import SimpleNamespace

        return SimpleNamespace(supabase_url=url, supabase_secret_key=SecretStr(key) if key else None)

    def client(status):
        return httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(status)))

    with caplog.at_level(logging.INFO, logger="app.config.startup_checks"):
        assert asyncio.run(check_auth(config(), client(200))) is True
        assert asyncio.run(check_auth(config(), client(401))) is False
        assert asyncio.run(check_auth(config(key=None), client(200))) is False
    assert "secret key accepted" in caplog.text
    assert "rejected SUPABASE_SECRET_KEY" in caplog.text
    assert "sb_secret_value" not in caplog.text
