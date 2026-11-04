"""SECURITY_RULES.md §2 and §7 at the API: deny by default, every login
state, mass assignment, fail closed, rate limits, no token leakage."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.config.composition import build_screening_service
from app.config.dependencies import get_auth_service, get_screening_service
from app.config.lazy import Lazy
from app.config.settings import Settings
from app.llm import LLMProviderFactory, ProviderRegistry
from app.main import create_app
from tests.conftest import STUDENT_ID, SUSPENDED_ID, FakeProvider, bearer, make_auth_service

SCREEN = "/api/prompts/screen"
PROFILE = "/api/profile"


def make(**settings):
    registry = ProviderRegistry()
    registry.register(FakeProvider)
    config = Settings(_env_file=None, llm_provider="fake", **settings)
    app = create_app(config)
    service = build_screening_service(config, provider_factory=LLMProviderFactory(registry))
    auth_service, provider, users = make_auth_service()
    app.dependency_overrides[get_screening_service] = lambda: Lazy(lambda: service)
    app.dependency_overrides[get_auth_service] = lambda: Lazy(lambda: auth_service)
    return TestClient(app, raise_server_exceptions=False), provider, users


PROTECTED = [
    ("POST", SCREEN, {"text": "hi"}),
    ("GET", PROFILE, None),
    ("PUT", PROFILE, {"displayName": "x"}),
    ("DELETE", PROFILE, None),
]


@pytest.mark.parametrize("method, url, body", PROTECTED)
@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Basic dXNlcjpwYXNz"}, bearer("forged-token"), bearer("expired-or-logged-out")],
    ids=["no_token", "wrong_scheme", "forged", "expired_or_logged_out"],
)
def test_protected_endpoints_deny_without_a_valid_login(method, url, body, headers):
    client, _, _ = make()
    response = client.request(method, url, json=body, headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"] == "unauthenticated"


@pytest.mark.parametrize("method, url, body", PROTECTED)
def test_supabase_unreachable_fails_closed(method, url, body):
    client, provider, _ = make()
    provider.unavailable = True
    response = client.request(method, url, json=body, headers=bearer())
    assert response.status_code == 503
    assert response.json()["error"] == "auth_unavailable"


def test_health_stays_public():
    client, _, _ = make()
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    "token, code", [("unverified-token", "email_not_verified"), ("suspended-token", "account_suspended")]
)
def test_screening_requires_verified_active_account(token, code):
    client, _, _ = make()
    response = client.post(SCREEN, json={"text": "hi"}, headers=bearer(token))
    assert response.status_code == 403
    assert response.json()["error"] == code


def test_verified_student_can_screen():
    client, _, _ = make()
    assert client.post(SCREEN, json={"text": "hi"}, headers=bearer()).status_code == 200


def test_get_profile():
    client, _, _ = make()
    body = client.get(PROFILE, headers=bearer()).json()
    assert body["userId"] == STUDENT_ID
    assert (body["email"], body["role"], body["status"], body["emailVerified"]) == (
        "student@uni.ac.za",
        "student",
        "active",
        True,
    )


def test_update_display_name():
    client, _, _ = make()
    response = client.put(PROFILE, json={"displayName": "  Thabo  "}, headers=bearer())
    assert response.status_code == 200 and response.json()["displayName"] == "Thabo"
    assert client.get(PROFILE, headers=bearer()).json()["displayName"] == "Thabo"


@pytest.mark.parametrize(
    "body",
    [
        {"displayName": "x", "role": "admin"},
        {"displayName": "x", "status": "active"},
        {"displayName": "x", "email": "other@uni.ac.za"},
        {"displayName": "x", "userId": SUSPENDED_ID},
        {"displayName": "x", "emailVerified": True},
        {"displayName": "x" * 101},
        {},
    ],
    ids=["role", "status", "email", "user_id", "email_verified", "too_long", "missing"],
)
def test_profile_update_rejects_mass_assignment_and_bad_input(body):
    client, _, _ = make()
    response = client.put(PROFILE, json=body, headers=bearer())
    assert response.status_code == 422
    assert client.get(PROFILE, headers=bearer()).json()["role"] == "student"


def test_suspended_user_can_view_and_delete_but_not_edit():
    client, provider, _ = make()
    assert client.get(PROFILE, headers=bearer("suspended-token")).status_code == 200
    assert (
        client.put(PROFILE, json={"displayName": "x"}, headers=bearer("suspended-token")).status_code == 403
    )
    assert client.delete(PROFILE, headers=bearer("suspended-token")).status_code == 204
    assert provider.deleted == [SUSPENDED_ID]


def test_delete_account_only_deletes_the_caller():
    client, provider, _ = make()
    response = client.delete(PROFILE, headers=bearer())
    assert response.status_code == 204 and response.content == b""
    assert provider.deleted == [STUDENT_ID]


def test_auth_attempts_are_rate_limited_per_address_before_supabase_is_called():
    client, provider, _ = make(auth_rate_limit_per_client=3)
    statuses = [client.get(PROFILE, headers=bearer("forged-token")).status_code for _ in range(5)]
    assert statuses == [401, 401, 401, 429, 429]
    assert len(provider.received_tokens) == 3


def test_screening_rate_limit_is_per_user():
    client, _, _ = make(screening_rate_limit_per_client=1)
    assert client.post(SCREEN, json={"text": "hi"}, headers=bearer()).status_code == 200
    assert client.post(SCREEN, json={"text": "hi"}, headers=bearer()).status_code == 429
    assert client.post(SCREEN, json={"text": "hi"}, headers=bearer("admin-token")).status_code == 200


def test_tokens_never_appear_in_logs_or_responses(caplog):
    client, provider, _ = make()
    provider.unavailable = True
    with caplog.at_level(logging.DEBUG):
        response = client.get(PROFILE, headers=bearer("student-token"))
        client.get(PROFILE, headers=bearer("forged-token"))
    assert "student-token" not in caplog.text and "forged-token" not in caplog.text
    assert "student-token" not in response.text


def test_docs_offer_the_authorize_button():
    client, _, _ = make()
    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    assert "HTTPValidationError" not in schema["components"]["schemas"]
