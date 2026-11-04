"""Builds DetectedSpan value objects from detector output."""

from __future__ import annotations

import re

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


MAX_OCCURRENCES = 50


def build_context_spans(
    category: str,
    span_text: str,
    source_text: str,
    confidence: float | None = None,
) -> tuple[DetectedSpan, ...]:
    """Like build_context_span, but one span for EVERY occurrence of span_text.

    The model names a phrase once, but the student may have written it several
    times; each copy must be highlighted and can be hidden. Matching ignores
    case and only counts whole words (so "ill" never matches inside "skill").
    If no whole-word copy exists, the model's exact match is kept (as before).
    At most MAX_OCCURRENCES spans, to bound the work on very repetitive text.
    """
    first = build_context_span(category, span_text, source_text, confidence)
    before = r"(?<!\w)" if re.match(r"\w", span_text) else ""
    after = r"(?!\w)" if re.search(r"\w$", span_text) else ""
    pattern = re.compile(before + re.escape(span_text) + after, re.IGNORECASE)
    spans: list[DetectedSpan] = []
    for match in pattern.finditer(source_text):
        spans.append(
            DetectedSpan(
                category=first.category,
                start=match.start(),
                end=match.end(),
                detector_source=DetectorSource.CONTEXT,
                confidence=first.confidence,
            )
        )
        if len(spans) == MAX_OCCURRENCES:
            break
    return tuple(spans) if spans else (first,)
