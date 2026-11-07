from dataclasses import dataclass
from datetime import datetime

from .enums import MessageRole


@dataclass(frozen=True, slots=True)
class Message:
    """One message in a conversation. Plain text in memory; the repository
    encrypts content before storing it (NFR-011). Create via message_factory."""

    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime
