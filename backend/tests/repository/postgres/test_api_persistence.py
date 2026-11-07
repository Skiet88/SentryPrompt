"""End to end: a prompt screened through the API is saved in PostgreSQL."""

from fastapi.testclient import TestClient

from app.config.composition import build_screening_service
from app.config.dependencies import get_auth_service, get_screening_service
from app.config.lazy import Lazy
from app.config.settings import Settings
from app.llm import LLMProviderFactory, ProviderRegistry
from app.main import create_app
from app.repository.postgres.screening_records import (
    PostgresEvaluationLogEntryRepository,
    PostgresFlaggedSpanRepository,
)
from tests.conftest import FakeProvider, bearer, make_auth_service
from tests.repository.postgres.conftest import run


def test_screening_is_saved_in_postgres_without_prompt_text(database_url, engine):
    registry = ProviderRegistry()
    registry.register(FakeProvider)
    settings = Settings(
        _env_file=None, llm_provider="fake", database_url=database_url, database_ssl="disable"
    )
    app = create_app(settings)
    service = build_screening_service(
        settings, provider_factory=LLMProviderFactory(registry), records=app.state.screening_records
    )
    app.dependency_overrides[get_screening_service] = lambda: Lazy(lambda: service)
    auth_service, _, _ = make_auth_service()
    app.dependency_overrides[get_auth_service] = lambda: Lazy(lambda: auth_service)

    response = TestClient(app, headers=bearer()).post(
        "/api/prompts/screen", json={"text": "My ID is 9203105800089"}
    )
    result_id = response.json()["screeningResultId"]

    [entry] = run(PostgresEvaluationLogEntryRepository(engine).find_by_result_id(result_id))
    [span] = run(PostgresFlaggedSpanRepository(engine).find_by_result_id(result_id))
    assert entry.outcome.value == "flagged"
    assert (span.start_index, span.end_index) == (9, 22)
    assert "9203105800089" not in repr(entry) + repr(span)
    run(app.state.database_engine.dispose())
