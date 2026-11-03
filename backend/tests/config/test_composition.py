import asyncio

from app.config.composition import build_screening_service
from app.domain import Verdict
from app.llm import LLMProviderFactory, ProviderRegistry
from app.service.screening.screening_service import ScreeningService
from tests.conftest import FakeProvider


def test_builds_screening_service_from_settings(config):
    registry = ProviderRegistry()
    registry.register(FakeProvider)
    service = build_screening_service(
        config.with_(llm_provider="fake"), provider_factory=LLMProviderFactory(registry)
    )
    assert isinstance(service, ScreeningService)
    outcome = asyncio.run(service.screen("My ID is 9203105800089", "extension"))
    assert outcome.result.aggregated_verdict is Verdict.FLAG


def test_builds_with_default_provider(config):
    assert isinstance(build_screening_service(config), ScreeningService)
