"""LLMProvider interface (Strategy). Each provider only talks to its model;
prompt building and reply parsing belong to the screening layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar, Self

from app.domain import ChatMessage

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
    def complete_json(self, system_prompt: str, user_text: str) -> str:
        """Send one request in JSON mode and return the raw reply text."""

    @abstractmethod
    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Return the model's reply to a conversation."""
