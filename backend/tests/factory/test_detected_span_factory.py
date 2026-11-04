import dataclasses

import pytest

from app.domain import DetectorSource
from app.exception import InvalidArgumentError
from app.factory.detected_span_factory import MAX_OCCURRENCES, build_context_span, build_context_spans

TEXT = "I've been on sertraline for two months"


def test_locates_span_in_text():
    span = build_context_span("medical", "sertraline", TEXT, 0.9)
    assert span.category == "MEDICAL"
    assert TEXT[span.start : span.end] == "sertraline"
    assert span.detector_source is DetectorSource.CONTEXT
    assert span.confidence == 0.9


def test_confidence_is_optional():
    assert build_context_span("INSTITUTIONAL", "two months", TEXT).confidence is None


def test_span_is_immutable():
    span = build_context_span("MEDICAL", "sertraline", TEXT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        span.start = 0


@pytest.mark.parametrize(
    "category, span_text, confidence, message",
    [
        ("FINANCIAL", "sertraline", None, "category must be one of"),
        ("MEDICAL", "", None, "cannot be empty"),
        ("MEDICAL", "   ", None, "cannot be empty"),
        ("MEDICAL", "depression", None, "does not occur"),
        ("MEDICAL", "sertraline", 1.5, "between 0 and 1"),
    ],
)
def test_rejects_invalid_input(category, span_text, confidence, message):
    with pytest.raises(InvalidArgumentError, match=message):
        build_context_span(category, span_text, TEXT, confidence)


# --- Every occurrence (build_context_spans) ---


REPEATED = "Sertraline helps. I take sertraline daily; my sertraline dose is low. Skill and ill."


def found(spans, text=REPEATED):
    return [text[s.start : s.end] for s in spans]


def test_every_occurrence_is_found_ignoring_case():
    assert found(build_context_spans("medical", "sertraline", REPEATED)) == [
        "Sertraline",
        "sertraline",
        "sertraline",
    ]


def test_only_whole_words_count():
    assert found(build_context_spans("medical", "ill", REPEATED)) == ["ill"]


def test_falls_back_to_the_exact_match_when_no_whole_word_exists():
    assert found(build_context_spans("medical", "kil", REPEATED)) == ["kil"]


def test_phrases_and_punctuation_are_matched_literally():
    text = "My (disciplinary hearing) was hard. The (disciplinary hearing) is Monday."
    assert len(build_context_spans("institutional", "(disciplinary hearing)", text)) == 2
    assert len(build_context_spans("institutional", ".*", "a.* b .*")) == 2  # not a regex


def test_number_of_spans_is_bounded():
    text = " ".join(["sertraline"] * (MAX_OCCURRENCES + 20))
    assert len(build_context_spans("medical", "sertraline", text)) == MAX_OCCURRENCES


def test_invalid_input_still_rejected():
    with pytest.raises(InvalidArgumentError):
        build_context_spans("medical", "not in text", REPEATED)
