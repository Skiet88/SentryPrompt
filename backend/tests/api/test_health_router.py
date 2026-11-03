import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic_settings")

from fastapi.testclient import TestClient  # noqa: E402

from app import __version__  # noqa: E402
from app.config.settings import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def test_health_reports_ok_version_and_environment():
    client = TestClient(create_app(Settings(_env_file=None, app_env="production")))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "environment": "production"}


def test_app_errors_become_json_responses():
    from app.exception import NotFoundError

    app = create_app(Settings(_env_file=None))

    @app.get("/boom")
    def boom():
        raise NotFoundError("missing thing")

    response = TestClient(app).get("/boom")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "message": "missing thing"}
