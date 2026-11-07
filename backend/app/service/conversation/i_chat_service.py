from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import Conversation, SourceChannel, User

from .chat_models import ConversationWithMessages, SendOutcome


class IChatService(ABC):
    @abstractmethod
    async def create_conversation(
        self, user: User, channel: SourceChannel | str, title: str | None = None
    ) -> Conversation: ...

    @abstractmethod
    async def list_conversations(self, user: User) -> list[Conversation]: ...

    @abstractmethod
    async def get_conversation(self, user: User, conversation_id: str) -> ConversationWithMessages: ...

    @abstractmethod
    async def delete_conversation(self, user: User, conversation_id: str) -> None: ...

    @abstractmethod
    async def send(
        self,
        user: User,
        conversation_id: str,
        text: str,
        *,
        send_anyway: bool = False,
        hide_flagged: bool = False,
    ) -> SendOutcome:
        """Screen the prompt; if clean (or sent anyway), send the redacted
        prompt to the AI and save both messages."""
