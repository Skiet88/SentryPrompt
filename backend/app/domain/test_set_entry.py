from dataclasses import dataclass

from .enums import TestSetCategory, Verdict


@dataclass(frozen=True, slots=True)
class TestSetEntry:
    """One hand-labelled evaluation prompt. Isolated from live data: no
    references to any live entity. Create via test_set_entry_factory."""

    __test__ = False  # not a pytest test class

    entry_id: str
    sample_text: str
    ground_truth_category: TestSetCategory
    ground_truth_label: Verdict
