"""Builds ContextFlag entities, validating the model's output against the prompt."""

from __future__ import annotations

from app.domain import ContextCategory, ContextFlag
from app.exception import InvalidArgumentError
from app.util.validation import is_blank, is_probability


def build_context_flag(
    category: str,
    span: str,
    source_text: str,
    confidence: float | None = None,
) -> ContextFlag:
    """Build a flag located inside source_text.

    Raises InvalidArgumentError if the category is unknown, the span is empty,
    the span does not occur in source_text (it could not be highlighted, FR-005),
    or the confidence is outside [0, 1].
    """
    try:
        parsed_category = ContextCategory(str(category).upper())
    except ValueError:
        raise InvalidArgumentError(f"Unknown context category: {category!r}") from None
    if not isinstance(span, str) or is_blank(span):
        raise InvalidArgumentError("Flag span cannot be empty")
    start = source_text.find(span)
    if start == -1:
        raise InvalidArgumentError("Flag span does not occur in the source text")
    if confidence is not None and not is_probability(confidence):
        raise InvalidArgumentError("Confidence must be between 0 and 1")

    return ContextFlag(
        category=parsed_category,
        span=span,
        start=start,
        end=start + len(span),
        confidence=float(confidence) if confidence is not None else None,
    )
