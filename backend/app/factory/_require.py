"""Shared checks for factories: each returns the validated value or raises
InvalidArgumentError with a message naming the field."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TypeVar

from app.exception import InvalidArgumentError
from app.util.clock import utc_now
from app.util.ids import new_id
from app.util.validation import is_blank, is_timezone_aware

E = TypeVar("E", bound=Enum)


def text(value: str | None, field: str, max_length: int | None = None) -> str:
    if value is None or is_blank(value):
        raise InvalidArgumentError(f"{field} cannot be empty")
    if max_length is not None and len(value) > max_length:
        raise InvalidArgumentError(f"{field} cannot be longer than {max_length} characters")
    return value


def identifier(value: str | None, field: str) -> str:
    return text(value, field)


def new_or_given_id(value: str | None, field: str) -> str:
    """Generate an ID when none is given; validate it when one is."""
    return new_id() if value is None else identifier(value, field)


def enum_value(enum_cls: type[E], value: E | str, field: str) -> E:
    try:
        return enum_cls(value)
    except ValueError:
        allowed = ", ".join(str(m.value) for m in enum_cls)
        raise InvalidArgumentError(f"{field} must be one of: {allowed}") from None


def timestamp(value: datetime | None, field: str) -> datetime:
    """Default to now (UTC); otherwise require a timezone-aware datetime."""
    if value is None:
        return utc_now()
    if not is_timezone_aware(value):
        raise InvalidArgumentError(f"{field} must be a timezone-aware datetime")
    return value
