from __future__ import annotations

from app.domain import TestSetCategory, TestSetEntry, Verdict
from app.exception import InvalidArgumentError

from . import _require


def build_test_set_entry(
    entry_id: str,
    sample_text: str,
    ground_truth_category: TestSetCategory | str,
    ground_truth_label: Verdict | str,
) -> TestSetEntry:
    category = _require.enum_value(TestSetCategory, ground_truth_category, "ground_truth_category")
    label = _require.enum_value(Verdict, ground_truth_label, "ground_truth_label")
    if category is TestSetCategory.CLEAN and label is Verdict.FLAG:
        raise InvalidArgumentError("A CLEAN entry cannot be labelled FLAG")
    return TestSetEntry(
        entry_id=_require.identifier(entry_id, "entry_id"),
        sample_text=_require.text(sample_text, "sample_text"),
        ground_truth_category=category,
        ground_truth_label=label,
    )
