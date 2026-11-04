"""Shared test doubles."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC

import pytest

from app.llm import ChatMessage, LLMProvider


@dataclass(frozen=True)
class FakeConfig:
    """Satisfies the LLMConfig protocol without reading the environment."""

    app_env: str = "development"
    llm_provider: str = "groq"
    groq_api_key: str = "test-key"
    groq_model: str = "openai/gpt-oss-20b"
    gemini_api_key: str = "test-key"
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_paid_tier: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    context_detector_timeout_seconds: float = 3.0

    def with_(self, **changes) -> FakeConfig:
        return replace(self, **changes)


class FakeProvider(LLMProvider):
    """Returns a canned reply (or raises / stalls) and records what it was sent."""

    name = "fake"

    def __init__(
        self,
        reply: str = '{"flags": []}',
        model: str = "fake-model",
        error: Exception | None = None,
        delay_seconds: float = 0.0,
    ):
        super().__init__(model)
        self.reply = reply
        self.error = error
        self.delay_seconds = delay_seconds
        self.received: list[tuple[str, str]] = []
        self.chat_reply = "Here is an outline for your essay."
        self.chat_error: Exception | None = None
        self.chat_delay_seconds = 0.0
        self.chat_received: list[list[ChatMessage]] = []

    @classmethod
    def from_config(cls, config):
        return cls()

    async def complete_json(self, system_prompt: str, user_text: str) -> str:
        self.received.append((system_prompt, user_text))
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.error:
            raise self.error
        return self.reply

    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        self.chat_received.append(list(messages))
        if self.chat_error:
            raise self.chat_error
        if self.chat_delay_seconds:
            await asyncio.sleep(self.chat_delay_seconds)
        return self.chat_reply


TEST_MESSAGE_KEY = "dGVzdC1vbmx5LWtleS0zMi1ieXRlcy1sb25nISEhISE="

# Valid production settings for tests. The database address is never contacted
# (the engine connects lazily); .invalid is a reserved, unresolvable domain.
PROD_SETTINGS = {
    "app_env": "production",
    "cors_origins": ["https://sentryprompt.example"],
    "database_url": "postgresql://sentry@db.invalid:5432/postgres",
    "supabase_url": "https://project.supabase.invalid",
    "supabase_secret_key": "sb_secret_test_value",
    # Test-only AES key (32 zero-free bytes, base64); never used outside tests.
    "message_encryption_key": TEST_MESSAGE_KEY,
}

# ---- authentication test doubles ------------------------------------------------

STUDENT_ID = "00000000-0000-4000-8000-000000000001"
ADMIN_ID = "00000000-0000-4000-8000-000000000002"
UNVERIFIED_ID = "00000000-0000-4000-8000-000000000003"
SUSPENDED_ID = "00000000-0000-4000-8000-000000000004"


class FakeIdentityProvider:
    """Stands in for Supabase Auth: known tokens map to identities."""

    def __init__(self) -> None:
        from app.service.auth.identity import VerifiedIdentity

        self.identities = {
            "student-token": VerifiedIdentity(STUDENT_ID, "student@uni.ac.za", True),
            "admin-token": VerifiedIdentity(ADMIN_ID, "admin@uni.ac.za", True),
            "unverified-token": VerifiedIdentity(UNVERIFIED_ID, "new@uni.ac.za", False),
            "suspended-token": VerifiedIdentity(SUSPENDED_ID, "suspended@uni.ac.za", True),
        }
        self.unavailable = False
        self.deleted: list[str] = []
        self.received_tokens: list[str] = []
        self.banned: dict[str, bool] = {}
        self.ban_unavailable = False

    async def verify_token(self, access_token: str):
        from app.exception import AuthenticationError, AuthUnavailableError

        self.received_tokens.append(access_token)
        if self.unavailable:
            raise AuthUnavailableError("Login could not be checked right now.")
        if access_token not in self.identities:
            raise AuthenticationError()
        return self.identities[access_token]

    async def delete_user(self, user_id: str) -> None:
        from app.exception import AuthUnavailableError

        if self.unavailable:
            raise AuthUnavailableError("The account could not be deleted right now.")
        self.deleted.append(user_id)

    async def list_users(self, page: int, per_page: int):
        from app.exception import AuthUnavailableError
        from app.service.auth.identity import IdentityRecord

        if self.unavailable:
            raise AuthUnavailableError("Accounts could not be listed right now.")
        records = [IdentityRecord(i.user_id, i.email, i.email_verified) for i in self.identities.values()]
        start = (page - 1) * per_page
        return records[start : start + per_page]

    async def set_banned(self, user_id: str, banned: bool) -> None:
        from app.exception import AuthUnavailableError

        if self.unavailable or self.ban_unavailable:
            raise AuthUnavailableError("The login block could not be updated right now.")
        self.banned[user_id] = banned


def make_auth_service():
    """An AuthService with the fake provider and in-memory profiles, where
    ADMIN_ID is an admin and SUSPENDED_ID is suspended."""
    from app.repository.memory.user_repository import InMemoryUserRepository
    from app.service.auth.auth_service import AuthService

    users = InMemoryUserRepository()
    users.set_profile(ADMIN_ID, role="admin")
    users.set_profile(SUSPENDED_ID, status="suspended")
    provider = FakeIdentityProvider()
    return AuthService(provider, users), provider, users


def bearer(token: str = "student-token") -> dict[str, str]:  # noqa: S107 - fake test token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def config() -> FakeConfig:
    return FakeConfig()


@pytest.fixture
def aware_time():
    from datetime import datetime

    return datetime(2026, 11, 3, 14, 37, 12, tzinfo=UTC)
