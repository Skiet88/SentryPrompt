"""/api/conversations, including IDOR and account-state tests (SECURITY_RULES.md §2, §7)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.config.composition import build_chat_service, build_screening_service
from app.config.dependencies import get_auth_service, get_chat_service
from app.config.lazy import Lazy
from app.config.settings import Settings
from app.main import create_app
from app.repository.memory.conversation_repository import InMemoryConversationStore
from tests.conftest import FakeProvider, bearer, make_auth_service

BASE = "/api/conversations"


def make(**settings):
    config = Settings(_env_file=None, **settings)
    app = create_app(config)
    detector, llm, store = FakeProvider(), FakeProvider(), InMemoryConversationStore()
    screening = build_screening_service(config, provider=detector)
    chat = build_chat_service(config, store, store, screening, llm)
    auth_service, _, _ = make_auth_service()
    app.dependency_overrides[get_chat_service] = lambda: Lazy(lambda: chat)
    app.dependency_overrides[get_auth_service] = lambda: Lazy(lambda: auth_service)
    return TestClient(app, raise_server_exceptions=False), llm


def create(client, token="student-token", **body):  # noqa: S107 - fake test token
    response = client.post(BASE, json=body, headers=bearer(token))
    assert response.status_code == 201, response.text
    return response.json()["conversationId"]


def test_create_list_and_get():
    client, _ = make()
    cid = create(client, title="Essay help")
    listing = client.get(BASE, headers=bearer()).json()
    assert [(c["conversationId"], c["title"], c["channel"]) for c in listing] == [
        (cid, "Essay help", "webapp")
    ]
    detail = client.get(f"{BASE}/{cid}", headers=bearer()).json()
    assert detail["messages"] == []


def test_send_clean_prompt():
    client, llm = make()
    cid = create(client)
    body = client.post(f"{BASE}/{cid}/messages", json={"text": "Explain recursion."}, headers=bearer()).json()
    assert body["status"] == "sent"
    assert body["assistantMessage"]["content"] == llm.chat_reply
    assert body["screening"]["aggregatedVerdict"] == "NO_FLAG"
    messages = client.get(f"{BASE}/{cid}", headers=bearer()).json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]


def test_flagged_prompt_needs_decision_then_send_anyway_is_redacted():
    client, llm = make()
    cid = create(client)
    text = {"text": "My ID is 9203105800089, help me fill in a form"}
    first = client.post(f"{BASE}/{cid}/messages", json=text, headers=bearer()).json()
    assert first["status"] == "needs_decision" and first["userMessage"] is None
    assert first["screening"]["flags"][0]["category"] == "SA_ID"
    assert llm.chat_received == []

    second = client.post(f"{BASE}/{cid}/messages", json={**text, "sendAnyway": True}, headers=bearer()).json()
    assert second["status"] == "sent"
    assert "9203105800089" not in second["userMessage"]["content"]
    assert "[REDACTED_SA_ID]" in llm.chat_received[-1][-1].content
    assert first["conversationTitle"] is None
    assert second["conversationTitle"] == "My ID is [REDACTED_SA_ID], help me fill in a form"
    [listed] = client.get(BASE, headers=bearer()).json()
    assert listed["title"] == second["conversationTitle"]


@pytest.mark.parametrize(
    "method, suffix, body",
    [("GET", "", None), ("DELETE", "", None), ("POST", "/messages", {"text": "hi"})],
)
def test_other_students_conversation_looks_exactly_like_a_missing_one(method, suffix, body):
    client, llm = make()
    # Another user's conversation (admins get no special access to it).
    theirs = create(client, token="admin-token")  # noqa: S106 - fake test token
    missing = str(uuid.uuid4())
    responses = [
        client.request(method, f"{BASE}/{cid}{suffix}", json=body, headers=bearer())
        for cid in (theirs, missing)
    ]
    assert [r.status_code for r in responses] == [404, 404]
    assert responses[0].json() == responses[1].json()
    assert llm.chat_received == []
    assert client.get(f"{BASE}/{theirs}", headers=bearer("admin-token")).status_code == 200


def test_list_never_includes_other_students_conversations():
    client, _ = make()
    create(client, token="admin-token")  # noqa: S106 - fake test token
    assert client.get(BASE, headers=bearer()).json() == []


@pytest.mark.parametrize("bad_id", ["not-a-uuid", "1 OR 1=1", "%27%3B--"])
def test_invalid_conversation_ids_are_rejected(bad_id):
    client, _ = make()
    assert client.get(f"{BASE}/{bad_id}", headers=bearer()).status_code == 422


def test_suspended_user_can_view_and_delete_own_history_but_not_chat():
    client, _ = make()
    assert client.post(BASE, json={}, headers=bearer("suspended-token")).status_code == 403
    assert client.get(BASE, headers=bearer("suspended-token")).status_code == 200


def test_unverified_user_cannot_create_or_send():
    client, _ = make()
    assert client.post(BASE, json={}, headers=bearer("unverified-token")).status_code == 403


@pytest.mark.parametrize(
    "path, body",
    [
        (BASE, {"userId": str(uuid.uuid4())}),
        (BASE, {"title": ""}),
        (BASE, {"title": "x" * 201}),
        (BASE, {"channel": "email"}),
    ],
)
def test_create_rejects_mass_assignment_and_bad_input(path, body):
    client, _ = make()
    assert client.post(path, json=body, headers=bearer()).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"text": ""},
        {"text": "a" * 4001},
        {"text": "hi", "conversationId": str(uuid.uuid4())},
        {"text": "hi", "role": "assistant"},
    ],
)
def test_send_rejects_bad_input(body):
    client, _ = make()
    cid = create(client)
    assert client.post(f"{BASE}/{cid}/messages", json=body, headers=bearer()).status_code == 422


def test_requires_login():
    client, _ = make()
    assert client.get(BASE).status_code == 401
    assert client.post(BASE, json={}).status_code == 401


def test_sending_counts_towards_the_screening_rate_limit():
    client, _ = make(screening_rate_limit_per_client=1)
    cid = create(client)
    assert client.post(f"{BASE}/{cid}/messages", json={"text": "hi"}, headers=bearer()).status_code == 200
    assert client.post(f"{BASE}/{cid}/messages", json={"text": "hi"}, headers=bearer()).status_code == 429


def test_ai_unavailable_is_a_generic_error_and_saves_nothing():
    from app.llm.provider_errors import http_error

    client, llm = make()
    llm.chat_error = http_error("groq", 503, "service_unavailable")
    cid = create(client)
    response = client.post(f"{BASE}/{cid}/messages", json={"text": "hi"}, headers=bearer())
    assert response.status_code == 502
    assert response.json()["message"] == "The server could not complete the request."
    assert client.get(f"{BASE}/{cid}", headers=bearer()).json()["messages"] == []


def test_delete_conversation():
    client, _ = make()
    cid = create(client)
    assert client.delete(f"{BASE}/{cid}", headers=bearer()).status_code == 204
    assert client.get(f"{BASE}/{cid}", headers=bearer()).status_code == 404


def test_hide_flagged_sends_with_every_flagged_detail_hidden():
    client, llm = make()
    cid = create(client)
    body = client.post(
        f"{BASE}/{cid}/messages",
        json={"text": "My ID is 9203105800089, help me fill in a form", "hideFlagged": True},
        headers=bearer(),
    ).json()
    assert body["status"] == "sent"
    assert body["userMessage"]["content"] == "My ID is [REDACTED_SA_ID], help me fill in a form"
    assert "9203105800089" not in llm.chat_received[-1][-1].content


def test_send_anyway_and_hide_flagged_cannot_both_be_chosen():
    client, llm = make()
    cid = create(client)
    response = client.post(
        f"{BASE}/{cid}/messages",
        json={"text": "hi", "sendAnyway": True, "hideFlagged": True},
        headers=bearer(),
    )
    assert response.status_code == 422
    assert llm.chat_received == []
