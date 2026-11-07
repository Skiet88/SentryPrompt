from dataclasses import dataclass

from app.domain import MessageRole


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One conversation turn as sent to an LLM provider. Services build these
    from stored Message entities."""

    role: MessageRole
    content: str
