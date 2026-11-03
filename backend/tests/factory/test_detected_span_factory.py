import dataclasses

import pytest

from app.domain import DetectorSource
from app.exception import InvalidArgumentError
from app.factory.detected_span_factory import build_context_span

TEXT = "I've been on sertraline for two months"


def test_locates_span_in_text():
    span = build_context_span("medical", "sertraline", TEXT, 0.9)
    assert span.category == "MEDICAL"
    assert TEXT[span.start:span.end] == "sertraline"
    assert span.detector_source is DetectorSource.CONTEXT
    assert span.confidence == 0.9


def test_confidence_is_optional():
    assert build_context_span("INSTITUTIONAL", "two months", TEXT).confidence is None


def test_span_is_immutable():
    span = build_context_span("MEDICAL", "sertraline", TEXT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        span.start = 0


@pytest.mark.parametrize("category, span_text, confidence, message", [
    ("FINANCIAL", "sertraline", None, "category must be one of"),
    ("MEDICAL", "", None, "cannot be empty"),
    ("MEDICAL", "   ", None, "cannot be empty"),
    ("MEDICAL", "depression", None, "does not occur"),
    ("MEDICAL", "sertraline", 1.5, "between 0 and 1"),
])
def test_rejects_invalid_input(category, span_text, confidence, message):
    with pytest.raises(InvalidArgumentError, match=message):
        build_context_span(category, span_text, TEXT, confidence)
