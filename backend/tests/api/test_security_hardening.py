"""SECURITY_RULES.md §4: headers, body size limit, docs, CORS."""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app

PROD = {"app_env": "production", "cors_origins": ["https://sentryprompt.example"]}


def client(**overrides) -> TestClient:
    return TestClient(create_app(Settings(_env_file=None, **overrides)))


def echo_client(**overrides) -> TestClient:
    app = create_app(Settings(_env_file=None, **overrides))

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return payload

    return TestClient(app)


def test_security_headers_on_every_response():
    headers = client().get("/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert headers["cache-control"] == "no-store"
    assert "default-src 'none'" in headers["content-security-policy"]
    assert "frame-ancestors 'none'" in headers["content-security-policy"]


def test_security_headers_on_error_responses():
    response = client().get("/does-not-exist")
    assert response.status_code == 404
    assert response.headers["x-content-type-options"] == "nosniff"


def test_hsts_only_in_production():
    assert "strict-transport-security" not in client().get("/health").headers
    assert "max-age=" in client(**PROD).get("/health").headers["strict-transport-security"]


def test_docs_available_in_development_without_strict_csp():
    response = client().get("/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


def test_docs_disabled_in_production():
    prod = client(**PROD)
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert prod.get(path).status_code == 404


def test_body_within_limit_accepted():
    response = echo_client(max_request_bytes=1024).post("/echo", json={"text": "a" * 500})
    assert response.status_code == 200


def test_oversized_body_rejected_by_declared_length():
    response = echo_client(max_request_bytes=1024).post("/echo", json={"text": "a" * 2000})
    assert response.status_code == 413
    assert response.json()["error"] == "payload_too_large"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_oversized_body_rejected_without_content_length():
    def chunks():
        yield b'{"text": "'
        yield b"a" * 2000
        yield b'"}'

    response = echo_client(max_request_bytes=1024).post(
        "/echo", content=chunks(), headers={"content-type": "application/json"}
    )
    assert response.status_code == 413


def test_cors_allows_only_listed_origin():
    c = client(cors_origins=["http://localhost:5173"])
    allowed = c.get("/health", headers={"Origin": "http://localhost:5173"})
    blocked = c.get("/health", headers={"Origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in blocked.headers


def test_chunked_body_within_limit_still_reaches_endpoint():
    def chunks():
        yield b'{"text": "'
        yield b"a" * 100
        yield b'"}'

    response = echo_client(max_request_bytes=1024).post(
        "/echo", content=chunks(), headers={"content-type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json() == {"text": "a" * 100}
