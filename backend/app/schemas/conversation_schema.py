"""Request/response models for /api/conversations (FR-007 to FR-009, FR-019, FR-020)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.domain import Conversation, Message, MessageRole, SourceChannel
from app.factory.conversation_factory import MAX_TITLE_LENGTH
from app.factory.prompt_factory import MAX_PROMPT_LENGTH
from app.service.conversation.chat_models import ConversationWithMessages, SendOutcome

from .screening_schema import ScreenPromptResponse, _CamelModel


class CreateConversationRequest(_CamelModel):
    title: str | None = Field(default=None, min_length=1, max_length=MAX_TITLE_LENGTH)
    channel: SourceChannel = SourceChannel.WEBAPP


class ConversationResponse(_CamelModel):
    conversation_id: str
    title: str
    channel: SourceChannel
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_conversation(cls, c: Conversation) -> ConversationResponse:
        return cls(
            conversation_id=c.conversation_id,
            title=c.title,
            channel=c.channel,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )


class MessageResponse(_CamelModel):
    message_id: str
    role: MessageRole
    # Shown as plain text only; never rendered as HTML (SECURITY_RULES.md §5).
    content: str
    created_at: datetime

    @classmethod
    def from_message(cls, m: Message) -> MessageResponse:
        return cls(message_id=m.message_id, role=m.role, content=m.content, created_at=m.created_at)


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]

    @classmethod
    def from_detail(cls, detail: ConversationWithMessages) -> ConversationDetailResponse:
        base = ConversationResponse.from_conversation(detail.conversation)
        return cls(**base.model_dump(), messages=[MessageResponse.from_message(m) for m in detail.messages])


class SendMessageRequest(_CamelModel):
    text: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    # The student saw the warning and chose "send anyway" (FR-007).
    send_anyway: bool = False


class SendMessageResponse(_CamelModel):
    status: Literal["sent", "needs_decision"]
    screening: ScreenPromptResponse
    user_message: MessageResponse | None
    assistant_message: MessageResponse | None
    # Set when sent: the chat's title (made from the first, redacted prompt).
    conversation_title: str | None

    @classmethod
    def from_outcome(cls, outcome: SendOutcome) -> SendMessageResponse:
        return cls(
            status=outcome.status.value,
            screening=ScreenPromptResponse.from_outcome(outcome.screening),
            user_message=MessageResponse.from_message(outcome.user_message) if outcome.user_message else None,
            assistant_message=(
                MessageResponse.from_message(outcome.assistant_message) if outcome.assistant_message else None
            ),
            conversation_title=outcome.conversation_title,
        )
