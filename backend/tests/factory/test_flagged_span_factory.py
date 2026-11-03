import pytest

from app.domain import DetectorSource
from app.exception import InvalidArgumentError
from app.factory.flagged_span_factory import build_flagged_span


def test_builds_span():
    span = build_flagged_span("result-1", 3, 10, "rule", "cat-1")
    assert (span.start_index, span.end_index) == (3, 10)
    assert span.detector_source is DetectorSource.RULE


@pytest.mark.parametrize("start, end", [(-1, 4), (5, 5), (6, 2), (1.0, 4)])
def test_rejects_invalid_indices(start, end):
    with pytest.raises(InvalidArgumentError):
        build_flagged_span("result-1", start, end, "rule", "cat-1")


@pytest.mark.parametrize("field, kwargs", [
    ("result_id", {"result_id": ""}),
    ("category_id", {"category_id": " "}),
    ("detector_source", {"detector_source": "regex"}),
])
def test_rejects_invalid_fields(field, kwargs):
    args = {"result_id": "r", "start_index": 0, "end_index": 1, "detector_source": "context",
            "category_id": "c", **kwargs}
    with pytest.raises(InvalidArgumentError, match=field):
        build_flagged_span(**args)
