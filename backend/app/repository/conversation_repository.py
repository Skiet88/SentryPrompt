"""Conversations and their messages.

Every method is scoped to the owner: there is deliberately no way to load a
conversation by ID alone, so one student can never reach another student's
conversation through a bug in the service layer (IDOR, SECURITY_RULES.md §2).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from app.domain import Conversation, Message


class ConversationRepository(ABC):
    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def find_for_user(self, conversation_id: str, user_id: str) -> Conversation | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: str) -> list[Conversation]:
        """Most recently updated first."""

    @abstractmethod
    async def set_title(self, conversation_id: str, user_id: str, title: str) -> bool:
        """True if the title of a conversation owned by user_id was changed."""

    @abstractmethod
    async def delete_for_user(self, conversation_id: str, user_id: str) -> bool:
        """True if a conversation owned by user_id was deleted (with its messages)."""


class MessageRepository(ABC):
    """Message content is encrypted before it is stored (NFR-011)."""

    @abstractmethod
    async def append(
        self, conversation: Conversation, messages: Sequence[Message], updated_at: datetime
    ) -> None:
        """Add messages and update the conversation's updated_at, in one transaction."""

    @abstractmethod
    async def list_for_conversation(
        self, conversation: Conversation, limit: int | None = None
    ) -> list[Message]:
        """Oldest first; with a limit, the most recent `limit` messages."""
