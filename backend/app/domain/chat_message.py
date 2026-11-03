from dataclasses import dataclass

from .enums import ChatRole


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One turn of a conversation sent to the LLM. Create via chat_message_factory."""

    role: ChatRole
    content: str
