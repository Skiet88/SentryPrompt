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
