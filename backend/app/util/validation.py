"""Input validation helpers used by factories. Each returns a bool."""

from __future__ import annotations

import re
from datetime import datetime

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def is_blank(value: str | None) -> bool:
    """True for None, empty, or whitespace-only strings."""
    return value is None or not isinstance(value, str) or not value.strip()


def is_probability(value: float) -> bool:
    """True when value is a number in [0.0, 1.0]."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= value <= 1.0


def is_valid_email(value: str | None) -> bool:
    return isinstance(value, str) and _EMAIL.fullmatch(value) is not None


def is_timezone_aware(value: datetime | None) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def is_valid_regex(value: str | None) -> bool:
    if value is None or is_blank(value):
        return False
    try:
        re.compile(value)
    except re.error:
        return False
    return True
