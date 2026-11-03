from __future__ import annotations

from datetime import datetime

from app.domain import Conversation, SourceChannel
from app.exception import InvalidArgumentError

from . import _require

DEFAULT_TITLE = "New conversation"
MAX_TITLE_LENGTH = 200


def build_conversation(
    user_id: str,
    channel: SourceChannel | str,
    *,
    title: str = DEFAULT_TITLE,
    conversation_id: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Conversation:
    created = _require.timestamp(created_at, "created_at")
    updated = created if updated_at is None else _require.timestamp(updated_at, "updated_at")
    if updated < created:
        raise InvalidArgumentError("updated_at cannot be before created_at")
    return Conversation(
        conversation_id=_require.new_or_given_id(conversation_id, "conversation_id"),
        user_id=_require.identifier(user_id, "user_id"),
        title=_require.text(title, "title", MAX_TITLE_LENGTH),
        channel=_require.enum_value(SourceChannel, channel, "channel"),
        created_at=created,
        updated_at=updated,
    )
