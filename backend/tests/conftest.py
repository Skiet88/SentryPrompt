"""Shared test doubles."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

import pytest

from app.llm import ChatMessage
from app.llm import LLMProvider


@dataclass(frozen=True)
class FakeConfig:
    """Satisfies the LLMConfig protocol without reading the environment."""

    app_env: str = "development"
    llm_provider: str = "groq"
    groq_api_key: str = "test-key"
    groq_model: str = "llama-3.1-8b-instant"
    gemini_api_key: str = "test-key"
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_paid_tier: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    def with_(self, **changes) -> "FakeConfig":
        return replace(self, **changes)


class FakeProvider(LLMProvider):
    """Returns a canned reply and records what it was sent."""

    name = "fake"

    def __init__(self, reply: str = '{"flags": []}', model: str = "fake-model"):
        super().__init__(model)
        self.reply = reply
        self.received: list[tuple[str, str]] = []

    @classmethod
    def from_config(cls, config):
        return cls()

    def complete_json(self, system_prompt: str, user_text: str) -> str:
        self.received.append((system_prompt, user_text))
        return self.reply

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        return "reply"


@pytest.fixture
def config() -> FakeConfig:
    return FakeConfig()


@pytest.fixture
def aware_time():
    from datetime import datetime, timezone

    return datetime(2026, 11, 3, 14, 37, 12, tzinfo=timezone.utc)
