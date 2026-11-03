import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic_settings")

from fastapi.testclient import TestClient

from app import __version__
from app.config.settings import Settings
from app.main import create_app


def test_health_reports_ok_version_and_environment():
    settings = Settings(_env_file=None, app_env="production", cors_origins=["https://sentryprompt.example"])
    client = TestClient(create_app(settings))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "environment": "production"}


def test_client_errors_return_their_message():
    from app.exception import NotFoundError

    app = create_app(Settings(_env_file=None))

    @app.get("/boom")
    def boom():
        raise NotFoundError("missing thing")

    response = TestClient(app).get("/boom")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "message": "missing thing"}


def test_server_errors_hide_internal_details():
    from app.exception import ProviderError

    app = create_app(Settings(_env_file=None))

    @app.get("/provider")
    def provider():
        raise ProviderError("Groq request failed: key gsk_secret internal detail")

    @app.get("/crash")
    def crash():
        raise RuntimeError("database password is hunter2")

    client = TestClient(app, raise_server_exceptions=False)
    for path, code in (("/provider", "llm_provider_error"), ("/crash", "internal_error")):
        response = client.get(path)
        assert response.status_code >= 500
        assert response.json() == {"error": code, "message": "The server could not complete the request."}
