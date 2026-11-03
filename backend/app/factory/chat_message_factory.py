"""Builds ChatMessage entities."""

from app.domain import ChatMessage, ChatRole
from app.exception import InvalidArgumentError
from app.util.validation import is_blank


def build_chat_message(role: str, content: str) -> ChatMessage:
    try:
        parsed_role = ChatRole(role)
    except ValueError:
        raise InvalidArgumentError(f"Unknown chat role: {role!r}") from None
    if is_blank(content):
        raise InvalidArgumentError("Message content cannot be empty")
    return ChatMessage(role=parsed_role, content=content)
