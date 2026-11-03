"""The backend detector must reproduce the published rule-based results
(docs/evaluation/EVALUATION_HARNESS_DESIGN.md §3, Revision 2) entry by entry."""

import csv
from pathlib import Path

import pytest

TEST_SET = Path(__file__).resolve().parents[4] / "docs" / "evaluation" / "TEST_SET.csv"

# Entries the rule-based detector flags in the published Revision 2 run.
# TS-007 is the known false positive (a public Luhn test card number).
EXPECTED_FLAGGED = {"TS-001", "TS-002", "TS-005", "TS-006", "TS-007", "TS-009", "TS-010", "TS-035"}


@pytest.mark.skipif(not TEST_SET.exists(), reason="test set not available")
def test_matches_published_rule_based_results(detector):
    with TEST_SET.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 40

    flagged = {row["entryId"] for row in rows if detector.detect_now(row["sampleText"]).spans}
    assert flagged == EXPECTED_FLAGGED

    outcomes = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    for row in rows:
        predicted = row["entryId"] in flagged
        actual = row["groundTruthLabel"].strip().upper() == "FLAG"
        key = ("T" if predicted == actual else "F") + ("P" if predicted else "N")
        outcomes[key] += 1
    assert outcomes == {"TP": 7, "FP": 1, "FN": 7, "TN": 25}
