import pytest

from app.domain import TestSetCategory, Verdict
from app.exception import InvalidArgumentError
from app.factory.test_set_entry_factory import build_test_set_entry


def test_builds_entry():
    entry = build_test_set_entry("TS-002", "My ID is 9203105800089", "ID_NUMBER", "FLAG")
    assert entry.ground_truth_category is TestSetCategory.ID_NUMBER
    assert entry.ground_truth_label is Verdict.FLAG


def test_clean_entry_cannot_be_flagged():
    with pytest.raises(InvalidArgumentError, match="CLEAN"):
        build_test_set_entry("TS-025", "Outline an essay", "CLEAN", "FLAG")


@pytest.mark.parametrize(
    "entry_id, text, category, label",
    [
        ("", "text", "CLEAN", "NO_FLAG"),
        ("TS-1", "", "CLEAN", "NO_FLAG"),
        ("TS-1", "text", "HEALTH", "NO_FLAG"),
        ("TS-1", "text", "CLEAN", "YES"),
        ("TS-1", "text", "MEDICAL", "UNAVAILABLE"),
    ],
)
def test_rejects_invalid_input(entry_id, text, category, label):
    with pytest.raises(InvalidArgumentError):
        build_test_set_entry(entry_id, text, category, label)
