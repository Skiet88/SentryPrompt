import json

import pytest

from app.domain import DetectorSource
from app.screening.classification_parser import ClassificationParser

TEXT = "I've been on sertraline for two months and I'm struggling to focus"
parser = ClassificationParser()


def parse(raw: str):
    return parser.parse(raw, TEXT, provider="groq", model="m", prompt_version="v1")


def test_parses_valid_flag():
    result = parse(json.dumps({"flags": [{"category": "medical", "span": "sertraline", "confidence": 0.9}]}))
    [span] = result.spans
    assert span.category == "MEDICAL" and TEXT[span.start:span.end] == "sertraline"
    assert span.detector_source is DetectorSource.CONTEXT and span.confidence == 0.9
    assert not result.parse_failed
    assert (result.provider, result.model, result.prompt_version) == ("groq", "m", "v1")


def test_empty_flags_is_clean():
    result = parse('{"flags": []}')
    assert not result.is_flagged and not result.parse_failed


@pytest.mark.parametrize("raw", ["not json", '{"other": 1}', '{"flags": "x"}', "", "[]"])
def test_malformed_reply_marked_as_parse_failure(raw):
    result = parse(raw)
    assert result.parse_failed and not result.is_flagged


def test_drops_invalid_flags_but_keeps_valid_ones():
    raw = json.dumps({"flags": [
        {"category": "FINANCIAL", "span": "sertraline"},
        {"category": "MEDICAL", "span": "depression"},
        "not a dict",
        {"category": "MEDICAL", "span": "sertraline"},
    ]})
    assert [TEXT[s.start:s.end] for s in parse(raw).spans] == ["sertraline"]
