"""SupabaseIdentityProvider against a simulated Supabase Auth API."""

import asyncio
import json
import logging

import httpx
import pytest
from pydantic import SecretStr

from app.exception import AuthenticationError, AuthUnavailableError, ConfigurationError
from app.service.auth.supabase_identity_provider import SupabaseIdentityProvider

URL = "https://project.supabase.co"
SECRET = SecretStr("sb_secret_test_value")
USER_ID = "3f2a1c4e-0000-4000-8000-000000000abc"
TOKEN = "header.payload.signature"  # noqa: S105 - fake test token


def provider(handler) -> tuple[SupabaseIdentityProvider, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(record))
    return SupabaseIdentityProvider(URL, SECRET, client=client), seen


def user_json(confirmed: bool = True) -> dict:
    return {
        "id": USER_ID,
        "email": "a@b.co",
        "email_confirmed_at": "2026-11-04T09:00:00Z" if confirmed else None,
    }


def test_valid_token_gives_identity_and_sends_the_right_headers():
    p, seen = provider(lambda r: httpx.Response(200, json=user_json()))
    identity = asyncio.run(p.verify_token(TOKEN))
    assert (identity.user_id, identity.email, identity.email_verified) == (USER_ID, "a@b.co", True)
    [request] = seen
    assert str(request.url) == f"{URL}/auth/v1/user"
    assert request.headers["authorization"] == f"Bearer {TOKEN}"
    assert request.headers["apikey"] == SECRET.get_secret_value()


def test_unconfirmed_email_is_reported():
    p, _ = provider(lambda r: httpx.Response(200, json=user_json(confirmed=False)))
    assert asyncio.run(p.verify_token(TOKEN)).email_verified is False


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_invalid_expired_or_logged_out_token_is_rejected(status):
    body = {
        "code": status,
        "error_code": "session_not_found",
        "msg": "Session from session_id claim does not exist",
    }
    p, _ = provider(lambda r: httpx.Response(status, json=body))
    with pytest.raises(AuthenticationError):
        asyncio.run(p.verify_token(TOKEN))


@pytest.mark.parametrize(
    "handler",
    [
        lambda r: httpx.Response(500),
        lambda r: httpx.Response(429),
        lambda r: httpx.Response(200, content=b"not json"),
        lambda r: httpx.Response(200, json={"id": "not-a-uuid"}),
        lambda r: httpx.Response(200, json={"email": "a@b.co"}),
    ],
    ids=["server_error", "rate_limited", "not_json", "bad_id", "no_id"],
)
def test_unclear_answers_fail_closed(handler):
    p, _ = provider(handler)
    with pytest.raises(AuthUnavailableError):
        asyncio.run(p.verify_token(TOKEN))


@pytest.mark.parametrize("error", [httpx.ConnectError("down"), httpx.ReadTimeout("slow")])
def test_unreachable_supabase_fails_closed(error):
    def raise_error(request):
        raise error

    p, _ = provider(raise_error)
    with pytest.raises(AuthUnavailableError):
        asyncio.run(p.verify_token(TOKEN))


def test_token_and_key_are_never_logged(caplog):
    p, _ = provider(lambda r: httpx.Response(500))
    with caplog.at_level(logging.DEBUG), pytest.raises(AuthUnavailableError):
        asyncio.run(p.verify_token(TOKEN))
    assert TOKEN not in caplog.text and SECRET.get_secret_value() not in caplog.text


@pytest.mark.parametrize("status", [200, 204, 404])
def test_delete_user(status):
    p, seen = provider(lambda r: httpx.Response(status))
    asyncio.run(p.delete_user(USER_ID))
    [request] = seen
    assert request.method == "DELETE"
    assert str(request.url) == f"{URL}/auth/v1/admin/users/{USER_ID}"
    assert request.headers["apikey"] == SECRET.get_secret_value()
    assert "authorization" not in request.headers


def test_delete_failure_fails_closed():
    p, _ = provider(lambda r: httpx.Response(500))
    with pytest.raises(AuthUnavailableError):
        asyncio.run(p.delete_user(USER_ID))


def test_delete_rejects_non_uuid_ids_before_any_request():
    p, seen = provider(lambda r: httpx.Response(204))
    with pytest.raises(ValueError):
        asyncio.run(p.delete_user("../../admin/users"))
    assert seen == []


@pytest.mark.parametrize("url, key", [("", SECRET), (URL, None)])
def test_requires_configuration(url, key):
    with pytest.raises(ConfigurationError, match="SUPABASE_URL and SUPABASE_SECRET_KEY"):
        SupabaseIdentityProvider(url, key)


def test_error_body_is_not_trusted_as_json_input():
    p, _ = provider(lambda r: httpx.Response(401, content=json.dumps({"msg": TOKEN}).encode()))
    with pytest.raises(AuthenticationError) as caught:
        asyncio.run(p.verify_token(TOKEN))
    assert TOKEN not in str(caught.value)


# --- Admin: list accounts and login block (FR-021) ---


def test_list_users_sends_pagination_and_secret_key_only():
    payload = {"users": [user_json(), {**user_json(confirmed=False), "id": USER_ID.upper(), "email": None}]}
    p, seen = provider(lambda r: httpx.Response(200, json=payload))
    records = asyncio.run(p.list_users(2, 25))
    assert [(r.user_id, r.email, r.email_verified) for r in records] == [
        (USER_ID, "a@b.co", True),
        (USER_ID, "", False),
    ]
    [request] = seen
    assert request.method == "GET"
    assert request.url.path == "/auth/v1/admin/users"
    assert dict(request.url.params) == {"page": "2", "per_page": "25"}
    assert request.headers["apikey"] == SECRET.get_secret_value()
    assert "authorization" not in request.headers


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(401),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"no_users": []}),
        httpx.Response(200, json={"users": [{"id": "not-a-uuid"}]}),
    ],
    ids=["server_error", "unauthorized", "not_json", "missing_users", "bad_id"],
)
def test_list_users_fails_closed(response):
    p, _ = provider(lambda r: response)
    with pytest.raises(AuthUnavailableError):
        asyncio.run(p.list_users(1, 10))


@pytest.mark.parametrize("banned, duration", [(True, "876000h"), (False, "none")])
def test_set_banned(banned, duration):
    p, seen = provider(lambda r: httpx.Response(200, json=user_json()))
    asyncio.run(p.set_banned(USER_ID, banned))
    [request] = seen
    assert request.method == "PUT"
    assert str(request.url) == f"{URL}/auth/v1/admin/users/{USER_ID}"
    assert json.loads(request.content) == {"ban_duration": duration}
    assert request.headers["apikey"] == SECRET.get_secret_value()
    assert "authorization" not in request.headers


def test_set_banned_failure_fails_closed():
    p, _ = provider(lambda r: httpx.Response(503))
    with pytest.raises(AuthUnavailableError):
        asyncio.run(p.set_banned(USER_ID, True))


def test_set_banned_network_error_fails_closed():
    def boom(request):
        raise httpx.ConnectError("down")

    p, _ = provider(boom)
    with pytest.raises(AuthUnavailableError):
        asyncio.run(p.set_banned(USER_ID, True))


def test_set_banned_rejects_non_uuid_ids_before_any_request():
    p, seen = provider(lambda r: httpx.Response(200))
    with pytest.raises(ValueError):
        asyncio.run(p.set_banned("../../users", True))
    assert seen == []
