"""Input validation helpers used by factories."""

from __future__ import annotations


def is_blank(value: str | None) -> bool:
    """True for None, empty, or whitespace-only strings."""
    return value is None or not value.strip()


def is_probability(value: float) -> bool:
    """True when value is a number in [0.0, 1.0]."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= value <= 1.0
