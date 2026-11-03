"""Builds DetectedSpan value objects from detector output."""

from __future__ import annotations

from app.domain import DetectorSource
from app.exception import InvalidArgumentError
from app.screening.detection import ContextCategory, DetectedSpan
from app.util.validation import is_blank, is_probability

from . import _require


def build_context_span(
    category: str,
    span_text: str,
    source_text: str,
    confidence: float | None = None,
) -> DetectedSpan:
    """Locate span_text inside source_text and build a context-aware span.

    Raises InvalidArgumentError if the category is unknown, the span is empty,
    the span does not occur in source_text (it could not be highlighted, FR-005),
    or the confidence is outside [0, 1].
    """
    parsed = _require.enum_value(ContextCategory, str(category).upper(), "category")
    if not isinstance(span_text, str) or is_blank(span_text):
        raise InvalidArgumentError("Flag span cannot be empty")
    start = source_text.find(span_text)
    if start == -1:
        raise InvalidArgumentError("Flag span does not occur in the source text")
    if confidence is not None and not is_probability(confidence):
        raise InvalidArgumentError("Confidence must be between 0 and 1")
    return DetectedSpan(
        category=parsed.value,
        start=start,
        end=start + len(span_text),
        detector_source=DetectorSource.CONTEXT,
        confidence=float(confidence) if confidence is not None else None,
    )
