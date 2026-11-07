"""/api/admin (FR-021, FR-022, NFR-013): admins only, every action audited,
no mass assignment, no route to conversation content."""

import pytest
from fastapi.testclient import TestClient

from app.config.composition import build_chat_service, build_screening_service
from app.config.dependencies import get_admin_service, get_auth_service, get_chat_service
from app.config.lazy import Lazy
from app.config.settings import Settings
from app.main import create_app
from app.repository.memory.conversation_repository import InMemoryConversationStore
from app.service.admin.admin_service import AdminService
from tests.conftest import ADMIN_ID, STUDENT_ID, SUSPENDED_ID, FakeProvider, bearer, make_auth_service

USERS = "/api/admin/users"
AUDIT = "/api/admin/audit-log"
ADMIN = bearer("admin-token")


def make(**settings):
    config = Settings(_env_file=None, **settings)
    app = create_app(config)
    auth_service, provider, users = make_auth_service()
    users.set_profile(STUDENT_ID)
    admin_service = AdminService(provider, users, users)
    app.dependency_overrides[get_auth_service] = lambda: Lazy(lambda: auth_service)
    app.dependency_overrides[get_admin_service] = lambda: Lazy(lambda: admin_service)
    store = InMemoryConversationStore()
    chat = build_chat_service(
        config, store, store, build_screening_service(config, provider=FakeProvider()), FakeProvider()
    )
    app.dependency_overrides[get_chat_service] = lambda: Lazy(lambda: chat)
    return TestClient(app, raise_server_exceptions=False), provider, users


ROUTES = [
    ("GET", USERS, None),
    ("POST", f"{USERS}/{STUDENT_ID}/suspend", {"reason": "x"}),
    ("POST", f"{USERS}/{SUSPENDED_ID}/reinstate", None),
    ("GET", AUDIT, None),
]


@pytest.mark.parametrize("method, url, body", ROUTES)
@pytest.mark.parametrize(
    "headers",
    [{}, bearer("forged-token"), bearer("expired-or-logged-out")],
    ids=["no_token", "forged", "expired_or_logged_out"],
)
def test_admin_routes_require_login(method, url, body, headers):
    client, _, _ = make()
    response = client.request(method, url, json=body, headers=headers)
    assert response.status_code == 401


@pytest.mark.parametrize("method, url, body", ROUTES)
@pytest.mark.parametrize(
    "token, code",
    [
        ("student-token", "admin_only"),
        ("unverified-token", "email_not_verified"),
        ("suspended-token", "account_suspended"),
    ],
)
def test_non_admins_get_403_on_every_admin_route(method, url, body, token, code):
    client, provider, _ = make()
    response = client.request(method, url, json=body, headers=bearer(token))
    assert response.status_code == 403
    assert response.json()["error"] == code
    assert provider.banned == {}


@pytest.mark.parametrize("method, url, body", ROUTES)
def test_supabase_unreachable_fails_closed(method, url, body):
    client, provider, _ = make()
    provider.unavailable = True
    assert client.request(method, url, json=body, headers=ADMIN).status_code == 503


def test_list_users():
    client, _, _ = make()
    response = client.get(USERS, params={"page": 1, "perPage": 10}, headers=ADMIN)
    assert response.status_code == 200
    by_id = {u["userId"]: u for u in response.json()}
    assert by_id[ADMIN_ID]["role"] == "admin"
    assert by_id[SUSPENDED_ID]["status"] == "suspended"
    assert set(by_id[STUDENT_ID]) == {
        "userId",
        "email",
        "emailVerified",
        "displayName",
        "role",
        "status",
        "createdAt",
    }


@pytest.mark.parametrize(
    "params", [{"page": 0}, {"perPage": 0}, {"perPage": 101}, {"page": "1 OR 1=1"}, {"perPage": "-1"}]
)
def test_list_users_rejects_bad_pagination(params):
    client, _, _ = make()
    assert client.get(USERS, params=params, headers=ADMIN).status_code == 422


def test_suspend_then_student_is_blocked_and_action_is_audited():
    client, provider, _ = make()
    response = client.post(f"{USERS}/{STUDENT_ID}/suspend", json={"reason": "Misuse"}, headers=ADMIN)
    assert response.status_code == 200
    body = response.json()
    assert (body["userId"], body["status"], body["loginBlockUpdated"]) == (STUDENT_ID, "suspended", True)
    assert body["auditLogId"]
    assert provider.banned == {STUDENT_ID: True}

    # Viewing own history stays allowed while suspended; starting a chat is not.
    assert client.get("/api/conversations", headers=bearer()).status_code == 200
    assert client.post("/api/conversations", json={}, headers=bearer()).status_code == 403

    log = client.get(AUDIT, headers=ADMIN).json()
    assert [
        (e["logId"], e["actionType"], e["targetUserId"], e["adminUserId"], e["details"]) for e in log
    ] == [(body["auditLogId"], "suspend", STUDENT_ID, ADMIN_ID, "Misuse")]


def test_suspend_without_a_body_is_allowed():
    client, _, _ = make()
    assert client.post(f"{USERS}/{STUDENT_ID}/suspend", headers=ADMIN).status_code == 200


def test_reinstate():
    client, provider, _ = make()
    response = client.post(f"{USERS}/{SUSPENDED_ID}/reinstate", headers=ADMIN)
    assert response.status_code == 200 and response.json()["status"] == "active"
    assert provider.banned == {SUSPENDED_ID: False}
    assert client.get("/api/profile", headers=bearer("suspended-token")).json()["status"] == "active"


def test_repeated_suspend_writes_no_second_audit_entry():
    client, _, _ = make()
    client.post(f"{USERS}/{STUDENT_ID}/suspend", headers=ADMIN)
    again = client.post(f"{USERS}/{STUDENT_ID}/suspend", headers=ADMIN).json()
    assert again["auditLogId"] is None
    assert len(client.get(AUDIT, headers=ADMIN).json()) == 1


def test_ban_failure_is_reported_but_account_is_still_blocked():
    client, provider, _ = make()
    provider.ban_unavailable = True
    body = client.post(f"{USERS}/{STUDENT_ID}/suspend", headers=ADMIN).json()
    assert body["status"] == "suspended" and body["loginBlockUpdated"] is False
    response = client.post("/api/conversations", json={}, headers=bearer())
    assert response.json()["error"] == "account_suspended"


def test_admin_cannot_suspend_self():
    client, provider, _ = make()
    response = client.post(f"{USERS}/{ADMIN_ID}/suspend", headers=ADMIN)
    assert response.status_code == 400
    assert provider.banned == {}


def test_unknown_account_is_404():
    client, _, _ = make()
    response = client.post(f"{USERS}/00000000-0000-4000-8000-0000000000ff/suspend", headers=ADMIN)
    assert response.status_code == 404


@pytest.mark.parametrize(
    "user_id",
    ["not-a-uuid", "1%20OR%201=1", "%3Cscript%3Ealert(1)%3C%2Fscript%3E", "..%2F..%2Fconversations"],
)
def test_target_must_be_a_uuid(user_id):
    client, provider, _ = make()
    response = client.post(f"{USERS}/{user_id}/suspend", headers=ADMIN)
    assert response.status_code in (404, 422)
    assert provider.banned == {}


@pytest.mark.parametrize(
    "body",
    [
        {"reason": "x" * 501},
        {"reason": "x", "status": "active"},
        {"reason": "x", "role": "admin"},
        {"reason": "x", "adminUserId": STUDENT_ID},
        {"reason": "x", "targetUserId": SUSPENDED_ID},
        {"reason": 123},
    ],
    ids=["too_long", "status", "role", "admin_id", "target_id", "wrong_type"],
)
def test_status_change_rejects_mass_assignment_and_bad_input(body):
    client, provider, _ = make()
    response = client.post(f"{USERS}/{STUDENT_ID}/suspend", json=body, headers=ADMIN)
    assert response.status_code == 422
    assert "x" * 50 not in response.text  # submitted text is not echoed back
    assert provider.banned == {}


def test_reason_is_stored_as_text_not_interpreted():
    client, _, _ = make()
    payload = "<script>alert(1)</script>'; DROP TABLE profiles; --"
    client.post(f"{USERS}/{STUDENT_ID}/suspend", json={"reason": payload}, headers=ADMIN)
    response = client.get(AUDIT, headers=ADMIN)
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()[0]["details"] == payload


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_audit_log_rejects_bad_pagination(params):
    client, _, _ = make()
    assert client.get(AUDIT, params=params, headers=ADMIN).status_code == 422


def test_admin_routes_are_rate_limited_per_user():
    client, _, _ = make(admin_rate_limit_per_user=2)
    statuses = [client.get(AUDIT, headers=ADMIN).status_code for _ in range(3)]
    assert statuses == [200, 200, 429]


def test_admin_cannot_reach_other_peoples_conversations():
    """NFR-013: admins have the same object-level limits as everyone else."""
    client, _, _ = make()
    created = client.post("/api/conversations", json={}, headers=bearer())
    assert created.status_code == 201
    conversation_id = created.json()["conversationId"]
    assert client.get(f"/api/conversations/{conversation_id}", headers=ADMIN).status_code == 404
    assert client.get("/api/conversations", headers=ADMIN).json() == []


def test_no_admin_route_mentions_conversations_or_messages():
    client, _, _ = make()
    paths = client.get("/openapi.json").json()["paths"]
    admin_paths = [p for p in paths if p.startswith("/api/admin")]
    assert sorted(admin_paths) == [
        "/api/admin/audit-log",
        "/api/admin/users",
        "/api/admin/users/{user_id}/reinstate",
        "/api/admin/users/{user_id}/suspend",
    ]
    assert not any("conversation" in p or "message" in p for p in admin_paths)
