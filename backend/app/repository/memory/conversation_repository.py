from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime

from app.domain import Conversation, Message

from ..conversation_repository import ConversationRepository, MessageRepository


class InMemoryConversationStore(ConversationRepository, MessageRepository):
    """Conversations and messages together (tests and development without a
    database). Messages are kept as plain objects in memory only."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._messages: dict[str, list[Message]] = {}

    async def create(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.conversation_id] = conversation
        self._messages[conversation.conversation_id] = []
        return conversation

    async def find_for_user(self, conversation_id: str, user_id: str) -> Conversation | None:
        conversation = self._conversations.get(conversation_id)
        return conversation if conversation and conversation.user_id == user_id else None

    async def list_for_user(self, user_id: str) -> list[Conversation]:
        owned = [c for c in self._conversations.values() if c.user_id == user_id]
        return sorted(owned, key=lambda c: c.updated_at, reverse=True)

    async def delete_for_user(self, conversation_id: str, user_id: str) -> bool:
        if await self.find_for_user(conversation_id, user_id) is None:
            return False
        del self._conversations[conversation_id]
        self._messages.pop(conversation_id, None)
        return True

    async def append(
        self, conversation: Conversation, messages: Sequence[Message], updated_at: datetime
    ) -> None:
        self._messages[conversation.conversation_id].extend(messages)
        self._conversations[conversation.conversation_id] = replace(conversation, updated_at=updated_at)

    async def list_for_conversation(
        self, conversation: Conversation, limit: int | None = None
    ) -> list[Message]:
        messages = self._messages.get(conversation.conversation_id, [])
        return list(messages[-limit:] if limit else messages)
