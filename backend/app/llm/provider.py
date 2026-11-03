"""LLMProvider interface (Strategy). Each provider only talks to its model;
prompt building and reply parsing belong to the screening layer.

Methods are async so the two detectors can run concurrently (FR-004) and a
slow model never blocks the server."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar, Self

from .chat_message import ChatMessage
from .config import LLMConfig


class LLMProvider(ABC):
    name: ClassVar[str]
    # True for providers whose free tier may use prompts for training.
    may_train_on_free_tier: ClassVar[bool] = False

    def __init__(self, model: str):
        self.model = model

    @classmethod
    @abstractmethod
    def from_config(cls, config: LLMConfig) -> Self:
        """Build the provider from configuration (used by the registry)."""

    @abstractmethod
    async def complete_json(self, system_prompt: str, user_text: str) -> str:
        """Send one request in JSON mode and return the raw reply text."""

    @abstractmethod
    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Return the model's reply to a conversation."""

    async def model_is_available(self) -> bool | None:
        """Whether the configured model is offered by the provider, or None if
        this provider can't tell. Used by the startup check."""
        return None
