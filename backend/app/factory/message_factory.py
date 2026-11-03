from __future__ import annotations

from datetime import datetime

from app.domain import Message, MessageRole

from . import _require


def build_message(
    conversation_id: str,
    role: MessageRole | str,
    content: str,
    *,
    message_id: str | None = None,
    created_at: datetime | None = None,
) -> Message:
    return Message(
        message_id=_require.new_or_given_id(message_id, "message_id"),
        conversation_id=_require.identifier(conversation_id, "conversation_id"),
        role=_require.enum_value(MessageRole, role, "role"),
        content=_require.text(content, "Message content"),
        created_at=_require.timestamp(created_at, "created_at"),
    )
