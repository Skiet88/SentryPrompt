from dataclasses import dataclass
from datetime import datetime

from .enums import SourceChannel


@dataclass(frozen=True, slots=True)
class Conversation:
    """A student's conversation (FR-019). Create via conversation_factory."""

    conversation_id: str
    user_id: str
    title: str
    channel: SourceChannel
    created_at: datetime
    updated_at: datetime
