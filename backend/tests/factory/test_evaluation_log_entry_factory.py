import dataclasses

import pytest

from app.domain import EvaluationOutcome
from app.exception import InvalidArgumentError
from app.factory.evaluation_log_entry_factory import build_evaluation_log_entry


def test_flagged_entry_needs_category_and_buckets_time(aware_time):
    entry = build_evaluation_log_entry("result-1", "flagged", "cat-1", occurred_at=aware_time)
    assert entry.outcome is EvaluationOutcome.FLAGGED
    assert entry.timestamp_bucket == "2026-11-03T14:00Z"


def test_unflagged_entry_has_no_category():
    assert build_evaluation_log_entry("result-1", "unflagged").category_id is None


def test_unflagged_entry_rejects_category():
    with pytest.raises(InvalidArgumentError, match="no category"):
        build_evaluation_log_entry("result-1", "unflagged", "cat-1")


@pytest.mark.parametrize("outcome", ["flagged", "override"])
def test_flagged_or_override_requires_category(outcome):
    with pytest.raises(InvalidArgumentError, match="category_id"):
        build_evaluation_log_entry("result-1", outcome)


def test_entry_has_no_field_for_prompt_text():
    """NFR-009: content-free by structure, not convention."""
    fields = {f.name for f in dataclasses.fields(build_evaluation_log_entry("r", "unflagged"))}
    assert fields == {"log_id", "result_id", "category_id", "outcome", "timestamp_bucket"}
